"""Generate draft ground-truth annotations and review reports for selected resumes.

Uses deterministic structural analysis and DeepSeek LLM review to generate candidate
annotations with full element-span coverage, stable IDs, coordinates, entity records,
and uncertainty flags. Mark all drafts as unverified.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import html

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from local_api.schemas.extraction import ExtractionResponse
from local_api.schemas.sections import SectionRequest, SectionResponse
from local_api.services.llm_section_review import ReviewSettings, review_sections
from local_api.services.resume_structure import heading_aliases, normalized_heading
from scripts.evaluate_resume_ground_truth import extraction_hash

def load_env():
    env_file = ROOT / '.env'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

ANCHORS = json.loads((ROOT / 'local_api/data/section_anchors.json').read_text())
CATEGORIES = set(ANCHORS.keys())
ALIASES = heading_aliases(ANCHORS)


def extract_work_entries(experience_spans, elements):
    """Group experience spans into structured work records."""
    records = []
    current_record = None
    date_regex = re.compile(
        r'\b(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*)?(?:19|20)\d{2}\s*(?:[-–—]|to)\s*(?:(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*)?(?:19|20)\d{2}|present|current|till date)\b',
        re.I
    )

    for span in experience_spans:
        text = span['text'].strip()
        if not text:
            continue
        # Check if span looks like an employer/title/dates header
        has_dates = bool(date_regex.search(text))
        is_title_elem = elements[span['source_element_index']].get('type') == 'Title' or span['field_role'] == 'heading'
        is_bullet = bool(re.match(r'^[•▪●*\-–]', text))

        if (has_dates or is_title_elem) and not is_bullet and (current_record is None or len(current_record['span_ids']) > 2):
            if current_record and current_record['span_ids']:
                records.append(current_record)
            current_record = {
                'record_id': f"exp-{len(records) + 1}",
                'employer': '',
                'header_text':text,
                'relationship_status':'proposed_requires_review',
                'title': '',
                'dates': date_regex.search(text).group(0) if has_dates else '',
                'client': None,
                'responsibilities': [],
                'span_ids': [span['span_id']]
            }
            span['record_type'] = 'work_experience'
            span['record_id'] = current_record['record_id']
            span['field_role'] = 'employer' if not is_bullet else 'content'
        else:
            if current_record is None:
                current_record = {
                    'record_id': f"exp-{len(records) + 1}",
                    'employer': '',
                    'title': '',
                    'dates': '',
                    'client': None,
                    'responsibilities': [],
                    'span_ids': []
                }
            current_record['span_ids'].append(span['span_id'])
            span['record_type'] = 'work_experience'
            span['record_id'] = current_record['record_id']
            if is_bullet or len(text.split()) > 10:
                span['field_role'] = 'responsibility'
                current_record['responsibilities'].append(text)
            else:
                span['field_role'] = 'content'

    if current_record and current_record['span_ids']:
        records.append(current_record)
    return records


def extract_edu_entries(edu_spans, elements):
    """Group education spans into structured academic records."""
    records = []
    current_record = None
    degree_regex = re.compile(
        r'\b(?:b\.?tech|m\.?tech|b\.?e\.?|m\.?e\.?|b\.?sc|m\.?sc|bachelor|master|ph\.?d|diploma|hsc|ssc|cbse|icse|secondary|degree)\b',
        re.I
    )
    year_regex = re.compile(r'\b(?:19|20)\d{2}\b')
    grade_regex = re.compile(r'\b(?:gpa|cgpa|percentage|\%|first class|distinction)\b[:\s]*([0-9.]+(?:\s*\%|\s*\/\s*10)?)', re.I)

    for span in edu_spans:
        text = span['text'].strip()
        if not text:
            continue
        has_degree = bool(degree_regex.search(text))
        has_year = bool(year_regex.search(text))

        if has_degree or (current_record is None and has_year):
            if current_record and current_record['span_ids']:
                records.append(current_record)
            current_record = {
                'record_id': f"edu-{len(records) + 1}",
                'degree': degree_regex.search(text).group(0) if has_degree else text,
                'institution': text if re.search(r'\b(?:university|college|institute)\b',text,re.I) else '',
                'year': year_regex.search(text).group(0) if has_year else '',
                'grade': grade_regex.search(text).group(0) if grade_regex.search(text) else None,
                'span_ids': [span['span_id']]
            }
            span['record_type'] = 'education'
            span['record_id'] = current_record['record_id']
            span['field_role'] = 'degree' if has_degree else 'institution'
        else:
            if current_record is None:
                current_record = {
                    'record_id': f"edu-{len(records) + 1}",
                    'degree': '',
                    'institution': text if re.search(r'\b(?:university|college|institute)\b',text,re.I) else '',
                    'year': year_regex.search(text).group(0) if has_year else '',
                    'grade': None,
                    'span_ids': []
                }
            current_record['span_ids'].append(span['span_id'])
            span['record_type'] = 'education'
            span['record_id'] = current_record['record_id']
            if grade_regex.search(text) and not current_record['grade']:
                current_record['grade'] = grade_regex.search(text).group(0)
                span['field_role'] = 'grade'
            elif has_year and not current_record['year']:
                current_record['year'] = year_regex.search(text).group(0)
                span['field_role'] = 'year'
            else:
                span['field_role'] = 'content'

    if current_record and current_record['span_ids']:
        records.append(current_record)
    return records


def generate_draft(filename, artifact_path, cache_dir=None, use_deepseek=True, cached_only=False):
    if use_deepseek:load_env()
    art = json.loads(artifact_path.read_text())
    elements = art['extraction']['elements']
    local_sections = art['sections']['sections']
    local_needs_review = art['sections']['needs_review']
    source_ext_hash = extraction_hash(elements)

    # Map local predictions
    local_map = {}
    for s in local_sections:
        for b in s['blocks']:
            key = (b['source_element_index'], b['start'], b['end'])
            local_map[key] = s['category']
    for b in local_needs_review:
        key = (b['source_element_index'], b['start'], b['end'])
        local_map[key] = 'needs_review'

    # DeepSeek Review (with file-level caching)
    llm_map = {}
    llm_status = 'skipped'
    llm_metadata={}
    final=None
    if use_deepseek and (os.getenv('DEEPSEEK_API_KEY') or cached_only):
        cache_file = cache_dir / f"{hashlib.sha256(filename.encode()).hexdigest()[:16]}.json" if cache_dir else None
        if cache_file and cache_file.exists():
            final_json = json.loads(cache_file.read_text())
            final = SectionResponse.model_validate(final_json)
            llm_status = final.metadata.get('llm_review',{}).get('status','unknown')
            llm_metadata['cache_used']=True
            binding=final.metadata.get('review_cache')
            if binding and binding.get('source_sha256')!=source_ext_hash:raise ValueError('Cached source hash mismatch')
            llm_metadata['cache_provenance']='source_bound' if binding else 'legacy_source_inventory_validated_config_unknown'
        else:
            if cached_only:raise ValueError('No cached review available; cached-only mode never calls provider')
            try:
                extraction = ExtractionResponse.model_validate(art['extraction'])
                local = SectionResponse.model_validate(art['sections'])
                req = SectionRequest(elements=extraction.elements, extraction_verified=False)
                settings = ReviewSettings.from_env()
                final = review_sections(req, local, settings=settings)
                llm_status = final.metadata.get('llm_review', {}).get('status', 'complete')
                if cache_file:
                    cache_file.parent.mkdir(parents=True, exist_ok=True)
                    final.metadata['review_cache']={'source_sha256':source_ext_hash,'model':settings.model,'prompt_version':'source_inventory_v2'}
                    cache_file.write_text(final.model_dump_json(indent=2))
            except Exception as e:
                llm_status = 'failed: '+type(e).__name__
                final = None

        if final:
            from local_api.services.llm_section_review import assert_coverage,source_ledger
            from local_api.services.source_accounting import account_source
            original=ExtractionResponse.model_validate(art['extraction'])
            assert_coverage(original.elements,source_ledger(final))
            llm_metadata.update(final.metadata.get('llm_review',{}))
            llm_metadata['source_accounting']=account_source(original.elements,final)
            if llm_metadata.get('status')!='complete':
                final=None
        if final:
            for s in final.sections:
                for b in s.blocks:
                    llm_map[(b.source_element_index, b.start, b.end)] = s.category
            for b in final.needs_review:
                llm_map[(b.source_element_index, b.start, b.end)] = 'needs_review'

    # Build Spans covering 100% of characters
    spans = []
    for elem_idx, elem in enumerate(elements):
        text = elem['text']
        elem_len = len(text)
        page = elem.get('page_number', 1)
        coords = elem.get('metadata', {}).get('coordinates', {})

        # Check if entire element matches artifact/header/page number
        is_page_marker = elem.get('type') in {'Footer','PageBreak'} and bool(re.fullmatch(r'\s*(?:page\s*\d+(?:\s*(?:of|\/)\s*\d+)?|\d+)\s*', text, re.I))
        if is_page_marker:
            span_id = f"span-p{page}-e{elem_idx}-s0-e{elem_len}"
            spans.append({
                'span_id': span_id,
                'source_element_index': elem_idx,
                'start': 0,
                'end': elem_len,
                'category': 'ignore',
                'text': text,
                'page_number': page,
                'coordinates': coords,
                'uncertainty_flag': False,
                'uncertainty_reason': None,
                'block_id': f"block-elem{elem_idx}",
                'record_type': None,
                'record_id': None,
                'field_role': 'artifact'
            })
            continue

        # Check existing block subdivisions or default to whole element
        boundaries={0,elem_len}
        for ei,start,end in set(local_map)|set(llm_map):
            if ei==elem_idx:boundaries.update([start,end])
        ordered=sorted(boundaries)
        intervals=list(zip(ordered,ordered[1:]))

        for start, end in intervals:
            if start == end:
                continue
            span_id = f"span-p{page}-e{elem_idx}-s{start}-e{end}"
            span_text = text[start:end]
            sub_key = (elem_idx, start, end)

            def covering(mapping):
                matches=[category for (ei,left,right),category in mapping.items() if ei==elem_idx and left<=start and right>=end]
                return matches[0] if len(matches)==1 else 'needs_review'
            loc_cat = covering(local_map)
            llm_cat = covering(llm_map) if final else loc_cat

            # Determine proposed category & uncertainty
            uncertain = False
            reason = None

            # Check explicit heading
            norm_head = normalized_heading(span_text)
            explicit_head_cat = ALIASES.get(norm_head)

            if explicit_head_cat and not final:
                proposed_cat = explicit_head_cat
                uncertain = False
                field_role = 'heading'
            elif llm_cat in CATEGORIES:
                proposed_cat = llm_cat
                if loc_cat in CATEGORIES and loc_cat != llm_cat:
                    uncertain = True
                    reason = f"Category conflict: local predicted '{loc_cat}' while LLM predicted '{llm_cat}'"
                field_role = 'content'
            elif loc_cat in CATEGORIES and not final:
                proposed_cat = loc_cat
                if llm_cat == 'needs_review':
                    uncertain = True
                    reason = "LLM abstained (needs_review); falling back to local model proposal"
                field_role = 'content'
            else:
                # Both unresolved - heuristics
                if elem_idx < 3 and ('@' in span_text or re.search(r'\+?\d{10}', span_text)):
                    proposed_cat = 'personal_information'
                    uncertain = True
                    reason = "Unresolved preamble span containing contact indicators; proposed personal_information"
                else:
                    proposed_cat = 'needs_review' # No fabricated fallback section
                    uncertain = True
                    reason = "Unassigned text without strong heading; flagged for human review"
                field_role = 'content'

            spans.append({
                'span_id': span_id,
                'source_element_index': elem_idx,
                'start': start,
                'end': end,
                'category': proposed_cat,
                'text': span_text,
                'page_number': page,
                'coordinates': coords,
                'local_category':loc_cat,
                'llm_category':llm_cat if final else None,
                'assignment_outcome':'assigned' if proposed_cat in CATEGORIES else 'human_review',
                'uncertainty_flag': uncertain,
                'uncertainty_reason': reason,
                'block_id': f"block-elem{elem_idx}-{start}",
                'record_type': None,
                'record_id': None,
                'field_role': field_role
            })

    # Sort spans strictly by element index and start offset
    spans.sort(key=lambda s: (s['source_element_index'], s['start'], s['end']))

    # Extract structured entity records
    exp_spans = [s for s in spans if s['category'] == 'experience']
    work_records = extract_work_entries(exp_spans, elements)

    edu_spans = [s for s in spans if s['category'] == 'education']
    edu_records = extract_edu_entries(edu_spans, elements)

    if final:
        # Use the final source-linked entry boundaries; never create a separate
        # job for every Title element/field label in the annotation renderer.
        def records_from_entries(category):
            section=next((s for s in final.sections if s.category==category),None)
            records=[]
            if section is None:return records
            for entry in section.entries:
                refs=[section.blocks[i] for i in entry.block_indices]
                members=[s for s in spans if s['category']==category and any(
                    b.source_element_index==s['source_element_index'] and b.start<=s['start'] and b.end>=s['end'] for b in refs)]
                if not members:continue
                record={'record_id':entry.entry_id,'span_ids':[s['span_id'] for s in members],
                        'source_text':' '.join(s['text'] for s in members),
                        'relationship_status':'proposed_requires_review'}
                if category=='experience':record.update(employer='',title='',dates='',client=None,responsibilities=[])
                else:record.update(degree='',institution='',year='',grade=None)
                for s in members:
                    s['record_id']=entry.entry_id
                    s['record_type']='work_experience' if category=='experience' else 'education'
                records.append(record)
            return records
        work_records=records_from_entries('experience')
        edu_records=records_from_entries('education')

    uncertain_count = sum(1 for s in spans if s['uncertainty_flag'])
    categories_present = sorted(set(s['category'] for s in spans if s['category'] != 'ignore'))

    draft = {
        'file': filename,
        'extraction_sha256': source_ext_hash,
        'human_verified': False,
        'status': 'unverified_draft',
        'llm_review_status': llm_status,
        'llm_review':llm_metadata,
        'uncertainty_summary': {
            'total_spans': len(spans),
            'uncertain_spans': uncertain_count,
            'unassigned_spans':sum(s['category']=='needs_review' for s in spans),
            'disagreement_spans':sum(s.get('local_category') in CATEGORIES and s.get('llm_category') in CATEGORIES and s['local_category']!=s['llm_category'] for s in spans),
            'artifact_spans':sum(s['category']=='ignore' for s in spans),
            'uncertainty_rate': round(uncertain_count / len(spans), 4) if spans else 0,
        },
        'spans': spans,
        'records': {
            'work_experience': work_records,
            'education': edu_records
        },
        'metadata': {
            'source_artifact': str(artifact_path),
            'page_count': len(art.get('extraction', {}).get('metadata', {}).get('page_numbers', [])),
            'total_elements': len(elements),
            'categories_present': categories_present,
            'generator': 'deterministic_rules_with_deepseek_review_v1',
            'schema_version': 'ground_truth_v1.0'
        }
    }
    return draft


def generate_html_review(draft, output_path):
    f_esc = html.escape(draft['file'])
    uncertain_cnt = draft['uncertainty_summary']['uncertain_spans']
    total_spans = draft['uncertainty_summary']['total_spans']

    rows = []
    for s in draft['spans']:
        text_esc = html.escape(s['text'])
        cat = s['category']
        unc = s['uncertainty_flag']
        reason = html.escape(s['uncertainty_reason'] or '')
        row_cls = "uncertain-row" if unc else ""
        badge = f"<span class='badge badge-warning'>Uncertain: {reason}</span>" if unc else "<span class='badge badge-success'>Assigned proposal — unverified</span>"
        role = s.get('field_role') or ''
        rec_id = s.get('record_id') or ''
        rec_info = f"{s.get('record_type') or ''} ({rec_id}): {role}" if rec_id else role

        rows.append(f"""
        <tr class="{row_cls}">
            <td><code>{s['span_id']}</code></td>
            <td>P{s['page_number']} E{s['source_element_index']} [{s['start']}:{s['end']}]</td>
            <td><span class="cat-pill cat-{cat}">{cat}</span></td>
            <td><small>{rec_info}</small></td>
            <td><pre class="span-text">{text_esc}</pre></td>
            <td>{badge}</td>
        </tr>
        """)

    exp_cards = []
    for r in draft['records']['work_experience']:
        resp_list = "".join(f"<li>{html.escape(item)}</li>" for item in r.get('responsibilities', []))
        exp_cards.append(f"""
        <div class="card mb-2">
            <div class="card-body">
                <h5 class="card-title">{html.escape(r['title'] or 'Work record proposal')} @ {html.escape(r['employer'] or 'Employer requires review')}</h5>
                <pre>{html.escape(r.get('source_text',r.get('header_text','')))}</pre>
                <h6 class="card-subtitle text-muted">{html.escape(r['dates'])} | Client: {html.escape(r.get('client') or 'N/A')}</h6>
                <ul class="mt-2">{resp_list}</ul>
                <small class="text-muted">Linked Spans: {len(r.get('span_ids', []))}</small>
            </div>
        </div>
        """)

    edu_cards = []
    for r in draft['records']['education']:
        edu_cards.append(f"""
        <div class="card mb-2">
            <div class="card-body">
                <h5 class="card-title">{html.escape(r['degree'] or 'Education record proposal')}</h5>
                <pre>{html.escape(r.get('source_text',''))}</pre>
                <h6 class="card-subtitle text-muted">{html.escape(r['institution'])} ({html.escape(r['year'])}) | Grade: {html.escape(r.get('grade') or 'N/A')}</h6>
                <small class="text-muted">Linked Spans: {len(r.get('span_ids', []))}</small>
            </div>
        </div>
        """)

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Ground Truth Draft Review: {f_esc}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
<style>
body {{ padding: 20px; background: #f8f9fa; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
.header-box {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }}
.span-text {{ margin: 0; white-space: pre-wrap; word-break: break-word; font-size: 0.85rem; max-height: 150px; overflow-y: auto; background: #fff; padding: 4px 8px; border: 1px solid #dee2e6; border-radius: 4px; }}
.uncertain-row {{ background-color: #fff3cd !important; }}
.cat-pill {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
.cat-personal_information {{ background: #e3f2fd; color: #0d47a1; }}
.cat-summary {{ background: #f3e5f5; color: #4a148c; }}
.cat-experience {{ background: #e8f5e9; color: #1b5e20; }}
.cat-education {{ background: #fff3e0; color: #e65100; }}
.cat-skills {{ background: #e0f2f1; color: #004d40; }}
.cat-projects {{ background: #ede7f6; color: #311b92; }}
.cat-certifications {{ background: #fbe9e7; color: #bf360c; }}
.cat-awards {{ background: #fffde7; color: #f57f17; }}
.cat-languages {{ background: #f1f8e9; color: #33691e; }}
.cat-ignore {{ background: #cfd8dc; color: #37474f; }}
.badge-warning {{ background-color: #ffc107; color: #212529; padding: 4px 8px; border-radius: 4px; font-weight: 500; }}
.badge-success {{ background-color: #198754; color: white; padding: 4px 8px; border-radius: 4px; }}
</style>
</head>
<body>
<div class="container-fluid">
    <div class="header-box">
        <h2>Draft Review: <code>{f_esc}</code></h2>
        <div class="row mt-3">
            <div class="col-md-3"><strong>Status:</strong> <span class="badge bg-secondary">UNVERIFIED DRAFT</span></div>
            <div class="col-md-3"><strong>Spans:</strong> {total_spans} ({uncertain_cnt} flagged for review)</div>
            <div class="col-md-3"><strong>LLM Review:</strong> <code>{draft['llm_review_status']}</code></div>
            <div class="col-md-3"><strong>SHA256:</strong> <code>{draft['extraction_sha256'][:16]}...</code></div>
        </div>
    </div>

    <ul class="nav nav-tabs" id="myTab" role="tablist">
        <li class="nav-item"><a class="nav-link active" data-bs-toggle="tab" href="#spans">All Spans ({total_spans})</a></li>
        <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#experience">Work Experience Records ({len(draft['records']['work_experience'])})</a></li>
        <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#education">Education Records ({len(draft['records']['education'])})</a></li>
    </ul>

    <div class="tab-content mt-3 bg-white p-3 rounded shadow-sm">
        <div class="tab-pane fade show active" id="spans">
            <table class="table table-sm table-hover align-middle">
                <thead class="table-light">
                    <tr>
                        <th>Span ID</th>
                        <th>Source Location</th>
                        <th>Proposed Category</th>
                        <th>Role / Record</th>
                        <th style="width: 45%;">Source Text</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>
        </div>
        <div class="tab-pane fade" id="experience">
            {"".join(exp_cards) if exp_cards else "<p class='text-muted'>No experience records detected.</p>"}
        </div>
        <div class="tab-pane fade" id="education">
            {"".join(edu_cards) if edu_cards else "<p class='text-muted'>No education records detected.</p>"}
        </div>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
    output_path.write_text(content, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selected-json', type=Path, default=ROOT / 'ground_truth/selected_15_resumes.json')
    parser.add_argument('--drafts-dir', type=Path, default=ROOT / 'ground_truth/drafts')
    parser.add_argument('--cache-dir', type=Path, default=ROOT / 'ground_truth/cache/llm_reviews')
    parser.add_argument('--cached-only', action='store_true',help='Rebuild annotations from validated saved review only; never call provider')
    parser.add_argument('--skip-deepseek', action='store_true', help="Skip live DeepSeek review")
    args = parser.parse_args()

    args.drafts_dir.mkdir(parents=True, exist_ok=True)
    if args.cache_dir:
        args.cache_dir.mkdir(parents=True, exist_ok=True)

    with open(args.selected_json) as f:
        selected = json.load(f)

    manifest_entries = []
    print(f"Generating draft ground truth for {len(selected)} resumes...")

    for i, s in enumerate(selected, 1):
        filename = s['file']
        art_path = ROOT / '.upstream/batch-validation' / s['artifact']
        print(f"[{i:2d}/{len(selected)}] Processing {filename}...")

        draft = generate_draft(filename, art_path, cache_dir=args.cache_dir, use_deepseek=not args.skip_deepseek,cached_only=args.cached_only)

        safe_stem = Path(filename).stem.replace(' ', '_').replace('(', '').replace(')', '')
        draft_file = args.drafts_dir / f"{safe_stem}.json"
        draft_file.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + '\n')

        html_file = args.drafts_dir / f"{safe_stem}_review.html"
        generate_html_review(draft, html_file)

        manifest_entries.append({
            'file': filename,
            'draft_json': str(draft_file.relative_to(ROOT)),
            'review_html': str(html_file.relative_to(ROOT)),
            'total_spans': draft['uncertainty_summary']['total_spans'],
            'uncertain_spans': draft['uncertainty_summary']['uncertain_spans'],
            'unassigned_spans':draft['uncertainty_summary']['unassigned_spans'],
            'disagreement_spans':draft['uncertainty_summary']['disagreement_spans'],
            'categories': draft['metadata']['categories_present'],
            'llm_review_status': draft['llm_review_status']
        })

    # Master index
    index_file = args.drafts_dir / "index.html"
    index_rows = []
    for m in manifest_entries:
        index_rows.append(f"""
        <tr>
            <td><strong>{html.escape(m['file'])}</strong></td>
            <td><a href="{Path(m['review_html']).name}" class="btn btn-sm btn-outline-primary" target="_blank">Review Draft</a></td>
            <td><code>{m['total_spans']}</code></td>
            <td><span class="badge { 'bg-warning text-dark' if m['uncertain_spans'] > 0 else 'bg-success' }">{m['uncertain_spans']}</span></td>
            <td>{m['unassigned_spans']}</td><td>{m['disagreement_spans']}</td>
            <td><code>{m['llm_review_status']}</code> (provider response only)</td>
            <td><small>{", ".join(m['categories'])}</small></td>
        </tr>
        """)

    index_html = f"""<!DOCTYPE html>
<html>
<head>
<title>Ground Truth Pilot Review Dashboard (15 Resumes)</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="p-4 bg-light">
<div class="container bg-white p-4 rounded shadow-sm">
    <h2>Ground Truth Pilot Review Dashboard</h2>
    <p class="text-muted">Initial 15 Representative Resumes for Human Review & Validation</p>
    <table class="table table-hover align-middle mt-3">
        <thead class="table-light">
            <tr>
                <th>Resume</th>
                <th>Action</th>
                <th>Total Spans</th>
                <th>Human-review flags (includes disagreements)</th><th>Unassigned spans</th><th>Local/LLM disagreements</th>
                <th>Provider response status</th>
                <th>Categories Detected</th>
            </tr>
        </thead>
        <tbody>
            {"".join(index_rows)}
        </tbody>
    </table>
</div>
</body>
</html>
"""
    index_file.write_text(index_html, encoding='utf-8')
    print(f"\nAll 15 drafts generated in {args.drafts_dir}")
    print(f"Master review dashboard created at {index_file}")


if __name__ == '__main__':
    main()
