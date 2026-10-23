"""Validate serialized corpus outputs and publish a final view without altering checkpoints."""
import csv
import hashlib
import json
import sys
from pathlib import Path
from collections import Counter
from local_api.schemas.sections import SectionResponse
from local_api.schemas.subschemas import SectionSchema
from local_api.services.source_validation import validate_result
from local_api.services.subschema_validation import validate_hierarchy

OUT=Path(__file__).parent
ROOT=OUT.resolve().parents[1]
manifest=json.loads((OUT/'manifest.json').read_text())
code=hashlib.sha256()
for path in sorted((ROOT/'local_api').rglob('*.py'))+sorted((ROOT/'local_api/data').glob('*.json'))+[ROOT/'scripts/map_resume_corpus.py',ROOT/'scripts/batch_check_resumes.py']:
    code.update(str(path.relative_to(ROOT)).encode());code.update(path.read_bytes())
assert code.hexdigest()==manifest['code_sha256']
rows=json.loads((OUT/'per-resume.json').read_text())
assert len(rows)==len(manifest['inventory'])
assert len({r['file'] for r in rows})==len(rows)
repairs_path=OUT/'doc-repairs.json'
if repairs_path.exists():
    repairs={r['file']:r for r in json.loads(repairs_path.read_text()) if r['status']=='mapped_needs_review'}
    rows=[repairs.get(r['file'],r) for r in rows]
# Retain the failed original attempt in results.jsonl/per-resume.json. The final
# view may point to a transparently normalized derivative, with original binding.
prep_path=OUT/'wrapped-pdf-preparation.json'
if prep_path.exists():
    prep=json.loads(prep_path.read_text()); recovered=OUT/'wrapped-pdf-local-recheck'
    if (recovered/'schema.json').exists():
        d=json.loads((recovered/'schema.json').read_text())
        target=next(r for r in rows if r['file']==prep['file'])
        target.update(status='mapped_needs_review', input_mode='normalized_pdf_same_local_pipeline',
            original_attempt_error_type=target.get('error_type'),
            original_attempt_extraction_status=target.get('extraction_status'),
            extraction_status='processed_after_normalization',
            source_preparation='wrapped-pdf-preparation.json',
            normalized_source_sha256=prep['normalized_sha256'],
            mapping_artifact=str((recovered/'schema.json').relative_to(OUT)),
            source_artifact=None,
            recovered_extraction=str((recovered/'extraction.json').relative_to(OUT)),
            recovered_sections=str((recovered/'sections.json').relative_to(OUT)),
            populated_items=sum(len(a['items']) for s in d['section_schemas'] for r in s['records'] for a in r['attributes']),
            unresolved_attributes=sum(not a['items'] for s in d['section_schemas'] for r in s['records'] for a in r['attributes']),
            unresolved_source_blocks=len(d['meta']['needs_review']),
            candidate_resume=d['meta']['document_scope']['candidate_resume'],citation_validation_passed=True)
        target.pop('error_type',None);target.pop('error_status',None)

for row in rows:
    if row['status']=='failed' and row['extension']=='.doc' and row.get('error_status')==503:
        row['status']='pending_converter'
        row['pending_reason']='LibreOffice missing; user explicitly requested leaving DOC files pending.'

validation=[];source_changes=[];saved_changes=[]
for index,row in enumerate(rows,1):
    actual=hashlib.sha256(Path(row['source']).read_bytes()).hexdigest()
    if actual!=row['sha256']:source_changes.append(row['file'])
    if row.get('reused_artifact'):
        if hashlib.sha256(Path(row['reused_artifact']).read_bytes()).hexdigest()!=row['reused_artifact_sha256']:
            saved_changes.append(row['reused_artifact'])
    if row['status']=='mapped_needs_review':
        mapped=json.loads((OUT/row['mapping_artifact']).read_text())
        if row.get('source_artifact'):
            source=json.loads((OUT/row['source_artifact']).read_text())
            extraction=source['extraction'];sections=source.get('sections',source.get('local_sections'))
            assert source['file']==row['file']
        else:
            extraction=json.loads((OUT/row['recovered_extraction']).read_text())
            sections=json.loads((OUT/row['recovered_sections']).read_text())
        from local_api.schemas.extraction import ExtractedElement
        elements=[ExtractedElement.model_validate(e) for e in extraction['elements']]
        sections=SectionResponse.model_validate(sections)
        assert not validate_result(elements,sections)
        validate_hierarchy(mapped['section_schemas'],sections)
        validation.append({'file':row['file'],'source_intervals_valid':True,'hierarchy_and_quotes_valid':True})
    if index%100==0:print('Validated',index,flush=True)
