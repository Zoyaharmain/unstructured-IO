"""Independent source-bound metrics; predictions never define reference spans."""
from collections import Counter
from hashlib import sha256
import json
import re


def source_hash(elements):
    return sha256(json.dumps([e.model_dump() for e in elements], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def reference_spans(elements, truth):
    """Validate arbitrary human intervals, independent of parser segmentation."""
    labels = truth.get('spans')
    if not isinstance(labels, list) or not labels:
        raise ValueError('Invalid truth spans')
    seen, coverage, result = set(), [set() for e in elements], []
    from local_api.services.resume_sections import ANCHORS
    for label in labels:
        if not isinstance(label, dict):
            raise ValueError('Invalid truth span')
        sid = label.get('source_id')
        match = re.fullmatch(r'e(\d+):(\d+):(\d+)', sid or '')
        if not match or sid in seen:
            raise ValueError('Invalid or duplicate reference source ID')
        index, start, end = map(int, match.groups())
        if not 0 <= index < len(elements) or not 0 <= start < end <= len(elements[index].text):
            raise ValueError('Reference interval outside immutable source')
        if coverage[index] & set(range(start, end)):
            raise ValueError('Overlapping reference spans')
        coverage[index].update(range(start, end))
        text = elements[index].text[start:end]
        if 'text' in label and label['text'] != text:
            raise ValueError('Reference text changed')
        if label.get('section') not in set(ANCHORS) | {'ignore'}:
            raise ValueError('Every reference requires a canonical section or ignore')
        seen.add(sid)
        result.append((label, index, start, end))
    if any(any(not c.isspace() and i not in covered for i,c in enumerate(e.text))
           for e,covered in zip(elements,coverage)):
        raise ValueError('Reference must cover every non-whitespace source character')
    by_id = {label['source_id']:label for label,_,_,_ in result}
    for label,_,_,_ in result:
        anchor = label.get('record_anchor')
        if anchor is not None and (anchor not in by_id or by_id[anchor].get('record_anchor') != anchor
                                   or by_id[anchor]['section'] != label['section']):
            raise ValueError('Invalid reference record anchor')
        if label.get('kind') in {'responsibilities','achievements'} and anchor is None:
            raise ValueError('Scored responsibilities require independently established role ownership')
    return result


def evaluate_ownership(elements, state, truth=None):
    spans = {s.source_id:s for s in state.spans}
    meaningful = {sid for sid,s in spans.items() if s.text.strip() and state.owners[sid].status != 'non_content_artifact'}
    unresolved = sum(state.owners[s].status == 'needs_review' for s in meaningful)
    result = {'source_digest':state.digest, 'meaningful_spans':len(meaningful),
              'unresolved_spans':unresolved,
              'unresolved_span_rate':unresolved/len(meaningful) if meaningful else None,
              'section_f1':None,'record_boundary_f1':None,'responsibility_ownership_accuracy':None,
              'cross_record_leakage':None,'scored_responsibilities':0,
              'accuracy_status':'not_independently_labeled'}
    if truth is None:
        return result
    from local_api.services.evaluation_datasets import validate_annotation
    validate_annotation(truth, source_hash(elements))
    labels = reference_spans(elements, truth)
    predicted_records, positions = {}, {s.source_id:(s.element,s.start) for s in state.spans}
    actual = [[None]*len(e.text) for e in elements]
    for span in state.spans:
        owner = state.owners[span.source_id]
        if owner.record is not None:
            predicted_records.setdefault(owner.record, positions[span.source_id])
        for i in range(span.start, span.end):
            actual[span.element][i] = owner
    anchors = {label['record_anchor'] for label,_,_,_ in labels if label.get('record_anchor') is not None}
    reference_positions = {label['source_id']:(index,start) for label,index,start,_ in labels}
    expected_by_id = {label['source_id']:label for label,_,_,_ in labels}
    wanted_boundaries = {(expected_by_id[a]['section'],reference_positions[a]) for a in anchors}
    got_boundaries = {(owner.section,predicted_records[owner.record]) for owner in state.owners.values() if owner.record is not None}
    tp = len(wanted_boundaries & got_boundaries)
    result['record_boundary_f1'] = 2*tp/(len(wanted_boundaries)+len(got_boundaries)) if wanted_boundaries or got_boundaries else None
    confusion, units = Counter(), {}
    for label,index,start,end in labels:
        if label['section'] == 'ignore':
            continue
        owners = [actual[index][offset] for offset in range(start,end) if not elements[index].text[offset].isspace()]
        for owner in owners:
            confusion[label['section'], owner.section if owner else None] += 1
        if label.get('kind') not in {'responsibilities','achievements'} or not owners:
            continue
        wanted = reference_positions[label['record_anchor']]
        unit_id = label.get('unit_id') or label['source_id']
        unit = units.setdefault(unit_id, {'correct':True, 'leaked':False, 'wanted':wanted})
        if unit['wanted'] != wanted:
            raise ValueError('A reference responsibility unit cannot have multiple primary roles')
        unit['correct'] &= all(owner is not None and predicted_records.get(owner.record) == wanted
                             and owner.section == label['section'] and owner.status != 'needs_review' for owner in owners)
        unit['leaked'] |= any(owner is not None and owner.record is not None
                             and (predicted_records.get(owner.record) != wanted or owner.section != label['section']) for owner in owners)
    classes = {c for pair in confusion for c in pair if c is not None}
    f1s = []
    for category in classes:
        tp = confusion[category,category]
        fp = sum(n for (a,b),n in confusion.items() if b == category and a != category)
        fn = sum(n for (a,b),n in confusion.items() if a == category and a != b)
        f1s.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0)
    duties = len(units)
    correct, leaked = sum(u['correct'] for u in units.values()), sum(u['leaked'] for u in units.values())
    result.update(section_f1=sum(f1s)/len(f1s) if f1s else None,
                  responsibility_ownership_accuracy=correct/duties if duties else None,
                  cross_record_leakage=leaked/duties if duties else None,
                  scored_responsibilities=duties, accuracy_status='independently_labeled',
                  section_metric='macro F1 over non-whitespace character assignments; only reference ignore spans excluded',
                  boundary_metric='exact section and first-primary-source-start F1; independent of span end offsets',
                  leakage_metric='fraction of labeled duties with any text assigned to a wrong primary record; abstentions are errors, not leaks')
    return result
