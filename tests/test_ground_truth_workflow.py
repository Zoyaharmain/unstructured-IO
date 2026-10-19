"""Unit and integration tests for ground-truth creation, verification, and scaling."""
import json
from pathlib import Path
import pytest

from scripts.evaluate_resume_ground_truth import extraction_hash, score, summarize_scores
from scripts.verify_ground_truth import apply_corrections, validate_gold_invariants

ROOT = Path(__file__).resolve().parents[1]


def test_gold_validation_invariants():
    elements = [{'text': 'John Doe'}, {'text': 'Python, Java'}, {'text': 'Software Engineer'}]
    ext_hash = extraction_hash(elements)

    spans = [
        {'source_element_index': 0, 'start': 0, 'end': len(elements[0]['text']), 'category': 'personal_information'},
        {'source_element_index': 1, 'start': 0, 'end': len(elements[1]['text']), 'category': 'skills'},
        {'source_element_index': 2, 'start': 0, 'end': len(elements[2]['text']), 'category': 'experience'},
    ]

    gold_data = {
        'file': 'test.pdf',
        'extraction_sha256': ext_hash,
        'human_verified': True,
        'spans': spans
    }

    assert validate_gold_invariants(gold_data, elements) is True


def test_gold_validation_rejects_gaps_or_overlaps():
    elements = [{'text': 'John Doe'}]
    ext_hash = extraction_hash(elements)

    # Gap
    gap_spans = [{'source_element_index': 0, 'start': 0, 'end': 4, 'category': 'personal_information'}]
    with pytest.raises(ValueError, match="Incomplete source coverage"):
        validate_gold_invariants({'extraction_sha256': ext_hash, 'spans': gap_spans}, elements)

    # Overlap
    overlap_spans = [
        {'source_element_index': 0, 'start': 0, 'end': 6, 'category': 'personal_information'},
        {'source_element_index': 0, 'start': 4, 'end': 8, 'category': 'personal_information'}
    ]
    with pytest.raises(ValueError, match="Overlapping labels"):
        validate_gold_invariants({'extraction_sha256': ext_hash, 'spans': overlap_spans}, elements)


def test_apply_corrections():
    draft = {
        'spans': [
            {'span_id': 's1', 'category': 'experience', 'uncertainty_flag': True, 'uncertainty_reason': 'test'},
            {'span_id': 's2', 'category': 'skills', 'uncertainty_flag': False, 'uncertainty_reason': None}
        ],
        'records': {'work_experience': [], 'education': []}
    }

    corrections = {
        'span_updates': [
            {'span_id': 's1', 'category': 'summary', 'note': 'opening objective'}
        ]
    }

    updated = apply_corrections(draft, corrections)
    assert updated['spans'][0]['category'] == 'summary'
    assert updated['spans'][0]['uncertainty_flag'] is False
    assert updated['spans'][0]['human_corrected'] is True
    assert len(updated['corrections_applied']) == 1


def test_gold_dataset_integrity():
    gold_dir = ROOT / 'ground_truth/gold'
    assert gold_dir.exists()
    gold_files = list(gold_dir.glob('*.json'))
    # Filter out verification_log.json
    annotation_files = [f for f in gold_files if f.name != 'verification_log.json']
    assert len(annotation_files) == 15

    for gf in annotation_files:
        d = json.load(gf.open())
        assert d['human_verified'] is True
        assert d['status'] == 'gold_approved'
        assert d['uncertainty_summary']['uncertain_spans'] == 0
        assert len(d['spans']) > 0



def test_cached_llm_splits_survive_annotation_projection(tmp_path):
    import hashlib
    from scripts.generate_ground_truth_drafts import generate_draft
    from local_api.schemas.sections import SectionBlock,SectionResponse
    from local_api.schemas.extraction import ExtractedElement,ExtractionResponse,ExtractionMetadata
    from local_api.services.resume_sections import build_sections
    from local_api.services.llm_section_review import source_ledger,assert_coverage
    text='Python SQLBachelor of Science'
    elements=[ExtractedElement(type='NarrativeText',text=text,page_number=1,metadata={})]
    def block(start,end):return SectionBlock(source_element_index=0,start=start,end=end,text=text[start:end],page_number=1,lane='main',assignment='semantic',reason='fixture')
    local=SectionResponse(status='provisional',sections=build_sections({'experience':[block(0,len(text))]},elements),needs_review=[],metadata={},warnings=[])
    reviewed=SectionResponse(status='provisional',sections=build_sections({'skills':[block(0,10)],'education':[block(10,len(text))]},elements),needs_review=[],metadata={'llm_review':{'status':'complete','model':'fixture'}},warnings=[])
    ext=ExtractionResponse(filename='fixture.pdf',file_type='application/pdf',strategy='fast',text=text,elements=elements,metadata=ExtractionMetadata(total_elements=1,page_numbers=[1]))
    artifact=tmp_path/'artifact.json';artifact.write_text(json.dumps({'extraction':ext.model_dump(),'sections':local.model_dump()}))
    cache=tmp_path/'cache';cache.mkdir();(cache/(hashlib.sha256(b'fixture.pdf').hexdigest()[:16]+'.json')).write_text(reviewed.model_dump_json())
    result=generate_draft('fixture.pdf',artifact,cache,cached_only=True)
    assert [(s['text'],s['category']) for s in result['spans']]==[('Python SQL','skills'),('Bachelor of Science','education')]
    assert result['uncertainty_summary']['unassigned_spans']==0
    assert result['uncertainty_summary']['disagreement_spans']==2
    assert result['human_verified'] is False
