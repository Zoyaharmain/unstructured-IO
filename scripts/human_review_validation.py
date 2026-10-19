"""Validate human decisions and source-backed record associations, without model calls."""
import copy
import hashlib
import json
import re
from pathlib import Path
from scripts.evaluate_resume_ground_truth import extraction_hash,label_map,CATEGORIES

ATTESTATIONS=('original_pdf_all_pages_checked','section_assignments_checked','missing_duplicate_content_checked','record_relationships_checked')
FIELDS={'work_experience':('employer','title','dates'),'education':('degree','institution','year')}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def normalized(text):return ' '.join(str(text).casefold().split())


def validate_annotation(annotation,elements,require_human=False,decisions=None):
    issues=[]
    if annotation.get('extraction_sha256')!=extraction_hash(elements):issues.append('source_hash_mismatch')
    spans=annotation.get('spans',[]);by_id={s.get('span_id'):s for s in spans}
    if len(by_id)!=len(spans) or None in by_id:issues.append('duplicate_or_missing_span_id')
    try:label_map(elements,spans,CATEGORIES|{'ignore'})
    except (ValueError,KeyError,TypeError) as exc:issues.append('invalid_source_coverage: '+str(exc))
    for span in spans:
        sid=span.get('span_id','?');i=span.get('source_element_index')
        if type(i)!=int or not 0<=i<len(elements):continue
        if span.get('text')!=elements[i]['text'][span.get('start',0):span.get('end',0)]:issues.append(sid+': source_text_changed')
        if require_human:
            decision=(decisions or {}).get(sid,{})
            if decision.get('action') not in {'approve','correct','artifact','duplicate'}:issues.append(sid+': human_decision_missing')
            if span.get('category')=='ignore':
                if not decision.get('reason','').strip():issues.append(sid+': ignored_content_reason_missing')
                if decision.get('action')=='duplicate':
                    other=by_id.get(decision.get('duplicate_of'))
                    if not other or other is span or normalized(other['text'])!=normalized(span['text']):issues.append(sid+': duplicate_evidence_invalid')
    block_categories={}
    for span in spans:
        block_id=span.get('block_id')
        if block_id:
            previous=block_categories.setdefault(block_id,span.get('category'))
            if previous!=span.get('category'):issues.append(block_id+': logical_block_crosses_sections')
    membership={};record_ids=set()
    for kind,fields in FIELDS.items():
        category='experience' if kind=='work_experience' else 'education'
        for record in annotation.get('records',{}).get(kind,[]):
            rid=record.get('record_id','?')
            if rid in record_ids:issues.append(rid+': duplicate_record_id')
            record_ids.add(rid)
            ids=record.get('span_ids',[])
            if not ids:issues.append(rid+': empty_record')
            for sid in ids:
                span=by_id.get(sid)
                if not span:issues.append(rid+': unknown_member '+sid);continue
                if span['category']!=category:issues.append(rid+': wrong_section_member '+sid)
                if sid in membership:issues.append(sid+': shared_between_records '+membership[sid]+' / '+rid)
                membership[sid]=rid
            for field in fields:
                value=record.get(field,'');state=record.get('field_states',{}).get(field)
                refs=record.get('field_evidence',{}).get(field,[])
                if not value:
                    if state!='not_in_source' or not record.get('field_notes',{}).get(field,'').strip():issues.append(rid+': '+field+'_unverified_or_missing')
                    continue
                if state not in {None,'present'}:issues.append(rid+': '+field+'_state_conflicts_with_value')
                if not refs or any(sid not in ids for sid in refs):issues.append(rid+': '+field+'_evidence_outside_record');continue
                quoted=' '.join(by_id[sid]['text'] for sid in refs if sid in by_id)
                if normalized(value) not in normalized(quoted):issues.append(rid+': '+field+'_unsupported_value')
            if require_human and record.get('human_relationship_decision')!='approved':issues.append(rid+': relationship_not_human_approved')
    for span in spans:
        if span.get('category') in {'experience','education'} and span.get('field_role')!='heading' and span.get('text','').strip() and span.get('span_id') not in membership:
            issues.append(span['span_id']+': record_membership_missing')
    return sorted(set(issues))


