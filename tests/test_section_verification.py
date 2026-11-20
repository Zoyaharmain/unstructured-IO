import json

import pytest

from local_api.services.llm_section_review import ReviewSettings, ReviewError
from local_api.services.review_chunking import RequestBudget
from local_api.services.section_verification import verify_section_decisions


TEXT = 'Built reporting tools for a previous employer.'
ORIGINAL = 'skills'
PROPOSED = 'experience'


def run(tier, initial, replies):
    models = ('cheap-model', 'higher-model', 'strongest-model')
    settings = ReviewSettings(model=models[('cheap', 'higher', 'strongest').index(tier)],
                              section_consensus=True, section_review_models=models, routing_tier=tier)
    first = {'u0': [(0, len(TEXT), initial)]}
    calls = []
    state = {'provider_calls': 1}
    budget = RequestBudget()
    budget.take('test', 0, 'initial_review')
    def transport(config, _):
        calls.append(config.model)
        response = replies.pop(0)
        if isinstance(response, Exception):
            raise response
        return json.dumps(response)
    result = verify_section_decisions(settings, first, {'u0': (TEXT, ORIGINAL)}, [], transport,
                                      budget, 'test', 0, state, lambda text: {key: [tuple(p) for p in parts] for key, parts in json.loads(text).items()})
    assert state['provider_calls'] == budget.total == 1 + len(calls)
    return result['u0'][0][2], calls, state


def test_high_confidence_agreement_does_not_repeat_provider_call():
    decision, calls, _ = run('cheap', ORIGINAL, [])
    assert decision == ORIGINAL and not calls


def test_medium_consensus_accepts_two_agreeing_opinions():
    decision, calls, _ = run('higher', PROPOSED, [{'u0': [[0, len(TEXT), PROPOSED]]}])
    assert decision == PROPOSED and calls == ['cheap-model']


@pytest.mark.parametrize('verdict,quote,expected', [
    (ORIGINAL, 'reporting tools', ORIGINAL),
    (PROPOSED, 'previous employer', PROPOSED),
    (PROPOSED, 'invented quote', 'needs_review'),
    ('needs_review', '', 'needs_review'),
])
def test_disagreement_only_changes_placement_with_judge_source_evidence(verdict, quote, expected):
    decision, calls, state = run('cheap', PROPOSED, [
        {'u0': [[0, len(TEXT), ORIGINAL]]},
        {'decisions': {'u0': {'section': verdict, 'quote': quote}}},
    ])
    assert decision == expected and calls == ['higher-model', 'strongest-model']
    assert bool(state.get('consensus_unresolved')) == (expected == 'needs_review')


def test_low_confidence_conflict_goes_to_judge():
    decision, calls, _ = run('strongest', PROPOSED, [
        {'decisions': {'u0': {'section': PROPOSED, 'quote': 'previous employer'}}},
    ])
    assert decision == PROPOSED and calls == ['strongest-model']


def test_failed_independent_call_marks_review_without_another_transfer():
    decision, calls, state = run('higher', PROPOSED, [ReviewError('provider_unavailable')])
    assert decision == 'needs_review' and calls == ['cheap-model']
    assert state['consensus_unresolved']
