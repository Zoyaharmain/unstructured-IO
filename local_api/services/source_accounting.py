"""Exact source-span outcomes, independently of provider completion or confidence."""
import re


def artifact_reason(element,block):
    if not block.text.strip():return 'Whitespace retained in source inventory'
    if element.type=='PageBreak':return 'Explicit page separator'
    if re.fullmatch(r'[\s•▪●○◦\uf0b7]+',block.text):return 'Standalone list markers retained in source inventory'
    compact=re.sub(r'\s+','',block.text).casefold()
    page_pattern=re.fullmatch(r'(?:page)?\d+(?:(?:of|/)\d+)?|\d+\|page',compact)
    if not page_pattern:return None
    # A graduation year at the bottom of a page is not a page number.
    if re.fullmatch(r'(?:19|20)\d{2}',compact):return None
    hints=[h for h in element.metadata.get('pdf_source_lines',[]) if len(h.get('bbox',[]))==4 and
           min(block.end,h.get('end',0))>max(block.start,h.get('start',0))]
    located=bool(hints and all(h['bbox'][1]>.88 for h in hints))
    if element.type=='Footer' or located:return 'Source-supported page-number footer retained'
    return None


def account_source(elements,result):
    from local_api.services.llm_section_review import source_ledger,assert_coverage
    ledger=source_ledger(result)
    assert_coverage(elements,ledger)
    outcomes=[]
    for block,category in ledger:
        element=elements[block.source_element_index]
        artifact=artifact_reason(element,block)
        outcome='non_content_artifact' if artifact else 'assigned' if category else 'human_review'
        outcomes.append({'source_id':f'e{block.source_element_index}:{block.start}:{block.end}',
                         'source_element_index':block.source_element_index,'start':block.start,'end':block.end,
                         'section':category,'outcome':outcome,'reason':artifact or block.reason})
    return {'all_source_text_preserved':True,'total_spans':len(outcomes),
            'assigned_meaningful_spans':sum(x['outcome']=='assigned' for x in outcomes),
            'unresolved_meaningful_spans':sum(x['outcome']=='human_review' for x in outcomes),
            'non_content_artifacts':sum(x['outcome']=='non_content_artifact' for x in outcomes),
            'duplicates_excluded':0,'all_meaningful_text_assigned':not any(x['outcome']=='human_review' for x in outcomes),
            'semantic_correctness_verified':False,'outcomes':outcomes}
