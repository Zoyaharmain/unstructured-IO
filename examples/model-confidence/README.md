# Model evaluation sample

The sample asks a GPT model to answer and sends each completed answer to DeepSeek for an independent verdict. It accepts a `pass`; for `fail` or `uncertain`, it sends the judge's feedback to the next model in this fixed order:

1. `gpt-6-luna`
2. `gpt-6.1-terra`
3. `gpt-6-sol`
4. `gpt-6.1-sol`
5. `gpt-6.2-sol`
6. `gpt-6.2-astra`

Model call errors also move to the next model. If every model is exhausted or the judge is unavailable, the result is unresolved. A request for clarification stops and returns the question. A judge verdict is an opinion, not proof of correctness. Verify the model IDs and access for your account.

Set `OPENAI_API_KEY` and `DEEPSEEK_API_KEY` in your environment, without putting keys in source files. Run:

```sh
python3 examples/model-confidence/evaluate.py --input 'Explain database indexes'
python3 examples/model-confidence/evaluate.py --start-model gpt-6.2-astra --input 'A critical task'
```

`--start-model` chooses a starting point in the fixed order; the default is the first model. The judge defaults to `deepseek-chat` and can be changed with `--judge-model` or `DEEPSEEK_JUDGE_MODEL`.

JSON-line events go to stderr; the full JSON report goes to stdout and optionally to a new file via `--output`. The report contains model responses and judge feedback. Exit code 0 means accepted, and 2 means clarification or unresolved.

Run tests with `python3 -m unittest discover -s examples/model-confidence -p 'test_evaluate.py'`. Tests mock both providers.
