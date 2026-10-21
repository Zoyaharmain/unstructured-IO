"""Separate structural evidence from unmeasured semantic/source accuracy."""
import re
from local_api.services.review_resolution import document_scope
from local_api.services.source_accounting import account_source


def assess_quality(elements,result):
    accounting=account_source(elements,result)
    relationship={};errors=[]
    for section in result.sections:
        if section.category not in {'experience','education'}:continue
        owned=set();ids=set();unresolved=[]
        for entry in section.entries:
            if entry.entry_id in ids:errors.append('duplicate_entry_id')
            ids.add(entry.entry_id)
            for index in entry.block_indices:
                if type(index)!=int or not 0<=index<len(section.blocks):errors.append('invalid_entry_reference');continue
                if index in owned:errors.append('overlapping_entry_ownership')
                owned.add(index)
            for indices in entry.fields.values():
                if any(index not in entry.block_indices for index in indices):errors.append('field_references_another_entry')
            if entry.review_reasons:unresolved.append({'entry_id':entry.entry_id,'reasons':entry.review_reasons})
        unlinked=[i for i,b in enumerate(section.blocks) if i not in owned and re.search(r'[A-Za-z0-9]',b.text) and b.assignment not in {'section_heading','structural_heading'}]
        relationship[section.category]={'verification':'unverified','proposed_entries':len(section.entries),'entries_needing_review':unresolved,'unlinked_block_indices':unlinked}
    scope=document_scope(elements);review=result.metadata.get('llm_review',{})
    return {
        'source_coverage':{'extracted_intervals_complete':True,'spans':accounting['total_spans'],'meaningful_unassigned':accounting['unresolved_meaningful_spans']},
        'assignment_correctness':{'verification':'unverified','ground_truth_used':False},
        'relationship_correctness':{'verification':'unverified','sections':relationship,'integrity_errors':sorted(set(errors))},
        'duplication':{'overlapping_source_intervals':0,'same_region_duplicates_retained_in_provenance':sum(len(e.metadata.get('pdf_same_region_duplicates',[])) for e in elements),'repeated_text_is_not_automatically_an_error':True},
        'source_fidelity':{'current_extracted_text_preserved':True,'original_pdf_word_accuracy':'unverified','ocr_reference_needed':any(e.metadata.get('text_as_html') is None and e.metadata.get('ocr_verification_required') for e in elements),'glyph_replacements':sum(len(e.metadata.get('pdf_glyph_recovery',{}).get('replacements',[])) for e in elements),'damaged_glyph_elements':sum('\x00' in e.text or '\ufffd' in e.text for e in elements)},
        'review_validity':{'provider_status':review.get('status','not_attempted'),'structurally_valid':review.get('status')=='complete','validation_failures':review.get('validation_failures',[])},
        'document_scope':scope,
        'candidate_meaningful_unassigned':None if scope['candidate_resume'] is False else accounting['unresolved_meaningful_spans'],
        'non_resume_pending_text_is_candidate_extraction_failure':False,
    }
