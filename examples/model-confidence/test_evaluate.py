import json
from contextlib import redirect_stderr
from io import BytesIO, StringIO
from fractions import Fraction
import unittest
from unittest.mock import patch
from urllib.error import URLError

from evaluate import available_tiers, build_request, call_model, evaluate, rank_models, repeat_until_confident


class SampleTests(unittest.TestCase):
    def test_input_reaches_the_requested_model(self):
        text = 'Summarize this JSON: {"apples": 3, "pears": 2}'
        request = build_request("model-a", text, "fake-key")
        body = json.loads(request.data)
        self.assertEqual(body["model"], "model-a")
        self.assertEqual(body["messages"][1]["content"], text)
        self.assertNotIn("fake-key", request.data.decode())

    def mock_response(self, confidence):
        data = {"model": "model-a-version", "id": "reply-1", "choices": [{
            "finish_reason": "stop", "message": {"content": json.dumps({
                "status": "answered", "answer": "42", "confidence": confidence, "reason": "Exact calculation"
            })}
        }]}
        return BytesIO(json.dumps(data).encode())

    def test_answer_and_model_attribution(self):
        with patch("evaluate.urlopen", return_value=self.mock_response(0.9)):
            result = call_model("model-a", "What is 6 times 7?", "fake-key")
        self.assertEqual(result["answer"], "42")
        self.assertEqual(result["returned_model"], "model-a-version")
        self.assertEqual(result["confidence"], 0.9)

    def test_out_of_range_confidence_is_rejected(self):
        with patch("evaluate.urlopen", return_value=self.mock_response(1.5)):
            with self.assertRaises(ValueError):
                call_model("model-a", "Question", "fake-key")

    def test_missing_probability_can_be_reported_as_null(self):
        with patch("evaluate.urlopen", return_value=self.mock_response(None)):
            self.assertIsNone(call_model("model-a", "Write a poem", "fake-key")["confidence"])

    def test_arithmetic_uses_no_model(self):
        def unexpected(*args):
            self.fail("Hardcoded arithmetic must not call an LLM")

        row = evaluate("What is 17 times 24?", "", {0: "cheap", 2: "higher"}, unexpected)
        self.assertEqual((row["stage"], row["answer"], row["calls"]), ("hardcoded", "408", []))

    def test_cheaper_model_is_accepted_at_threshold(self):
        def transport(model, text, key):
            self.assertEqual(model, "cheap")
            return {"answer": "Result", "confidence": 0.8, "returned_model": model}

        row = evaluate("Explain photosynthesis.", "fake", {0: "cheap", 2: "higher"}, transport)
        self.assertEqual(row["stage"], "cheaper_llm")
        self.assertEqual(len(row["calls"]), 1)

    def test_escalation_on_low_missing_or_failed_confidence(self):
        for score in (0.79, None, "error"):
            with self.subTest(score=score):
                def transport(model, text, key):
                    if model == "cheap" and score == "error":
                        raise URLError("offline")
                    return {"answer": model, "confidence": score if model == "cheap" else (0.75 if model == "middle" else 0.9)}

                row = evaluate("Explain photosynthesis.", "fake", {0: "cheap", 1: "middle", 2: "higher"}, transport)
                self.assertEqual(row["stage"], "higher_llm")
                self.assertEqual([call["selected_model"] for call in row["calls"]], ["cheap", "middle", "higher"])

    def test_calculate_with_period_stays_local(self):
        def unexpected(*args):
            self.fail("Simple arithmetic must stay local")

        row = evaluate("calculate 56 + 89.", "", {0: "cheap", 2: "higher"}, unexpected)
        self.assertEqual(row["answer"], "145")
        self.assertEqual(row["calls"], [])

    def test_clarification_stops_after_cheaper_model(self):
        def transport(model, text, key):
            self.assertEqual(model, "cheap")
            return {"status": "needs_clarification", "answer": "Which two databases?",
                    "confidence": None}

        row = evaluate("compare the tow database.", "fake", {0: "cheap", 1: "middle", 2: "higher"}, transport)
        self.assertEqual(row["status"], "needs_clarification")
        self.assertEqual(len(row["calls"]), 1)

    def test_wording_does_not_change_the_starting_tier(self):
        for text, expected in (
            ("Compare PostgreSQL and MongoDB.", "cheap"),
            ("Design the architecture for an event-processing system.", "cheap"),
        ):
            with self.subTest(text=text):
                calls = []

                def transport(model, question, key):
                    calls.append(model)
                    return {"answer": "result", "confidence": 0.9}

                evaluate(text, "fake", {0: "cheap", 1: "middle", 2: "higher"}, transport)
                self.assertEqual(calls, [expected])

    def test_api_catalog_is_used_instead_of_fixed_models(self):
        catalog = {"data": [{"id": name} for name in (
            "gpt-8-nano", "gpt-9-nano", "gpt-9-mini", "gpt-9-sol", "gpt-10-audio"
        )]}
        with patch("evaluate.urlopen", return_value=BytesIO(json.dumps(catalog).encode())) as opener:
            tiers = available_tiers("fake-key")
        self.assertEqual(opener.call_args.args[0].full_url, "https://api.openai.com/v1/models")
        self.assertEqual(tiers, {0: "gpt-9-nano", 1: "gpt-9-mini", 2: "gpt-9-sol"})
        selected = []
        def transport(model, text, key):
            selected.append(model)
            return {"answer": "Result", "confidence": 0.9}

        with patch("evaluate.available_tiers", return_value=tiers):
            evaluate("Compare PostgreSQL and MongoDB.", "fake-key", transport=transport)
        self.assertEqual(selected, ["gpt-9-nano"])

    def test_starts_at_lowest_available_tier(self):
        tiers = rank_models(["gpt-9-mini"])
        result = evaluate("Design the architecture.", "fake-key", tiers,
                          lambda *args: {"answer": "Result", "confidence": 0.9})
        self.assertEqual(result["initial_tier"], "medium_llm")

    def test_final_answer_appears_only_at_top_level(self):
        def transport(model, text, key):
            return {"answer": "The final answer", "reason": "A brief explanation",
                    "confidence": 0.95, "returned_model": model}

        row = evaluate("Design the architecture.", "fake", {2: "higher"}, transport)
        self.assertEqual(row["answer"], "The final answer")
        self.assertEqual(row["reason"], "A brief explanation")
        self.assertEqual(len(row["calls"]), 1)
        call = row["calls"][0]
        self.assertEqual(call["returned_model"], "higher")
        self.assertEqual(call["confidence"], 0.95)
        self.assertIn("seconds", call)
        self.assertNotIn("answer", call)
        self.assertNotIn("reason", call)

    def test_same_model_repeats_until_target_is_met(self):
        scores = iter([0.82, 0.90])
        calls = []

        def transport(model, text, key):
            calls.append((model, text))
            return {"answer": "4", "confidence": next(scores), "returned_model": model}

        progress = StringIO()
        with redirect_stderr(progress):
            result = repeat_until_confident("what is the sum of 2 + 2", "fake",
                                            "gpt-6-luna", 0.90, transport, show_progress=True)
        self.assertIn("Attempt 1 | gpt-6-luna | confidence 82.00% | FAIL", progress.getvalue())
        self.assertIn("Attempt 2 | gpt-6-luna | confidence 90.00% | PASS", progress.getvalue())
        self.assertEqual(calls, [("gpt-6-luna", "what is the sum of 2 + 2")] * 2)
        self.assertEqual(result["attempts"], 2)
        self.assertTrue(result["target_reached"])

    def test_high_confidence_stops_on_first_attempt(self):
        result = repeat_until_confident("Question", "fake", "luna", 0.9,
                                        lambda *args: {"confidence": 1.0})
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["stop_reason"], "target_reached")

    def test_repeat_can_run_past_thirty_attempts(self):
        scores = iter([0.89] * 30 + [0.9])
        result = repeat_until_confident("Question", "fake", "luna", 0.9,
                                        lambda *args: {"confidence": next(scores)})
        self.assertEqual(result["attempts"], 31)
        self.assertTrue(result["target_reached"])

    def test_exact_confidence_continues_past_one_hundred_percent(self):
        scores = iter([1.0, 0.82, 0.90])
        result = repeat_until_confident("Question", "fake", "luna", 0.9,
                                        lambda *args: {"confidence": next(scores)}, exact=True)
        self.assertEqual(result["attempts"], 3)
        self.assertTrue(result["target_reached"])

    def test_drop_mode_passes_high_scores_and_stops_on_failure(self):
        for failing_score in (0.90, 0.87):
            with self.subTest(failing_score=failing_score):
                scores = iter([1.0, 0.94, failing_score])
                progress = StringIO()
                with redirect_stderr(progress):
                    result = repeat_until_confident(
                        "Question", "fake", "luna", 0.90,
                        lambda *args: {"confidence": next(scores)},
                        stop_on_drop=True, show_progress=True,
                    )
                self.assertEqual(result["attempts"], 3)
                self.assertTrue(result["target_reached"])
                self.assertIn("Attempt 1 | luna | confidence 100.00% | PASS", progress.getvalue())
                self.assertIn(f"Attempt 3 | luna | confidence {failing_score:.2%} | FAIL",
                              progress.getvalue())

    def test_repeat_displays_and_checks_each_answer(self):
        responses = iter([
            {"answer": "9184.448718", "confidence": 1.0},
            {"answer": "9185", "confidence": 0.95},
            {"answer": "716387/78", "confidence": 0.90},
        ])
        progress = StringIO()
        with redirect_stderr(progress):
            result = repeat_until_confident(
                "Question", "fake", "luna", 0.90, lambda *args: next(responses),
                stop_on_drop=True, show_progress=True, expected=Fraction(716387, 78),
            )
        self.assertEqual(result["answer_checks"], ["CORRECT", "INCORRECT", "CORRECT"])
        self.assertEqual(result["confidence_fail_attempt"], 3)
        self.assertEqual(result["incorrect_answer_attempts"], [2])
        self.assertIn("Answer [CORRECT]: 9184.448718", progress.getvalue())
        self.assertIn("Answer [INCORRECT]: 9185", progress.getvalue())


if __name__ == "__main__":
    unittest.main()
