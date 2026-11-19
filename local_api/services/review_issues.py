"""One view of classification, relationship and execution uncertainty."""
def collect_review_issues(result):
    issues = [{'kind':'section', 'source_ids':[f'e{b.source_element_index}:{b.start}:{b.end}'],
               'reason':b.reason} for b in result.needs_review if b.text.strip()]
    for section in result.sections:
        for entry in section.entries:
            if entry.relationship_status == 'needs_review' or entry.review_reasons:
                issues.append({'kind':'record','section':section.category,'record_id':entry.entry_id,
                    'source_ids':[f'e{section.blocks[i].source_element_index}:{section.blocks[i].start}:{section.blocks[i].end}' for i in entry.block_indices],
                    'reasons':entry.review_reasons or ['record_relationship_unresolved']})
        for b in section.blocks:
            if b.assignment == 'ownership_needs_review':
                issues.append({'kind':'boundary' if b.boundary_source_id else 'ownership',
                    'section':section.category,'source_ids':[f'e{b.source_element_index}:{b.start}:{b.end}'],
                    'reason':b.reason})
    for stage in ['llm_review','structure_review','field_review']:
        status=result.metadata.get(stage,{})
        if status.get('status') in {'rejected','failed','partial','budget_exceeded','not_configured'} or status.get('execution_status') == 'partial':
            issues.append({'kind':'review_execution','stage':stage,'status':status['status'],
                           'reason':status.get('validation_reason',status.get('message',status.get('error_code'))) or
                                    'Some correction transactions require review; independent accepted repairs were retained.'})
    issues.extend(result.metadata.get('duplicate_record_issues',[]))
    issues.extend(result.metadata.get('field_review_issues',[]))
    audit = result.metadata.get('schema_audit', {})
    for finding in audit.get('findings', []) + audit.get('partial_findings', []):
        issues.append({'kind': 'schema_audit', 'stage': 'schema_audit',
                       'field': finding['field'], 'source_ids': finding['source_ids'],
                       'reason': finding['issue']})
    if audit.get('status') not in {None, 'complete', 'not_requested'}:
        issues.append({'kind': 'review_execution', 'stage': 'schema_audit',
                       'status': audit['status'], 'source_ids': [],
                       'reason': 'Schema audit did not complete; output requires review.'})
    return issues
