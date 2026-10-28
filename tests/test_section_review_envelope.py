import json
import pytest
from local_api.services.review_chunking import section_decisions, ChunkError


def chunk():
    return {'targets':[{'id':'e0:0:4','text':'test','allowed_split_offsets':[0,4]}]}


def test_chunk_and_document_accept_the_same_json_object_envelope():
    reply={'type':'json_object','assignments':[['e0:0:4','summary']]}
    assert section_decisions(chunk(),json.dumps(reply),{'summary':{}})=={'e0:0:4':[(0,4,'summary')]}


def test_envelope_fix_does_not_accept_foreign_sources_or_missing_coverage():
    with pytest.raises(ChunkError):
        section_decisions(chunk(),json.dumps({'assignments':[['other','summary']]}),{'summary':{}})
    from local_api.services.llm_section_review import ReviewError
    with pytest.raises(ReviewError):
        section_decisions(chunk(),json.dumps({'type':'json_object','assignments':[]}),{'summary':{}})
