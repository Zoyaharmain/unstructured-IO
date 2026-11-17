"""Identity evidence is separate from immutable employer source occurrences."""
import re


def normalize(text):
    return re.sub(r'\W+','',text.casefold())


def identity(state, record):
    from local_api.services.record_subfields import employment_header_fields, RANGE
    rows=[s for s in state.spans if state.owners[s.source_id].record==record]
    employers=[s for s in rows if 'employer' in state.owners[s.source_id].fields]
    if not employers:
        return None
    headers=[employment_header_fields(s.text) for s in employers]
    companies={normalize(h['company']) for h in headers if h.get('company')}
    if len(companies)>1:
        return None
    header=employment_header_fields(' '.join(s.text for s in employers))
    role=header.get('role') or next((employment_header_fields(s.text).get('role') for s in rows
                                   if employment_header_fields(s.text).get('role')),None)
    role=role or next((s.text for s in rows if 'title' in state.owners[s.source_id].fields),None)
    identified=[h for h in headers if h.get('company')]
    company=(identified[0]['company'] if len(identified)>1 else header.get('company')) or ' '.join(s.text for s in employers)
    dates={normalize(m.group()) for s in rows if 'dates' in state.owners[s.source_id].fields
           for m in RANGE.finditer(s.text)}
    if not company or not role or len(dates)!=1:
        return None
    return normalize(company),normalize(role),next(iter(dates))


def duplicate_groups(state):
    grouped={}
    for rid in dict.fromkeys(o.record for o in state.owners.values() if o.record and o.section=='experience'):
        key=identity(state,rid)
        if key:
            grouped.setdefault(key,[]).append(rid)
    return [records for records in grouped.values() if len(records)>1]


def duplicate_issues(state):
    return [{'kind':'duplicate','section':'experience','record_ids':records,
             'source_ids':[s.source_id for s in state.spans if state.owners[s.source_id].record in records],
             'reason':'Repeated employer, role and dates; separate source occurrences retained pending reconciliation.'}
            for records in duplicate_groups(state)]


def repeated_occurrence_operations(state):
    """Equal identity alone is uncertain; require a complete repeated record.

    One complete normalized source record must occur inside its counterpart.
    Every original span survives, including supplemental detail in an expansion.
    """
    operations=[]
    for records in duplicate_groups(state):
        signatures={r:normalize(' '.join(s.text for s in state.spans if state.owners[s.source_id].record==r)) for r in records}
        eligible=[r for r in records if r not in state.record_parents and r not in state.record_parents.values() and r not in state.groups]
        if len(eligible)<2:
            continue
        largest=max(eligible,key=lambda r:len(signatures[r]))
        copies=[r for r in eligible if signatures[r] and signatures[r] in signatures[largest]]
        if len(copies)>1:
            operations.append({'op':'merge','records':copies})
    return operations
