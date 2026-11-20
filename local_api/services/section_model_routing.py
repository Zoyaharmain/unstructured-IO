"""Opt-in model tier selection for existing section review calls."""
import hashlib
import json
from dataclasses import replace

from local_api.services.confidence import confidence_for
from local_api.services.decision_trace import emit


def select_section_model(settings, blocks):
    models = settings.section_review_models
    selected = settings
    reason = 'configure all three tier model IDs to enable section routing'
    if all(models):
        from local_api.services.resume_sections import ANCHORS, MODEL_REVISION

        anchor_digest = hashlib.sha256(json.dumps(ANCHORS, sort_keys=True).encode()).hexdigest()
        confidences = [
            confidence_for(block.margin, task=f'section_{block.cluster_space}',
                           model_revision=MODEL_REVISION, anchor_sha256=anchor_digest)['probability']
            for block in blocks
            if block.assignment in {'semantic', 'section_heading', 'needs_review'}
            and block.margin is not None and block.candidate_section
        ]
        reason = 'no complete calibration for the eligible local model candidates'
        if confidences and all(score is not None for score in confidences):
            score = min(confidences)
            index = 0 if score >= settings.high_confidence else 1 if score >= settings.low_confidence else 2
            tier = ('cheap', 'higher', 'strongest')[index]
            selected = replace(settings, model=models[index], routing_tier=tier, routing_probability=score)
            reason = 'lowest calibrated local candidate probability among the eligible targets'
    emit('section_model_routing', model=selected.model, tier=selected.routing_tier or 'configured',
         probability=selected.routing_probability, reason=reason)
    return selected
