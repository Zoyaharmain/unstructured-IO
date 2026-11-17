"""Explicit live recovery verification using generated ambiguous source only.

Writes source evidence and redacted protocol artifacts, never provider settings.
Run outside ordinary pytest (whose provider calls are disabled by default).
"""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import SectionBlock, SectionEntry, ResumeSection, SectionResponse
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.source_ownership import finalize_ownership, snapshot, validated_ownership_state
    from local_api.services.source_validation import validate_result
    from local_api.services.subschema_validation import validate_hierarchy
    from local_api.services.schema_mapping import map_schema
    from local_api.services.llm_section_review import ReviewSettings, call_deepseek
    from local_api.core.provider_env import load_provider_env
    texts = ['Project: Atlas Platform', 'Built data services.', 'Integrated reporting.',
             'Project: Beacon Portal', 'Built a reporting dashboard.']
    elements = [ExtractedElement(type='NarrativeText', text=t, page_number=1, metadata={'synthetic': True}) for t in texts]
    blocks = [SectionBlock(source_element_index=i, start=0, end=len(t), text=t, page_number=1,
                           assignment='semantic', lane='main', reason='Fictional ambiguous bridge between two records') for i, t in enumerate(texts)]
    # The unlabeled bridge could be a continuation of Atlas or a detached
    # description preceding Beacon. No geometry/style evidence resolves it.
    section = ResumeSection(category='projects', label='Projects', blocks=blocks, text='\n'.join(texts), entries=[
        SectionEntry(entry_id='atlas', block_indices=[0, 1], fields={'title':[0], 'responsibilities':[1]}, lane='main', boundary_reason='explicit title'),
        SectionEntry(entry_id='beacon', block_indices=[3, 4], fields={'title':[3], 'responsibilities':[4]}, lane='main', boundary_reason='explicit title')])
    original = SectionResponse(status='provisional', sections=[section], needs_review=[], metadata={}, warnings=[])
    before = finalize_ownership(elements, original)
    sid = f'e2:0:{len(texts[2])}'
    assert snapshot(elements, before).owners[sid].status == 'needs_review'
    def save(name, value):
        (args.output/name).write_text(json.dumps(value, indent=2, ensure_ascii=False))
    save('elements.json', [e.model_dump() for e in elements])
    save('before.sections.json', before.model_dump())
    load_provider_env(ROOT/'.env')
    settings = ReviewSettings.from_env()
    if not settings.enabled or not settings.api_key:
        save('summary.json', {'live_verification':'not_performed', 'reason':'Provider disabled or credentials unavailable'})
        print('Live verification not performed: provider disabled or credentials unavailable.')
        return
    def transport(config, messages):
        save('llm-request.json', messages)
        content = call_deepseek(config, messages)
        # Provider returns only fictional source-ID decisions; no secrets in
        # this request/response contract.
        (args.output/'llm-response.txt').write_text(content)
        return content
    after = finalize_ownership(elements, before, settings=settings, transport=transport, review='ambiguous')
    save('after.sections.json', after.model_dump())
    save('application-trace.json', after.metadata['structure_review'])
    state = snapshot(elements, after)
    owner = state.owners[sid]
    changed = owner.record is not None and owner.status == 'provisional'
    summary = {'live_verification':'performed', 'review_status':after.metadata['structure_review']['status'],
               'deterministic_abstention':True, 'correction_applied':changed,
               'ownership_integrity_errors':validate_result(elements, after),
               'semantic_ground_truth':'No unique correct parent; source is intentionally ambiguous. Provider choice is provisional.'}
    if changed:
        validated_ownership_state(elements, after)
        mapped = map_schema(SchemaMappingRequest(elements=elements, sections=after))
        validate_hierarchy(mapped.section_schemas, after)
        save('after.schema.json', mapped.model_dump())
        # Check exact primary ownership through both serialized contracts.
        records = next(s for s in mapped.section_schemas if s.category == 'projects').records
        targets = [r for r in records if sid in r.source_ids]
        assert len(targets) == 1
        summary['schema_preserves_correction'] = True
    invalid = finalize_ownership(elements, before, settings=settings,
        transport=lambda *_:'{"operations":[{"op":"review","source_ids":["invented"]}]}', review='ambiguous')
    assert invalid.metadata['structure_review']['status'] == 'rejected' and invalid.sections == before.sections
    summary['invalid_response_rejected_atomically'] = True
    save('invalid-response-trace.json', invalid.metadata['structure_review'])
    save('summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
