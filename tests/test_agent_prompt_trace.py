from __future__ import annotations

from contextlib import contextmanager

from app import agent as agent_module


class ManagedPrompt:
    version = 3

    def compile(self, **variables: str) -> str:
        return (
            f"Feature={variables['feature']}\n"
            f"Docs={variables['docs']}\n"
            f"Question={variables['message']}"
        )


class RecordingObservation:
    def __init__(self, attributes: dict) -> None:
        self.attributes = attributes
        self.updates: list[dict] = []

    def update(self, **kwargs) -> None:
        self.updates.append(kwargs)


class RecordingLangfuseClient:
    def __init__(self) -> None:
        self.prompt = ManagedPrompt()
        self.span_updates: list[dict] = []
        self.observations: list[RecordingObservation] = []

    def get_prompt(self, name: str, **kwargs):
        return self.prompt

    def update_current_span(self, **kwargs) -> None:
        self.span_updates.append(kwargs)

    @contextmanager
    def start_as_current_observation(self, **attributes):
        observation = RecordingObservation(attributes)
        self.observations.append(observation)
        yield observation


def test_agent_records_prompt_version_with_v4_observation_api(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    monkeypatch.setenv("LANGFUSE_PROMPT_LABEL", "production")
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(agent_module, "tracing_enabled", lambda: True)

    propagated: list[dict] = []

    @contextmanager
    def record_attributes(**kwargs):
        propagated.append(kwargs)
        yield

    monkeypatch.setattr(agent_module, "propagate_attributes", record_attributes)

    agent = agent_module.LabAgent()
    agent_module.LabAgent.run.__wrapped__(
        agent,
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Explain traces",
        correlation_id="req-12345678",
    )

    span_update = client.span_updates[-1]
    assert span_update["metadata"] == {
        "doc_count": 1,
        "query_preview": "Explain traces",
        "prompt_name": "day13-chat",
        "prompt_label": "production",
        "prompt_version": "3",
        "prompt_source": "langfuse",
        "prompt_fetch_error": "",
    }
    assert span_update["version"] == "3"
    assert propagated[0]["metadata"]["correlation_id"] == "req-12345678"
    assert propagated[-1]["prompt"] is client.prompt


def test_agent_creates_safe_retrieval_and_generation_observations(monkeypatch) -> None:
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(agent_module, "tracing_enabled", lambda: True)

    @contextmanager
    def no_attributes(**kwargs):
        yield

    monkeypatch.setattr(agent_module, "propagate_attributes", no_attributes)

    agent = agent_module.LabAgent()
    result = agent_module.LabAgent.run.__wrapped__(
        agent,
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="My email is demo.user@example.com",
        correlation_id="req-a1b2c3d4",
    )

    retrieval, generation = client.observations
    assert retrieval.attributes["name"] == "retrieval"
    assert retrieval.attributes["as_type"] == "retriever"
    assert "demo.user@example.com" not in str(retrieval.attributes["input"])
    assert retrieval.updates[-1]["output"]["doc_count"] >= 0

    assert generation.attributes["name"] == "llm-generation"
    assert generation.attributes["as_type"] == "generation"
    assert generation.attributes["model"] == agent.model
    assert generation.attributes["prompt"] is client.prompt
    assert "demo.user@example.com" not in str(generation.attributes["input"])
    generation_update = generation.updates[-1]
    assert generation_update["usage_details"] == {
        "input": result.tokens_in,
        "output": result.tokens_out,
    }
    assert generation_update["cost_details"] == {"total": result.cost_usd}