def validate_bundle(bundle,draft_path,pdf_path,elements):
    issues=[]
    if bundle.get('draft_sha256')!=sha(draft_path):issues.append('stale_draft_hash')
    if bundle.get('source_pdf_sha256')!=sha(pdf_path):issues.append('stale_pdf_hash')
    if not str(bundle.get('reviewer','')).strip():issues.append('reviewer_missing')
    if bundle.get('decision')!='approve':issues.append('explicit_approval_missing')
    for key in ATTESTATIONS:
        if bundle.get('attestations',{}).get(key) is not True:issues.append(key+': not_checked')
    from pypdf import PdfReader
    expected=list(range(1,len(PdfReader(pdf_path).pages)+1))
    if sorted(set(bundle.get('reviewed_pages',[])))!=expected:issues.append('not_all_pdf_pages_reviewed')
    if any(issue.get('status')!='resolved' for issue in bundle.get('pdf_issues',[])):issues.append('unresolved_pdf_content_issues')
    # Known source discrepancies cannot be hidden by deleting issue rows.
    findings_path=Path(__file__).resolve().parents[1]/'ground_truth/human_review/audit/content-blockers.json'
    required=[]
    if findings_path.exists():
        required=json.loads(findings_path.read_text()).get(json.loads(Path(draft_path).read_text()).get('file'),[])
        supplied={item.get('id'):item for item in bundle.get('pdf_issues',[])}
        for item in required:
            if item['id'] not in supplied:issues.append(item['id']+': known_source_finding_missing')
            elif supplied[item['id']].get('kind')!=item['kind']:issues.append(item['id']+': source_finding_kind_changed')
    annotation=bundle.get('annotation',{})
    original=json.loads(Path(draft_path).read_text())
    if annotation.get('file')!=original.get('file'):issues.append('annotation_file_mismatch')
    old_spans={s['span_id']:s for s in original['spans']}
    for span in annotation.get('spans',[]):
        before=old_spans.get(span.get('span_id'))
        action=bundle.get('span_decisions',{}).get(span.get('span_id'),{}).get('action')
        if span.get('category')=='ignore' and action not in {'artifact','duplicate'}:issues.append(span.get('span_id','?')+': explicit_artifact_decision_required')
        if action=='approve' and (not before or any(span.get(k)!=before.get(k) for k in ('category','start','end','source_element_index','text'))):issues.append(span.get('span_id','?')+': changed_prediction_requires_correction_decision')
    for issue in bundle.get('pdf_issues',[]):
        if issue.get('status')=='resolved' and not issue.get('resolution_note','').strip():issues.append('resolved_pdf_issue_needs_explanation')
        if issue.get('kind')=='missing_text' and issue.get('status')=='resolved' and issue.get('resolution')!='false_alarm':
            finding=next((x for x in required if x['id']==issue.get('id')), {})
            old_hash=finding.get('original_extraction_sha256')
            current_text=' '.join(e['text'] for e in elements)
            if not (issue.get('resolution')=='reextracted' and old_hash and annotation.get('extraction_sha256')!=old_hash and normalized(finding.get('text','')) in normalized(current_text)):
                issues.append('missing_pdf_text_requires_new_extraction_and_rebased_review')
    issues.extend(validate_annotation(annotation,elements,True,bundle.get('span_decisions',{})))
    return sorted(set(issues))


def score_record_relationships(predicted,reference):
    """Strict employer/title/date and degree/institution/year tuple scoring.

    Only explicit human-approved reference versions are eligible. Equal entry
    counts never imply correct relationships. Not run against legacy auto-gold.
    """
    from collections import Counter
    if reference.get('human_verified') is not True or not reference.get('review_provenance',{}).get('approved_bundle_sha256'):
        raise ValueError('Explicitly human-approved reference provenance required for relationship scoring')
    if predicted.get('extraction_sha256')!=reference.get('extraction_sha256'):raise ValueError('Relationship source inventories differ')
    result={}
    for kind,fields in FIELDS.items():
        def tuples(data):
            complete=[];incomplete=0
            for record in data.get('records',{}).get(kind,[]):
                if any(not record.get(field) and record.get('field_states',{}).get(field)!='not_in_source' for field in fields):incomplete+=1;continue
                complete.append(tuple(normalized(record.get(field,'')) for field in fields))
            return Counter(complete),incomplete
        expected,missing_reference=tuples(reference)
        if missing_reference:raise ValueError('Human reference relationships remain incomplete')
        actual,incomplete=tuples(predicted);matches=sum((expected&actual).values());expected_count=sum(expected.values());actual_count=sum(actual.values())
        precision=matches/actual_count if actual_count else (1.0 if not expected_count else 0.0)
        recall=matches/expected_count if expected_count else 1.0
        result[kind]={'reference_records':expected_count,'complete_predicted_records':actual_count,'incomplete_predicted_records':incomplete,
                      'exact_relationship_matches':matches,'precision':precision,'recall':recall,
                      'f1':2*precision*recall/(precision+recall) if precision+recall else 0.0}
    return result
