import hashlib
import json
from pathlib import Path
import pytest
from local_api.services.evaluation_datasets import inventory, audit_usage, make_splits, validate_splits, validate_annotation
from scripts.annotate_resume_sources import blind_template
from local_api.schemas.extraction import ExtractedElement
from local_api.services.ownership_evaluation import reference_spans


def test_audit_detects_renamed_source_copies_and_literal_references(tmp_path):
    corpus=tmp_path/'corpus';corpus.mkdir()
    (corpus/'New.pdf').write_bytes(b'document-a')
    (corpus/'Copy.pdf').write_bytes(b'document-a')
    (corpus/'Other.docx').write_bytes(b'document-b')
    history=tmp_path/'ground_truth';history.mkdir()
    (history/'original.pdf').write_bytes(b'document-a')
    (history/'manifest.json').write_text(json.dumps({'filename':'Other.docx'}))
    docs=inventory(corpus)
    assert len(docs)==2
    audited=audit_usage(docs,[history])
    assert all(d['historical_evidence'] for d in audited)
    splits=make_splits(audited)
    assert len(splits['development'])==2
    assert not splits['held_out_test'] and not splits['validation']
    assert validate_splits(splits)


def test_reservations_are_disjoint_and_do_not_claim_independence():
    docs=[{'sha256':hashlib.sha256(str(i).encode()).hexdigest(),'historical_evidence':[]} for i in range(100)]
    splits=make_splits(docs)
    assert all(splits.values()) and validate_splits(splits)
    assert all(d['independence_status']=='requires_independence_attestation' for values in splits.values() for d in values)
    contaminated={**splits,'held_out_test':splits['held_out_test']+[splits['development'][0]]}
    with pytest.raises(ValueError):validate_splits(contaminated)
    docs[0]['historical_evidence']=[{'use':'development_reference'}]
    assert docs[0]['sha256'] in {d['sha256'] for d in make_splits(docs)['development']}


def test_human_verification_cannot_be_inferred_from_llm_label_or_flag():
    annotation={'source_digest':'digest','human_verified':True,'annotation_origin':'llm',
        'review':{'method':'independent_human','reviewer_id':'a','adjudicator_id':'b',
                  'saw_parser_predictions':False,'independence_attested':True}}
    with pytest.raises(ValueError):validate_annotation(annotation,'digest',held_out=True)
    annotation['annotation_origin']='independent_human'
    assert validate_annotation(annotation,'digest',held_out=True)
    annotation['review']['adjudicator_id']='a'
    with pytest.raises(ValueError):validate_annotation(annotation,'digest',held_out=True)
    annotation['review']['adjudicator_id']='b'
    annotation['review']['saw_parser_predictions']=True
    with pytest.raises(ValueError):validate_annotation(annotation,'digest')


def test_blind_export_has_no_predictions_and_preserves_exact_offsets():
    elements=[ExtractedElement(type='Title',text='WORK\nPython\n',page_number=1,metadata={})]
    template=blind_template(elements)
    assert template['annotation_origin']=='unlabeled_template' and not template['human_verified']
    assert all(row['section'] is None and row['record_anchor'] is None for row in template['spans'])
    assert ''.join(row['text'] for row in template['spans'])==elements[0].text
    with pytest.raises(ValueError):validate_annotation(template,template['source_digest'])
    for row in template['spans']:row['section']='skills'
    assert reference_spans(elements,template)
    template['spans'][0]['text']='Changed'
    with pytest.raises(ValueError):reference_spans(elements,template)
