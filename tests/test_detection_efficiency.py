"""Avoid repeated encoder work without reusing source ownership or classification."""
import numpy as np
from local_api.services.resume_sections import SectionEngine


def test_encoder_cache_encodes_only_distinct_missing_text_and_stays_bounded():
    class Encoder:
        def __init__(self): self.calls=[]
        def encode(self,texts,**kwargs):
            self.calls.append(texts)
            return np.asarray([[len(t),1.0] for t in texts])
    engine=SectionEngine.__new__(SectionEngine);engine.encoder=Encoder()
    first=engine.encode_texts(['Alpha','Beta','Alpha'])
    second=engine.encode_texts(['Beta','New','Alpha'])
    assert engine.encoder.calls == [['Alpha','Beta'],['New']]
    assert np.array_equal(first[0],second[2])
    engine.encode_texts([str(i) for i in range(2100)])
    assert len(engine._embedding_cache)==2048
    assert all(isinstance(k,bytes) for k in engine._embedding_cache)
