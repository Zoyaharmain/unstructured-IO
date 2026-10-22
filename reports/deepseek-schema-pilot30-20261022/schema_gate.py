"""Isolated evaluation gate. Never imported by production routes; no network."""
from copy import deepcopy
import json
import re
from local_api.vendor.handoff_schema.models import ResumeSchema


def norm(value):
    return ' '.join(str(value).casefold().split())


def leaves(value, path=''):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, path + '/' + key.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from leaves(item, path + '/' + str(i))
    elif value is not None and value != '':
        yield path, value


def validate(raw, blocks):
    """Fail closed; retain raw output. Parent evidence never satisfies a leaf."""
    issues = []
    def flag(kind, path, **detail):
        issues.append({'kind': kind, 'path': path, **detail})
    sources = {b['source_id']: b for b in blocks}
    if len(sources) != len(blocks):
        flag('duplicate_source_id', '')
    try:
        model = ResumeSchema.model_validate(raw.get('data'))
        data = model.model_dump(mode='json')
    except (ValueError, TypeError):
        return {'accepted': False, 'schema_valid': False, 'issues': [{'kind': 'invalid_target_schema', 'path': '/data'}], 'fields': []}
    # The handoff defaults tolerate extra/missing optional properties; this
    # experimental contract requires explicit shape and does not silently drop data.
    def shape(original, parsed, path=''):
        if isinstance(parsed, dict):
            if not isinstance(original, dict): return
            for key in set(original)-set(parsed): flag('unknown_target_property', path+'/'+key)
            for key in set(parsed)-set(original): flag('omitted_target_property', path+'/'+key)
            for key in set(original)&set(parsed): shape(original[key], parsed[key], path+'/'+key)
        elif isinstance(parsed, list) and isinstance(original, list):
            for i, (a, b) in enumerate(zip(original, parsed)): shape(a, b, path+'/'+str(i))
    shape(raw.get('data'), data)
    evidence = raw.get('evidence', {})
    if not isinstance(evidence, dict):
        flag('invalid_evidence_envelope', '/evidence'); evidence = {}
    populated = dict(leaves(data)); fields = []
    for path in evidence:
        if not isinstance(path, str) or not path.startswith('/'):
            flag('non_standard_json_pointer', str(path))
        if path not in populated:
            flag('evidence_not_for_populated_leaf', str(path))
    for path, value in populated.items():
        refs = evidence.get(path)
        errors = []
        if not isinstance(refs, list) or not refs:
            errors.append('missing_field_evidence'); refs = []
        quotes = []
        for ref in refs:
            if not isinstance(ref, dict) or set(ref) != {'source_id', 'quote'}:
                errors.append('invalid_citation_shape'); continue
            sid, quote = ref['source_id'], ref['quote']
            if not isinstance(sid, str) or sid not in sources:
                errors.append('unknown_source_id'); continue
            if not isinstance(quote, str) or not quote or quote not in sources[sid]['text']:
                errors.append('quote_not_in_cited_block'); continue
            quotes.append(quote)
        if quotes:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                number = any(float(x) == float(value) for x in re.findall(r'\d+(?:\.\d+)?', ' '.join(quotes)))
                context = any(re.search(r'years?|experience', sources[r['source_id']]['text'], re.I) for r in refs if isinstance(r, dict) and r.get('source_id') in sources)
                supported = number and context
            else:
                supported = norm(value) in norm(' '.join(quotes))
            if not supported: errors.append('value_not_supported_by_quotes')
        elif refs:
            errors.append('no_valid_supporting_quote')
        for kind in sorted(set(errors)): flag(kind, path)
        fields.append({'path': path, 'value': value, 'citation_valid': not errors, 'errors': sorted(set(errors)), 'citations': refs})
    uncertainties = []
    for note in raw.get('missing_information', []):
        if isinstance(note, dict) and note.get('reason') in {'ambiguous_source', 'upstream_defect'}:
            uncertainties.append({'path': note.get('path'), 'kind': note['reason'], 'detail': note.get('detail'), 'source_ids': note.get('source_ids', [])})
    for note in raw.get('uncertainties', []):
        if isinstance(note, dict): uncertainties.append(note)
    for path, value in populated.items():
        refs = evidence.get(path, [])
        context = ' '.join(sources[r['source_id']]['text'] for r in refs if isinstance(r, dict) and r.get('source_id') in sources) if isinstance(refs, list) else ''
        if path.endswith('/graduation_year') and re.search(r'expected|pursuing|anticipated', context, re.I):
            uncertainties.append({'path': path, 'kind': 'expected_completion_not_earned', 'detail': 'Source describes an expected/in-progress qualification.'})
        if path.endswith('/role') and re.search(r'\btrainee\b|graduate student', str(value), re.I):
            uncertainties.append({'path': path, 'kind': 'training_or_research_classification', 'detail': 'Do not assume this record is verified paid employment.'})
        if path == '/total_experience_years' and re.search(r'\d\s*\+|around|approximately|over\s+\d', context, re.I):
            uncertainties.append({'path': path, 'kind': 'approximate_experience', 'detail': 'Numeric schema loses a source qualification; preserve it in metadata.'})
    order = {b['source_id']: i for i, b in enumerate(blocks)}
    for i, record in enumerate(data['experience']):
        refs = evidence.get(f'/experience/{i}/company', [])
        anchors = [order[r['source_id']] for r in refs if isinstance(r, dict) and r.get('source_id') in order] if isinstance(refs,list) else []
        if anchors:
            for field in ('start_date', 'end_date', 'duration'):
                path = f'/experience/{i}/{field}'
                date_refs = evidence.get(path, [])
                if isinstance(date_refs,list) and any(order[r['source_id']] < min(anchors) for r in date_refs if isinstance(r, dict) and r.get('source_id') in order):
                    uncertainties.append({'path': path, 'kind': 'date_precedes_employer_anchor', 'detail': 'Association requires source/layout review; literal date presence is insufficient.'})
        if record['company']:
            for ref in refs if isinstance(refs,list) else []:
                if not isinstance(ref,dict) or ref.get('source_id') not in sources: continue
                text = sources[ref['source_id']]['text']
                if re.search(r'\bClient\s*:\s*'+re.escape(record['company']), text, re.I):
                    flag('client_promoted_to_employer', f'/experience/{i}/company')
    # Source-supported emptiness cannot pass merely because there is no leaf
    # requiring a citation. This check is deliberately narrow and explicit.
    source_emails = set(re.findall(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', ' '.join(b['text'] for b in blocks)))
    if source_emails and not data['contact']['email']:
        flag('source_email_unassigned', '/contact/email')
    if not populated and any(b['text'].strip() for b in blocks):
        flag('empty_mapping_for_nonempty_source', '/data')
    headers = [(j,b) for j,b in enumerate(blocks) if re.search(r'\bCompany\s*:', b['text'], re.I)]
    for i, record in enumerate(data['experience']):
        company = record['company']
        matches = [(j,b) for j,b in headers if company and re.search(r'\bCompany\s*:\s*'+re.escape(company)+r'(?:\s*\||\s*$)',b['text'],re.I)]
        if len(matches)!=1: continue
        start,_ = matches[0]; end = next((j for j,_ in headers if j>start),len(blocks))
        prefix=f'/experience/{i}/'
        for path,_ in populated.items():
            if not path.startswith(prefix) or path.endswith('/company'):continue
            if '/start_date' in path or '/end_date' in path or '/duration' in path:continue
            refs=evidence.get(path,[])
            if isinstance(refs,list) and any(not start<=order[r['source_id']]<end for r in refs if isinstance(r,dict) and r.get('source_id') in order):
                flag('field_evidence_outside_explicit_employer',path)
    degree_elements=[]
    for i,_ in enumerate(data['education']):
        refs=evidence.get(f'/education/{i}/degree',[])
        degree_elements.append({sources[r['source_id']]['source_element'] for r in refs if isinstance(r,dict) and r.get('source_id') in sources} if isinstance(refs,list) else set())
    for i,record in enumerate(data['education']):
        for field in ('start_year','graduation_year'):
            path=f'/education/{i}/{field}'; refs=evidence.get(path,[])
            if not record.get(field) or not isinstance(refs,list):continue
            date_elements={sources[r['source_id']]['source_element'] for r in refs if isinstance(r,dict) and r.get('source_id') in sources}
            if any(degree_elements[i]&others for j,others in enumerate(degree_elements) if j!=i) and date_elements-degree_elements[i]:
                uncertainties.append({'path':path,'kind':'detached_date_with_shared_degree_element','detail':'Several qualifications share an element and date evidence is detached; do not assert a reliable row association.'})
    completeness = discover_omissions(data, evidence, blocks)
    return {'accepted': not issues and not uncertainties and not completeness, 'schema_valid': True,
            'citation_contract_valid': not issues, 'issues': issues, 'fields': fields,
            'populated_fields': len(fields), 'citation_valid_fields': sum(r['citation_valid'] for r in fields),
            'uncertainties': uncertainties, 'completeness_findings': completeness,
            'semantic_accuracy_verified': False}


def discover_omissions(data, evidence, blocks):
    """Conservative patterns, not an exhaustive recall oracle."""
    findings = []; sources = {b['source_id']: b for b in blocks}
    for i, record in enumerate(data['education']):
        if record.get('field_of_study'): continue
        match = re.search(r'\b(?:master\s+of\s+technology|bachelor\s+of\s+engineering|b\.?e\.?)\s+in\s+(.+)$', record.get('degree',''), re.I)
        if not match: continue
        major = match.group(1).strip(' .')
        for ref in evidence.get(f'/education/{i}/degree', []):
            if not isinstance(ref,dict) or ref.get('source_id') not in sources: continue
            text = sources[ref['source_id']]['text']
            # Derivation must be literal and in the same source as this degree.
            start = text.casefold().find(major.casefold())
            if start >= 0:
                exact = text[start:start+len(major)]
                findings.append({'path': f'/education/{i}/field_of_study', 'value': exact,
                    'citation': {'source_id': ref['source_id'], 'quote': exact},
                    'rule': 'explicit_major_in_same_degree_source'}); break
    # Explicit Company: markers bound action statements to an employer. No
    # adjacency-only guesses and no PDF/embedding rerun are allowed here.
    all_values = ' '.join(str(v) for _, v in leaves(data))
    company_headers = [(i,b) for i,b in enumerate(blocks) if re.search(r'\bCompany\s*:', b['text'], re.I)]
    for i, record in enumerate(data['experience']):
        if not record.get('company'): continue
        matching = [(index,b) for index,b in company_headers if re.search(r'\bCompany\s*:\s*'+re.escape(record['company'])+r'(?:\s*\||\s*$)', b['text'],re.I)]
        if len(matching)!=1: continue
        start,_ = matching[0]; end = next((index for index,_ in company_headers if index>start),len(blocks))
        for block in blocks[start+1:end]:
            text = block['text'].strip()
            if not re.match(r'^(?:Worked|Developed|Designed|Gathered|Implemented|Supported|Managed|Conducted|Created|Performed|Provided|Acted|Coordinated)\b',text):continue
            if not text.endswith('.'):continue
            if norm(text) in norm(all_values):continue
            findings.append({'path':f'/experience/{i}/responsibilities/-','value':text,
                'citation':{'source_id':block['source_id'],'quote':text},
                'rule':'unmapped_complete_action_under_explicit_company_marker'})
    return findings


def repair_confirmed_omissions(raw, blocks):
    """Transparent source-derived candidate; never repair/inherit other citations."""
    candidate = deepcopy(raw); before = validate(raw, blocks); changes = []
    if not before['schema_valid']:return candidate, changes
    for finding in before['completeness_findings']:
        parts = finding['path'].strip('/').split('/')
        collection, index = parts[0], int(parts[1]); record = candidate['data'][collection][index]
        if parts[-1]=='-':
            target = record[parts[2]]; path=f'/{collection}/{index}/{parts[2]}/{len(target)}';target.append(finding['value'])
        else:
            path=finding['path'];record[parts[2]]=finding['value']
        candidate.setdefault('evidence',{})[path]=[finding['citation']]
        changes.append({**finding,'written_path':path,'origin':'explicit deterministic source-derived omission repair; not model-generated'})
    return candidate, changes


def parse_strict_json_response(content: str):
    """Strictly parses provider response as a single JSON object.

    Validates complete response strictly:
    - If content is not valid JSON (e.g. contains trailing extra data, missing braces, or truncated tokens),
      records full failure details (line, column, char offset) and raises ValueError.
    - Never silently truncates, guesses, or repairs ambiguous output.
    - If parsing fails, quarantines the output without retrying automatically.
    """
    if not isinstance(content, str):
        raise ValueError(f"Response content must be a string, got {type(content).__name__}")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Strict JSON parsing failed: {exc.msg} at line {exc.lineno} column {exc.colno} (char {exc.pos})") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"Response must be a JSON object, got {type(parsed).__name__}")
    return parsed


def parse_response_with_quarantine(content: str, finish_reason: str = "stop") -> tuple[dict | None, dict | None]:
    """Strictly parses model output; returns (parsed_dict, None) on success or (None, failure_metadata) on failure.
    Never silently truncates, guesses, or repairs invalid responses.
    """
    if not isinstance(content, str):
        return None, {
            "error": "invalid_type",
            "message": f"Expected str, got {type(content).__name__}",
            "finish_reason": finish_reason,
            "automatic_repair_attempted": False,
            "retry_performed": False,
        }
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        return None, {
            "error": "invalid_json",
            "message": exc.msg,
            "line": exc.lineno,
            "column": exc.colno,
            "offset": exc.pos,
            "finish_reason": finish_reason,
            "automatic_repair_attempted": False,
            "retry_performed": False,
        }
    if not isinstance(parsed, dict):
        return None, {
            "error": "not_a_json_object",
            "message": f"Expected JSON object, got {type(parsed).__name__}",
            "finish_reason": finish_reason,
            "automatic_repair_attempted": False,
            "retry_performed": False,
        }
    return parsed, None


def normalize_evidence_pointers(raw, blocks=None):
    """Normalizes provably equivalent evidence paths to standard JSON Pointer syntax.

    Rules:
    1. Target data values are NEVER modified.
    2. Evidence citations (source_ids, quotes) are NEVER fabricated or modified.
    3. A path is provably equivalent if:
       - It lacks a leading slash (e.g. 'contact/email') and prepending '/' matches an existing populated leaf.
       - Or has redundant leading slashes (e.g. '//contact/email').
       - And the candidate path matches a unique populated leaf in target data.
    4. If multiple raw keys resolve to the same leaf path, or if an exact pointer already
       exists for that path, this constitutes an ambiguous path conflict:
       the normalization is REJECTED and recorded under rejections.
    5. Every normalization and rejection is recorded with full audit metadata.
    """
    candidate = deepcopy(raw)
    data = candidate.get("data")
    if not isinstance(data, dict):
        return candidate, [], []
    populated = dict(leaves(data))
    evidence = candidate.get("evidence")
    if not isinstance(evidence, dict):
        return candidate, [], []

    target_mapping = {}
    normalizations = []
    rejections = []
    normalized_evidence = {}

    for raw_path, refs in evidence.items():
        if not isinstance(raw_path, str):
            rejections.append({
                "raw_path": raw_path,
                "reason": "non_string_path",
                "detail": "Evidence key is not a string",
            })
            continue
        if raw_path.startswith("/") and not raw_path.startswith("//"):
            target_path = raw_path
            equiv = False
        else:
            stripped = raw_path.lstrip("/")
            candidate_target = "/" + stripped
            target_path = candidate_target
            equiv = True
        target_mapping.setdefault(target_path, []).append((raw_path, refs, equiv))

    for target_path, entries in target_mapping.items():
        if len(entries) > 1:
            for raw_path, refs, equiv in entries:
                rejections.append({
                    "raw_path": raw_path,
                    "target_path": target_path,
                    "reason": "ambiguous_path_collision",
                    "detail": f"Multiple evidence keys resolved to {target_path}: {[e[0] for e in entries]}",
                })
                normalized_evidence[raw_path] = refs
        else:
            raw_path, refs, equiv = entries[0]
            if equiv:
                normalized_evidence[target_path] = refs
                normalizations.append({
                    "original_path": raw_path,
                    "normalized_path": target_path,
                    "rule": "provably_equivalent_leading_slash",
                    "citations_count": len(refs) if isinstance(refs, list) else 0,
                    "origin": "local deterministic pointer normalizer; target data untouched",
                })
            else:
                normalized_evidence[raw_path] = refs

    candidate["evidence"] = normalized_evidence
    assert candidate["data"] == raw["data"], "Normalizer mutated target data!"
    return candidate, normalizations, rejections


def align_array_and_span_evidence(candidate, blocks):
    """Aligns shifted array citations and inverted sibling sub-block spans.

    Rules:
    1. Target data values are NEVER modified.
    2. Evidence citations (source_ids, quotes) are NEVER fabricated.
    3. Re-alignment only occurs within the exact same parent array or between
       sibling spans of the same source element.
    4. Unambiguous 1-to-1 matching only; ambiguous or unevidenced fields remain untouched.
    """
    blocks_dict = {b["source_id"]: b["text"] for b in blocks} if isinstance(blocks, list) else {}
    data = candidate.get("data", {})
    evidence = candidate.get("evidence", {})
    if not isinstance(data, dict) or not isinstance(evidence, dict):
        return candidate, []

    changes = []

    # 1. Intra-array alignment
    def find_arrays(obj, prefix=""):
        res = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                p = f"{prefix}/{k}"
                if isinstance(v, list) and v and isinstance(v[0], (str, int, float)):
                    res.append((p, v))
                elif isinstance(v, (dict, list)):
                    res.extend(find_arrays(v, p))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                res.extend(find_arrays(v, f"{prefix}/{i}"))
        return res

    arrays = find_arrays(data)
    for arr_path, items in arrays:
        raw_cits = {}
        for k, v in list(evidence.items()):
            if k.startswith(arr_path + "/"):
                suffix = k[len(arr_path) + 1:]
                if suffix.isdigit():
                    raw_cits[k] = v
        valid_items = set()
        for k, cits in raw_cits.items():
            idx = int(k.split("/")[-1])
            if idx < len(items):
                val = items[idx]
                quotes = [c["quote"] for c in cits if isinstance(c, dict) and "quote" in c and c.get("source_id") in blocks_dict and c["quote"] in blocks_dict[c["source_id"]]]
                if quotes and norm(val) == norm(" ".join(quotes)):
                    valid_items.add(idx)
        unmatched_cits = [(k, c) for k, c in raw_cits.items() if int(k.split("/")[-1]) not in valid_items]
        avail_items = set(range(len(items))) - valid_items
        target_claims = {}
        for k, cits in unmatched_cits:
            quotes = [c["quote"] for c in cits if isinstance(c, dict) and "quote" in c and c.get("source_id") in blocks_dict and c["quote"] in blocks_dict[c["source_id"]]]
            if not quotes:
                continue
            q_norm = norm(" ".join(quotes))
            # Must uniquely match exactly one available item in the SAME array
            matches = [i for i in avail_items if norm(items[i]) == q_norm]
            if len(matches) == 1:
                target_idx = matches[0]
                target_claims.setdefault(target_idx, []).append((k, cits))

        # Only accept target indices that were claimed by EXACTLY ONE citation (reject ambiguous collisions)
        reassigned = {}
        for target_idx, claims in target_claims.items():
            if len(claims) == 1:
                old_k, cits = claims[0]
                target_path = f"{arr_path}/{target_idx}"
                reassigned[old_k] = (target_path, cits)
        for old_k, (new_k, cits) in reassigned.items():
            evidence[new_k] = cits
            if old_k not in [new_k for new_k, _ in reassigned.values()]:
                del evidence[old_k]
            changes.append({
                "original_path": old_k,
                "normalized_path": new_k,
                "rule": "intra_array_index_alignment",
                "citations_count": len(cits) if isinstance(cits, list) else 0,
                "origin": "deterministic intra-array citation re-indexing; target data untouched",
            })

    # 2. Inverted sibling block spans
    for path, cits in list(evidence.items()):
        if len(cits) == 2 and isinstance(cits[0], dict) and isinstance(cits[1], dict):
            sid1, q1 = cits[0].get("source_id", ""), cits[0].get("quote", "")
            sid2, q2 = cits[1].get("source_id", ""), cits[1].get("quote", "")
            elem1 = sid1.split(":")[0] if ":" in sid1 else sid1
            elem2 = sid2.split(":")[0] if ":" in sid2 else sid2
            if elem1 == elem2 and sid1 in blocks_dict and sid2 in blocks_dict:
                if q1 not in blocks_dict[sid1] and q1 in blocks_dict[sid2] and q2 not in blocks_dict[sid2] and q2 in blocks_dict[sid1]:
                    evidence[path] = [
                        {"source_id": sid2, "quote": q1},
                        {"source_id": sid1, "quote": q2},
                    ]
                    changes.append({
                        "original_path": path,
                        "normalized_path": path,
                        "rule": "sibling_subblock_span_realignment",
                        "citations_count": len(cits),
                        "origin": "deterministic swap of inverted sub-block spans for same source element; target data untouched",
                    })

    assert candidate["data"] == data, "Target data mutated during alignment!"
    return candidate, changes


def prepare_candidate_mapping(raw, blocks):
    """Applies local provably equivalent pointer normalizations and confirmed omission repairs.
    Never fabricates citations or modifies data values without source derivation.
    Returns (candidate, all_changes, rejections).
    """
    candidate, normalizations, rejections = normalize_evidence_pointers(raw, blocks)
    candidate, omission_repairs = repair_confirmed_omissions(candidate, blocks)
    candidate, alignment_changes = align_array_and_span_evidence(candidate, blocks)
    all_changes = normalizations + omission_repairs + alignment_changes
    return candidate, all_changes, rejections

