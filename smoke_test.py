"""Run three real Foundry requests and save evidence using only fictional test data."""

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from chat import ROOT, ask, build_instructions, load_settings, open_client


def evaluate_answer(case_name: str, answer: str) -> bool:
    """Simple regression checks, not an LLM quality or safety benchmark."""
    answer = answer.lower()
    if case_name == "known_policy":
        return "operations coordinator" in answer
    if case_name == "follow_up_context":
        return "operations coordinator" in answer
    if case_name == "missing_information":
        return "the faq does not specify that" in answer
    raise ValueError("Unknown check name.")


def run_checks(client, settings) -> dict:
    cases = [
        ("known_policy", "Who can approve a maintenance window?", False),
        ("follow_up_context", "Which role did you just mention? Reply with that role only.", True),
        ("missing_information", "What is the price of an urgent maintenance service?", False),
    ]
    results = []
    previous_response_id = None
    for name, question, use_history in cases:
        response, metrics = ask(
            client, settings, question, previous_response_id if use_history else None
        )
        previous_response_id = response.id
        results.append({
            "name": name,
            "question": question,
            "uses_previous_response": use_history,
            "answer": response.output_text,
            "status": response.status,
            "passed": evaluate_answer(name, response.output_text),
            "model": response.model,
            **metrics,
        })
    return {
        "schema_version": 1,
        "evaluation_revision": 2,
        "instructions_sha256": hashlib.sha256(build_instructions().encode()).hexdigest(),
        "request_settings": {
            "max_output_tokens": settings.max_output_tokens,
            "reasoning_effort": settings.reasoning_effort,
        },
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution": "live_azure_foundry",
        "authentication": "Microsoft Entra ID via DefaultAzureCredential",
        "api": "Responses API through AIProjectClient.get_openai_client()",
        "data": "Repository-owned fictional HarborWorks FAQ and three fixed prompts",
        "python_version": platform.python_version(),
        "dependencies": {name: version(name) for name in ("azure-ai-projects", "azure-identity", "openai")},
        "all_checks_passed": all(result["passed"] for result in results),
        "total_tokens": sum(result["total_tokens"] or 0 for result in results),
        "checks": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "cloud-smoke.json")
    args = parser.parse_args()
    report = {
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution": "failed_before_completion",
        "all_checks_passed": False,
    }
    try:
        settings = load_settings()
        with open_client(settings) as client:
            report = run_checks(client, settings)
    except Exception as error:
        # Persist the error type, never the raw exception or authenticated endpoint.
        report["error_type"] = type(error).__name__
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["all_checks_passed"]:
        print(f"3/3 live checks passed; {report['total_tokens']} tokens. Evidence: {args.output.name}")
        return 0
    print(f"Live checks did not all pass. Review {args.output.name}; no successful run is claimed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
