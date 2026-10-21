"""Offline replay of saved batch outputs; never calls models or provider APIs.

Writes only to a new output directory. Recovered inventories invalidate saved
span IDs, so they are not combined with old classifications. No gold promotion.
"""
import argparse,csv,hashlib,json,socket,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionResponse
from local_api.services.review_resolution import document_scope
from local_api.services.resume_structure import entry_groups,word_safe_cut
from local_api.services.pdf_source_recovery import recover_pdf_source
from local_api.services.pdf_section_layout import annotate_pdf_lines
from local_api.services.llm_section_review import assert_coverage,source_ledger,assignment_feedback


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run=args.run.resolve();out=args.output.resolve()
    if out.exists():parser.error('Use a new output directory to preserve previous results')
    if out==run or run in out.parents:parser.error('Output must be outside the original run')
    def blocked(*a,**kw):raise RuntimeError('This audit forbids network access')
    socket.socket.connect=blocked;socket.create_connection=blocked
    before={str(p):digest(p) for p in run.rglob('*') if p.is_file()}
    out.mkdir(parents=True);(out/'documents').mkdir()
    manifest=json.loads((run/'manifest.json').read_text());selected={r['file']:r for r in manifest['selected']}
    rows=[];details=[];counts=Counter()
    for file in sorted((run/'local/documents').glob('*.json')):
        local=json.loads(file.read_text());name=local['file'];source=run/'selected-pdfs'/name
        if digest(source)!=selected[name]['sha256']:raise RuntimeError('Source hash mismatch: '+name)
        raw=local['extraction']['elements']
        # Refresh geometry in memory only; repeated source words previously
        # matched another identical line elsewhere on the page.
        for e in raw:e.setdefault('metadata',{}).pop('pdf_source_lines',None)
        annotate_pdf_lines(source.read_bytes(),raw)
        elements=[ExtractedElement.model_validate(e) for e in raw]
        scope=document_scope(elements)
        recovered,audit=recover_pdf_source(source.read_bytes(),raw)
        saved=json.loads((run/'deepseek/documents'/file.name).read_text())
        response=SectionResponse.model_validate(saved['reviewed_sections'])
        assert_coverage(elements,source_ledger(response))
        grouping=[]
        for section in response.sections:
            if section.category not in {'experience','education'}:continue
            rebuilt=entry_groups(section.blocks,section.category,elements)
            original=[e.model_dump() for e in section.entries]
            changed_membership=[e['block_indices'] for e in original]!=[e['block_indices'] for e in rebuilt]
            grouping.append({'category':section.category,'before':original,'after':rebuilt,'changed':changed_membership,
                             'block_source_ids':[f'e{b.source_element_index}:{b.start}:{b.end}' for b in section.blocks]})
        word_splits=[]
        ledger=source_ledger(response)
        for (left,_),(right,_) in zip(ledger,ledger[1:]):
            if left.source_element_index==right.source_element_index and left.end==right.start:
                text=elements[left.source_element_index].text;cut=left.end
                if word_safe_cut(text,cut)!=cut:word_splits.append({'element':left.source_element_index,'cut':cut,'context':text[max(0,cut-20):cut+20]})
        removed=sum(e['action']=='collapse_exact_same_region_duplicate' for e in audit['events'])
        added=sum(e['action']=='recover_pdf_character_line' for e in audit['events'])
        counts['recovered_lines']+=added;counts['same_region_duplicates']+=removed
        counts['out_of_scope' if scope['candidate_resume'] is False else 'candidate_unconfirmed']+=1
        counts['grouping_changed_documents']+=any(g['changed'] for g in grouping)
        detail={'file':name,'source_sha256':digest(source),'scope':scope,'source_recovery':audit,'recovered_elements':recovered,
                'relationship_replay':grouping,'saved_word_splits':word_splits,'geometry_refreshed_from_original_pdf':True,'fresh_model_or_provider_run':False,'independently_verified':False}
        if name=='Keerthi_SAPresume.pdf':
            provider=json.loads((run/'deepseek/provider-decisions'/file.name).read_text())
            local_response=SectionResponse.model_validate(local['sections']);source_spans=source_ledger(local_response)
            lengths={f'u{i}':len(b.text) for i,(b,_) in enumerate(source_spans)}
            detail['rejected_provider_feedback']=[json.loads(assignment_feedback(p['content'],lengths)) for p in provider]
        (out/'documents'/file.name).write_text(json.dumps(detail,indent=2)+'\n')
        rows.append({'file':name,'scope':scope['kind'],'candidate_confirmed':False,'exclude_from_candidate_accuracy':scope['candidate_resume'] is False,
                     'recovered_pdf_lines':added,'same_region_duplicates':removed,'ambiguous_source_lines':len(audit['ambiguous_source_lines']),
                     'relationship_groups_changed':sum(g['changed'] for g in grouping),'saved_ordinary_word_splits':len(word_splits),
                     'fresh_block_detection_required':bool(audit['events']),'new_api_calls':0})
        details.append(detail)
    changed=[path for path,value in before.items() if not Path(path).is_file() or digest(Path(path))!=value]
    if changed:raise RuntimeError('Protected files changed')
    with (out/'per-document.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result={'scope_documents':len(rows),'counts':dict(counts),'new_api_calls':0,'fresh_block_detection_run':False,'protected_files_checked':len(before),'protected_files_changed':changed,
            'accuracy_measured':False,'human_approved_gold_created':0,'records':rows}
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    md=['# Offline 50-document repair audit','','Saved results and PDFs remain unchanged. This is a replay/source-recovery audit, not a fresh pipeline run or an accuracy measurement. No API calls were made.','',
        f"Documents: {len(rows)}. Non-resume exclusions: {counts['out_of_scope']}. Remaining candidates requiring confirmation: {counts['candidate_unconfirmed']}.",
        f"Recovered PDF text lines: {counts['recovered_lines']}; collapsed exact same-region duplicates: {counts['same_region_duplicates']}.",
        f"Relationship grouping proposals changed in {counts['grouping_changed_documents']} documents; changed counts do not establish correctness.",'',
        '| File | Scope | PDF lines recovered | Same-region duplicates | Groups changed |', '|---|---|---:|---:|---:|']
    for r in rows:md.append(f"| {r['file']} | {r['scope']} | {r['recovered_pdf_lines']} | {r['same_region_duplicates']} | {r['relationship_groups_changed']} |")
    md+=['','## How to interpret this','',
         'The remaining candidate_or_unknown files are not automatically confirmed candidate resumes. Four exclusions must be reviewed, and replacements need source review before claiming a clean 50-resume test.',
         'Recovered source inventories require fresh extraction/block detection and new compatible provider decisions; existing cached decisions cannot be attached to changed element IDs. Original upstream indices and same-region duplicate contents are preserved in metadata.',
         'Relationship changes attach uniquely source-aligned dates and recognize dated employment headers. They do not verify every employer/title/responsibility or degree/institution/grade association.',
         'The provider validator still rejects missing IDs, out-of-range offsets, overlapping/gapped intervals and invalid categories. Retry feedback now identifies missing IDs and required span lengths; a rejected review is never counted as success.',
         f"Protected original-run files: {len(before)} checked; changed: 0. Gold annotations created: 0."]
    (out/'report.md').write_text('\n\n'.join(md)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))

if __name__=='__main__':main()
