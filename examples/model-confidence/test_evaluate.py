import json
from io import BytesIO, StringIO
from contextlib import redirect_stderr
import unittest
from unittest.mock import patch
from urllib.error import URLError

from evaluate import DEFAULT_MODELS, call_judge, call_model, emit, evaluate

MODELS = ('low-model', 'middle-model', 'high-model')


def candidate(answer='answer', status='answered'):
    return {'status': status, 'answer': answer, 'confidence': 0.99, 'reason': 'reason'}


def verdict(value):
    return {'verdict': value, 'reason': 'assessment', 'feedback': 'check evidence'}


class EvaluationTests(unittest.TestCase):
    def test_judge_rejection_escalates_even_with_high_self_confidence(self):
        seen = []
        def model(name, text, key, feedback):
            seen.append((name, feedback))
            return candidate(name)
        opinions = iter([verdict('fail'), verdict('uncertain'), verdict('pass')])
        result = evaluate('task', 'openai', 'deepseek', MODELS, model_transport=model,
                          judge_transport=lambda *args: next(opinions), logger=lambda *a, **k: None)
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(result['answer'], 'high-model')
        self.assertEqual([x[0] for x in seen], list(MODELS))
        self.assertEqual(seen[1][1]['judge_feedback'], 'check evidence')
        self.assertEqual(len(result['calls']), 3)

    def test_full_default_order(self):
        seen = []
        def model(name, *args):
            seen.append(name)
            return candidate(name)
        result = evaluate('task', 'a', 'b', model_transport=model,
                          judge_transport=lambda *a: verdict('fail'), logger=lambda *a, **k: None)
        self.assertEqual(seen, ['gpt-6-luna', 'gpt-6.1-terra', 'gpt-6-sol',
                                'gpt-6.1-sol', 'gpt-6.2-sol', 'gpt-6.2-astra'])
        self.assertEqual(result['status'], 'unresolved')

    def test_all_rejected_is_unresolved(self):
        result = evaluate('task', 'a', 'b', MODELS, model_transport=lambda *a: candidate(),
                          judge_transport=lambda *a: verdict('fail'), logger=lambda *a, **k: None)
        self.assertEqual((result['status'], result['answer']), ('unresolved', None))
        self.assertEqual(len(result['calls']), 3)

    def test_judge_failure_stops_without_acceptance(self):
        def failed(*args):
            raise URLError('offline')
        result = evaluate('task', 'a', 'b', MODELS, model_transport=lambda *a: candidate(),
                          judge_transport=failed, logger=lambda *a, **k: None)
        self.assertEqual(result['reason'], 'judge_error')
        self.assertEqual(len(result['calls']), 1)

    def test_candidate_failure_escalates_and_critical_starts_high(self):
        seen = []
        def model(name, *args):
            seen.append(name)
            if name == 'low-model':
                raise ValueError('bad response')
            return candidate()
        result = evaluate('task', 'a', 'b', MODELS, model_transport=model,
                          judge_transport=lambda *a: verdict('pass'), logger=lambda *a, **k: None)
        self.assertEqual(result['model'], 'middle-model')
        self.assertEqual(seen, ['low-model', 'middle-model'])
        seen.clear()
        evaluate('task', 'a', 'b', MODELS, start_model='high-model', model_transport=model,
                 judge_transport=lambda *a: verdict('pass'), logger=lambda *a, **k: None)
        self.assertEqual(seen, ['high-model'])

    def test_clarification_stops_without_judge(self):
        def judge(*args):
            self.fail('clarification should not be judged as an answer')
        result = evaluate('task', 'a', 'b', MODELS, model_transport=lambda *a: candidate('Which?', 'needs_clarification'),
                          judge_transport=judge, logger=lambda *a, **k: None)
        self.assertEqual(result['status'], 'needs_clarification')

    def test_transport_validates_and_sends_correct_provider_payload(self):
        response = {'id': '1', 'model': 'returned', 'choices': [{'finish_reason': 'stop',
                    'message': {'content': json.dumps(verdict('pass'))}}]}
        with patch('evaluate.urlopen', return_value=BytesIO(json.dumps(response).encode())) as opener:
            result = call_judge('judge', 'question', candidate(), 'secret')
        request = opener.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.deepseek.com/chat/completions')
        self.assertNotIn('secret', request.data.decode())
        self.assertEqual(result['verdict'], 'pass')
        response['choices'][0]['message']['content'] = json.dumps({'verdict': 'maybe'})
        with patch('evaluate.urlopen', return_value=BytesIO(json.dumps(response).encode())):
            with self.assertRaises(ValueError):
                call_judge('judge', 'question', candidate(), 'secret')

    def test_model_response_requires_valid_confidence(self):
        response = {'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps({**candidate(), 'confidence': 2})}}]}
        with patch('evaluate.urlopen', return_value=BytesIO(json.dumps(response).encode())):
            with self.assertRaises(ValueError):
                call_model('model', 'task', 'key')

    def test_events_are_json_lines(self):
        stream = StringIO()
        with redirect_stderr(stream):
            emit('answer_start', tier='low')
        self.assertEqual(json.loads(stream.getvalue()), {'event': 'answer_start', 'tier': 'low'})


if __name__ == '__main__':
    unittest.main()
