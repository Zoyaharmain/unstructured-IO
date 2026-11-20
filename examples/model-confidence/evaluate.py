"""Try a local rule, then a cheaper model, then a higher model if needed."""
import argparse
from fractions import Fraction
import json
import os
import operator
import re
import sys
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ENDPOINT = "https://api.openai.com/v1/chat/completions"


def build_request(model, text, key):
    instructions = (
        "Answer or perform the task requested in the user input. If the intent is "
        "missing essential information, ask a clarifying question and use status "
        "needs_clarification with null confidence. Otherwise use status answered. "
        "Return JSON containing status, answer (text), confidence (your estimate "
        "from 0 to 1 that the answer is correct, or null if unavailable), and reason."
    )
    body = {
        "model": model,
        "messages": [{"role": "system", "content": instructions},
                     {"role": "user", "content": text}],
        "response_format": {"type": "json_object"},
    }
    return Request(ENDPOINT, data=json.dumps(body).encode(), headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})


def call_model(model, text, key):
    with urlopen(build_request(model, text, key), timeout=45) as response:
        data = json.load(response)
    choice = data["choices"][0]
    if choice["finish_reason"] != "stop":
        raise ValueError("Incomplete response")
    decision = json.loads(choice["message"]["content"])
    if not isinstance(decision, dict):
        raise ValueError("Expected a JSON object")
    confidence = decision.get("confidence")
    valid_confidence = confidence is None or (
        type(confidence) in (int, float) and 0 <= confidence <= 1
    )
    status = decision.get("status")
    if (status not in ("answered", "needs_clarification")
            or "confidence" not in decision or not valid_confidence
            or not isinstance(decision.get("answer"), str) or not decision["answer"].strip()
            or not isinstance(decision.get("reason"), str)):
        raise ValueError("Invalid response")
    usage = data.get("usage") or {}
    return {
        "returned_model": data.get("model"), "response_id": data.get("id"),
        "status": status, "answer": decision["answer"],
        "confidence": None if status == "needs_clarification" else confidence,
        "reason": decision["reason"],
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }


def hardcoded_answer(text):
    match = re.fullmatch(
        r"\s*(?:(?:what is|calculate|compute)\s+)?(-?[0-9]{1,12})\s*(\+|-|\*|×|times)\s*(-?[0-9]{1,12})\s*[?.=]?\s*",
        text, re.IGNORECASE,
    )
    if match is None:
        return None
    left, symbol, right = match.groups()
    operations = {"+": operator.add, "-": operator.sub, "*": operator.mul,
                  "×": operator.mul, "times": operator.mul}
    return str(operations[symbol.lower()](int(left), int(right)))


def model_call(tier, model, text, key, transport):
    row = {"stage": tier, "selected_model": model}
    start = time.monotonic()
    try:
        row.update(transport(model, text, key))
    except HTTPError as error:
        row["error"] = f"HTTP {error.code}"
        error.close()
    except (URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError) as error:
        row["error"] = type(error).__name__
    row["seconds"] = round(time.monotonic() - start, 3)
    return row


def available_tiers(key):
    request = Request("https://api.openai.com/v1/models",
                      headers={"Authorization": f"Bearer {key}"})
    with urlopen(request, timeout=45) as response:
        models = json.load(response)["data"]
    return rank_models(item["id"] for item in models)


def rank_models(model_ids):
    """Choose the newest recognized general-purpose model in each size class."""
    candidates = {}
    for model in model_ids:
        match = re.fullmatch(r"gpt-(\d+(?:\.\d+)*)(?:-(nano|mini|sol|luna|pro))?", model)
        if match is None:
            continue
        version, variant = match.groups()
        tier = {"nano": 0, "mini": 1}.get(variant, 2)
        rank = (tuple(map(int, version.split("."))), variant == "pro", model)
        if tier not in candidates or rank > candidates[tier]:
            candidates[tier] = rank
    return {tier: rank[-1] for tier, rank in candidates.items()}


def evaluate(text, key, models=None, transport=call_model, threshold=0.80):
    answer = hardcoded_answer(text)
    if answer is not None:
        return {"stage": "hardcoded", "status": "answered", "answer": answer, "confidence": None, "calls": []}

    if models is None:
        models = available_tiers(key)
    if not models:
        raise ValueError("No recognized general-purpose models available for this API key")
    labels = ("cheaper_llm", "medium_llm", "higher_llm")
    tiers = [(labels[tier], models[tier]) for tier in sorted(models)]
    calls = []
    for tier, model in tiers:
        row = model_call(tier, model, text, key, transport)
        calls.append(row)
        confidence = row.get("confidence")
        if row.get("status") == "needs_clarification" or (
            "error" not in row and confidence is not None and confidence >= threshold
        ):
            break
    call_history = [
        {key: value for key, value in row.items() if key not in {"answer", "reason"}}
        for row in calls
    ]
    return {**calls[-1], "initial_tier": tiers[0][0], "calls": call_history}


