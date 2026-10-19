"""Exact source-span outcomes, independently of provider completion or confidence."""
import re


def account_source(elements,result):
    from local_api.services.llm_section_review import source_ledger,assert_coverage
    ledger=source_ledger(result)
    assert_coverage(elements,ledger)
    outcomes=[]
    for block,category in ledger:
        element=elements[block.source_element_index]
        artifact=None
        if not block.text.strip():artifact='Whitespace retained in source inventory'
        elif element.type=='PageBreak':artifact='Explicit page separator'
        elif element.type=='Footer' and re.fullmatch(r'\s*(?:page\s*)?\d+(?:\s*(?:of|/)\s*\d+)?\s*',block.text,re.I):artifact='Explicit page-number footer'
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
