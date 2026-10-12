"""Offline checks: no Azure credentials, network calls, or model charges."""

from types import SimpleNamespace

import pytest

import chat
from chat import Settings, ask, load_settings
from smoke_test import run_checks


class FakeResponses:
    def __init__(self, answers=None, status="completed"):
        self.calls = []
        self.answers = answers or ["The operations coordinator can approve a maintenance window."]
        self.status = status

    def create(self, **kwargs):
        self.calls.append(kwargs)
        answer = self.answers[min(len(self.calls) - 1, len(self.answers) - 1)]
        return SimpleNamespace(
            id=f"response-{len(self.calls)}",
            status=self.status,
            output_text=answer,
            model="test-model",
            usage=SimpleNamespace(input_tokens=30, output_tokens=10, total_tokens=40),
        )


def fake_client(**kwargs):
    return SimpleNamespace(responses=FakeResponses(**kwargs))


SETTINGS = Settings("https://sample.services.ai.azure.com/api/projects/test", "test-model")


def test_follow_up_passes_previous_response_and_repeats_instructions():
    client = fake_client()
    first, _ = ask(client, SETTINGS, "Who approves a window?")
    ask(client, SETTINGS, "Which role did you just mention?", first.id)
    assert "previous_response_id" not in client.responses.calls[0]
    assert client.responses.calls[1]["previous_response_id"] == first.id
    assert client.responses.calls[1]["instructions"] == client.responses.calls[0]["instructions"]
    assert client.responses.calls[1]["max_output_tokens"] == 1200
    assert client.responses.calls[1]["model"] == "test-model"


@pytest.mark.parametrize("question", ["", " ", "x" * 1001])
def test_invalid_question_never_calls_the_service(question):
    client = fake_client()
    with pytest.raises(ValueError):
        ask(client, SETTINGS, question)
    assert not client.responses.calls


def test_incomplete_response_is_not_reported_as_success():
    with pytest.raises(RuntimeError):
        ask(fake_client(status="incomplete"), SETTINGS, "Who approves?")


def test_reasoning_setting_is_optional_and_no_temperature_is_sent():
    client = fake_client()
    settings = Settings(SETTINGS.endpoint, SETTINGS.deployment_name, reasoning_effort="low")
    ask(client, settings, "Who approves?")
    assert client.responses.calls[0]["reasoning"] == {"effort": "low"}
    assert "temperature" not in client.responses.calls[0]
    ask(client, SETTINGS, "Who approves?")
    assert "reasoning" not in client.responses.calls[1]


def test_missing_answer_is_not_reported_as_success():
    with pytest.raises(RuntimeError):
        ask(fake_client(answers=[""]), SETTINGS, "Who approves?")


def test_cloud_check_report_does_not_include_endpoint_or_response_ids():
    client = fake_client(answers=[
        "The operations coordinator approves a maintenance window.",
        "The operations coordinator.",
        "The FAQ does not specify that.",
    ])
    report = run_checks(client, SETTINGS)
    assert report["all_checks_passed"]
    assert len(client.responses.calls) == 3
    assert "previous_response_id" in client.responses.calls[1]
    assert "previous_response_id" not in client.responses.calls[2]
    assert report["total_tokens"] == 120
    assert SETTINGS.endpoint not in str(report)
    assert "response-1" not in str(report)


def test_failed_behavior_check_stays_failed():
    client = fake_client(answers=["The coordinator.", "I do not know.", "It costs $99."])
    assert run_checks(client, SETTINGS)["all_checks_passed"] is False


def test_resource_endpoint_is_rejected(monkeypatch):
    monkeypatch.setattr(chat, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://sample.openai.azure.com/")
    monkeypatch.setenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "model")
    with pytest.raises(ValueError, match="project endpoint"):
        load_settings()


def test_placeholder_deployment_is_rejected(monkeypatch):
    monkeypatch.setattr(chat, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", SETTINGS.endpoint)
    monkeypatch.setenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "your-model-deployment")
    with pytest.raises(ValueError, match="deployment name"):
        load_settings()
