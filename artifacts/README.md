# Execution evidence

`cloud-smoke.json` is produced by `python smoke_test.py` only after attempting the
real Azure service. It includes the fixed fictional prompts and model answers,
token counts, latency, model identifier, package versions, and individual checks.

A successful record has `execution: live_azure_foundry` and
`all_checks_passed: true`. A failed attempt records its error type and is never
presented as a successful cloud execution.

## First cloud run

[cloud-smoke-initial.json](cloud-smoke-initial.json) records the first real run on
12 October 2026: three completed requests against `gpt-5-mini`, 1,189 total tokens,
and two of three checks passed. The known-policy and missing-price checks passed.
The broad follow-up, “What is their responsibility in this process?”, produced
“The FAQ does not specify that.” and correctly remained a failed check.

The next revision explicitly tells the model to use conversation history for
references while keeping business facts grounded in the FAQ. The follow-up is
now a narrower recall question: “Which role did you just mention? Reply with that
role only.” Its check expects the role from the previous answer. The next run
records `evaluation_revision: 2`, the instruction hash, and generation settings.
Because the question and instructions changed, the rerun is a separate small
evaluation, not a relabeling of the initial failure.

## Revised cloud run

[cloud-smoke.json](cloud-smoke.json) records the revised run at
2026-10-12 20:37 UTC: **3/3 checks passed**, with **1,420 total tokens** against
`gpt-5-mini`. Observed latencies were 3.151, 3.501, and 3.274 seconds. The answers
identified the operations coordinator, recalled that role in the follow-up, and
declined to invent a price. This does not erase the initial failed check.

## Notebook execution

The walkthrough notebook was independently executed from its first code cell to
its last at **2026-10-12 20:39 UTC**, using the project virtual environment and
existing Azure CLI identity. All three model requests completed. Saved notebook
outputs contain the fictional instructions, real answers, and token usage;
no resource endpoint, response ID, subscription ID, or private local path is
included. [notebook-execution.json](notebook-execution.json) records **1,174 total
tokens**: 334 for the first answer, 461 for the follow-up, and 379 for the missing
price. The notebook outputs were inspected after execution.

No credentials, authenticated endpoint, subscription ID, or arbitrary user chat
history are written by the smoke test. These three checks are illustrative and
do not establish production readiness or robust resistance to prompt injection.