assert not source_changes and not saved_changes
summary={'files_discovered':len(rows),'unique_source_hashes':manifest['unique_hashes'],
    'files_attempted':len(rows),'formats':dict(Counter(r['extension'] for r in rows)),
    'statuses':dict(Counter(r['status'] for r in rows)),
    'input_modes':dict(Counter(r['input_mode'] for r in rows)),
    'provider_calls':0,'provider_tokens':0,
    'populated_items':sum(r.get('populated_items',0) for r in rows if r['status']=='mapped_needs_review'),
    'unresolved_attributes':sum(r.get('unresolved_attributes',0) for r in rows if r['status']=='mapped_needs_review'),
    'serialized_mapping_validations_passed':len(validation),
    'pipeline_code_matches_manifest':True,
    'source_files_changed':source_changes,'reused_artifacts_changed':saved_changes,
    'semantic_accuracy_measured':False,'human_verified':False}
for name,data in [('final-per-resume.json',rows),('final-summary.json',summary),
                  ('final-failures.json',[r for r in rows if r['status']!='mapped_needs_review']),('validation.json',validation)]:
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2))
fields=['file','status','input_mode','extension','sha256','populated_items','unresolved_attributes','unresolved_source_blocks','candidate_resume','mapping_artifact','error_type','error_status']
for name in ['per-resume.csv','review-queue.csv']:
    with (OUT/name).open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader()
        for row in sorted(rows,key=lambda r:(r['status']=='mapped_needs_review',-r.get('unresolved_attributes',0),r['file'])):writer.writerow(row)
failed=[r for r in rows if r['status']!='mapped_needs_review']
lines='\n'.join(f"| {r['file']} | {r.get('error_type')} | {r.get('error_status')} |" for r in failed)
report=f'''# Full-folder hierarchical schema mapping

**All {len(rows):,} supported files were attempted locally.** Hierarchy outputs: **{len(validation):,}**. Remaining pending/unmapped files: **{len(failed)}**. No DeepSeek requests or provider tokens were used.

Source folder: `{manifest['source_directory']}`. Formats: {summary['formats']}. There are **{manifest['unique_hashes']:,} distinct source hashes**; duplicates were still represented as separate files as requested.

## Processing

{summary['input_modes']}

The saved blocks for 1,053 files were reused only when their source-file hash matched and current source/hierarchy validation passed. The other files went through the existing local extraction, Sentence-BERT/K-means, recovery and schema stages. Reused blocks retain their original segmentation decisions; this is not a fresh segmentation rerun of those files. The corpus checkpoint runner and immutable manifest are in `scripts/map_resume_corpus.py` and `manifest.json`.

One PDF, `EWM_Resume_Shailesh.pdf`, initially failed content-type detection because its PDF header follows a 137-byte wrapper. A derivative in `normalized-inputs/` passed through the unchanged local pipeline. All three pages' independently parsed text matched before/after prefix removal. Original/derivative hashes and preparation details are in `wrapped-pdf-preparation.json`; original-attempt failure evidence remains in the raw checkpoint. Final results include the recovered mapping explicitly.

## Verification and limits

All **{len(validation):,} serialized mapping outputs** were reloaded and passed exact extracted-source interval checks, deterministic hierarchy validation, record-local source evidence checks and exact-quote validation. Populated child items: **{summary['populated_items']:,}**. Unresolved attribute slots: **{summary['unresolved_attributes']:,}**. The latter count is not a count of facts missing from the original documents.

All **{len(rows):,} original file hashes** were checked again: changed files **0**. Reused saved-artifact hashes were checked again: changed artifacts **0**. Existing extraction, detection and schema implementation code was not modified for this bulk run. Only a separate offline batch runner and its regression tests were added. Runner regression tests: **2 passed** (saved-block reuse/idempotent resume, changed-source rejection).

**These are provisional mappings requiring review.** Exact citations and schema validity do not establish correct names, associations, field completeness or original-PDF word accuracy. The local mapper's known completeness limitations remain. This run contains no new LLM verification and is not a readiness/accuracy certification. Non-resume material may be present; document-scope diagnostics are retained per file.

## Pending/unmapped files

| File | Error | HTTP-style status |
|---|---|---:|
{lines}

Legacy Word failures with status 503 require the missing LibreOffice `soffice` converter. **The user explicitly requested leaving these six DOC files pending.** They have no completed hierarchy output. No converter was installed and originals were not converted in place. They can be processed later if the user chooses to supply the dependency or supported copies.

## Results to use

- `final-summary.json`: final counts, including the recovered PDF.
- `final-per-resume.json` and `per-resume.csv`: every file, final status and mapping path.
- `review-queue.csv`: failures first, followed by unresolved-field counts.
- `final-failures.json`: outstanding files.
- `documents/<id>/mapping.json`: each ordinary mapped output; the recovered PDF uses `wrapped-pdf-local-recheck/schema.json`.
- `validation.json`: post-serialization source/hierarchy validation outcomes.
- `results.jsonl`, `per-resume.json`, `summary.json`: original checkpoint outcomes, retaining the PDF's initial failure.

To query one result, load its `section_schemas` using `SectionSchema.model_validate`, validate it against the paired `source.json` sections, then call `query_subschemas(hierarchy, 'education.institution')` or another predefined field path. Keep record IDs when joining employer/title or degree/institution results. The live source-bound query endpoint remains documented in `docs/SCHEMA_MAPPING_API.md`.
'''
(OUT/'report.md').write_text(report)
print(json.dumps(summary),flush=True)