def check_answer(answer, expected):
    if expected is None or not isinstance(answer, str):
        return "UNVERIFIED"
    try:
        actual = Fraction(answer.strip().strip("*`$").strip())
    except (ValueError, ZeroDivisionError):
        return "UNVERIFIED"
    return "CORRECT" if abs(actual - expected) <= Fraction(1, 1_000_000) else "INCORRECT"


def repeat_until_confident(text, key, model, threshold, transport=call_model, *,
                           show_progress=False, exact=False, stop_on_drop=False, expected=None):
    scores = []
    checks = []
    if stop_on_drop:
        text += (
            "\n\nFor your confidence estimate, consider which parts of your answer you actually checked. "
            "For a numerical problem, distinguish deriving a correct method from verifying the exact "
            "computed result. Account for unchecked computations and assumptions, and explain the "
            "main source of uncertainty in your reason."
        )
    while True:
        result = model_call("repeat", model, text, key, transport)
        confidence = result.get("confidence")
        scores.append(confidence)
        checks.append(check_answer(result.get("answer"), expected))
        attempt = len(scores)
        if stop_on_drop:
            reached = confidence is not None and confidence <= threshold
        else:
            reached = confidence is not None and (confidence == threshold if exact else confidence >= threshold)
        if show_progress:
            score = "unavailable" if confidence is None else f"{confidence:.2%}"
            detail = result.get("error") or result.get("status") or "response received"
            if stop_on_drop:
                outcome = "NO SCORE" if confidence is None else ("FAIL" if reached else "PASS")
            else:
                outcome = "PASS" if reached else "FAIL"
            print(f"Attempt {attempt} | {model} | confidence {score} | {outcome} | {detail}",
                  file=sys.stderr, flush=True)
            if "answer" in result:
                print(f"  Answer [{checks[-1]}]: {result['answer']}", file=sys.stderr, flush=True)
        if "error" in result:
            stop_reason = "api_error"
            break
        if result.get("status") == "needs_clarification":
            stop_reason = "needs_clarification"
            break
        if reached:
            stop_reason = "target_reached"
            break
    return {**result, "attempts": len(scores), "target_confidence": threshold,
            "target_reached": stop_reason == "target_reached",
            "stop_reason": stop_reason, "confidence_scores": scores, "answer_checks": checks,
            "confidence_fail_attempt": len(scores) if stop_on_drop and stop_reason == "target_reached" else None,
            "incorrect_answer_attempts": [index for index, check in enumerate(checks, 1)
                                          if check == "INCORRECT"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="A question, task, or data with instructions")
    source.add_argument("--file", type=Path, help="UTF-8 input, or '-' for standard input")
    parser.add_argument("--output", type=Path, help="Optional new path for the JSON report")
    parser.add_argument("--model", help="Model ID for repeat mode")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--until-confidence", type=float, help="Stop at or above this confidence (0 to 1)")
    target.add_argument("--until-confidence-drops", type=float,
                        help="Pass above this confidence and stop at or below it (0 to 1)")
    parser.add_argument("--exact-confidence", action="store_true", help="Match the confidence target exactly")
    parser.add_argument("--expected-answer", help="Known numeric answer for repeat mode (e.g. 4 or 1/3)")
    args = parser.parse_args()
    expected = None
    if args.expected_answer is not None:
        if args.model is None:
            parser.error("--expected-answer requires repeat mode")
        try:
            expected = Fraction(args.expected_answer)
        except (ValueError, ZeroDivisionError):
            parser.error("--expected-answer must be a number or fraction")
    if args.exact_confidence and args.until_confidence is None:
        parser.error("--exact-confidence requires --until-confidence")
    stop_on_drop = args.until_confidence_drops is not None
    threshold = args.until_confidence_drops if stop_on_drop else args.until_confidence
    if (args.model is None) != (threshold is None):
        parser.error("Provide --model and one confidence target together")
    if threshold is not None and not 0 <= threshold <= 1:
        parser.error("Confidence target must be from 0 to 1")
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    try:
        if args.file is None:
            text = args.input
        elif args.file == Path("-"):
            text = sys.stdin.read()
        else:
            text = args.file.read_text(encoding="utf-8")
        if not text.strip():
            parser.error("Supply non-empty input")
        if not key and (args.model is not None or hardcoded_answer(text) is None):
            parser.error("Set OPENAI_API_KEY for questions that need an LLM")
        def run():
            if args.model is not None:
                return repeat_until_confident(text, key, args.model, threshold, show_progress=True,
                                              exact=args.exact_confidence, stop_on_drop=stop_on_drop,
                                              expected=expected)
            return evaluate(text, key)

        if args.output:
            with args.output.open("x", encoding="utf-8") as stream:
                result = run()
                json.dump(result, stream, indent=2, ensure_ascii=False)
        else:
            result = run()
    except HTTPError as error:
        parser.error(f"OpenAI model discovery failed (HTTP {error.code})")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(f"Could not complete evaluation: {error}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return int("error" in result)


if __name__ == "__main__":
    raise SystemExit(main())
