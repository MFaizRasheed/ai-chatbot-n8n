from langchain_core.messages import AIMessage

from app.services.agent import AgentService


import pytest

from langchain_core.messages import AIMessage

from app.services.agent import AgentService


class FakeModel:
    """Minimal stand-in for a chat model so tests need no API keys."""

    def invoke(self, messages):
        return AIMessage(content="Hello from the fake model")

    def bind_tools(self, tools):
        return self


class FailingModel:
    """A model that always raises, used to test failover."""

    def invoke(self, messages):
        raise RuntimeError("provider down")

    def bind_tools(self, tools):
        return self


def test_agent_returns_model_response() -> None:
    service = AgentService(model=FakeModel())  # type: ignore[arg-type]

    result = service.graph.invoke(
        {"messages": [{"role": "user", "content": "hi"}]},
        config={"configurable": {"thread_id": "test-session"}},
    )

    assert result["messages"][-1].content == "Hello from the fake model"


def test_agent_falls_back_to_next_provider() -> None:
    service = AgentService(models=[FailingModel(), FakeModel()])  # type: ignore[list-item]

    result = service.graph.invoke(
        {"messages": [{"role": "user", "content": "hi"}]},
        config={"configurable": {"thread_id": "failover-session"}},
    )

    assert result["messages"][-1].content == "Hello from the fake model"


def test_agent_raises_when_all_providers_fail() -> None:
    service = AgentService(models=[FailingModel(), FailingModel()])  # type: ignore[list-item]

    with pytest.raises(RuntimeError, match="provider down"):
        service.graph.invoke(
            {"messages": [{"role": "user", "content": "hi"}]},
            config={"configurable": {"thread_id": "all-down-session"}},
        )


def test_send_email_reports_when_not_configured() -> None:
    from app.services.tools import _send_email

    result = _send_email("", "", "test@example.com", "Hi", "Body")

    assert "not configured" in result
    assert "GMAIL_USER" in result


def test_resolve_account_by_label_and_email() -> None:
    from app.services.tools import resolve_account

    accs = {
        "primary": ("one@gmail.com", "pw1"),
        "second": ("two@gmail.com", "pw2"),
    }

    assert resolve_account(accs, "") == ("one@gmail.com", "pw1")
    assert resolve_account(accs, "second") == ("two@gmail.com", "pw2")
    assert resolve_account(accs, "the second account") == ("two@gmail.com", "pw2")
    assert resolve_account(accs, "two@gmail.com") == ("two@gmail.com", "pw2")
    assert resolve_account(accs, "nope@x.com") is None


def test_send_email_from_unknown_account_reports_available() -> None:
    from app.services.tools import send_email_from

    accs = {
        "primary": ("one@gmail.com", "pw1"),
        "second": ("two@gmail.com", "pw2"),
    }

    result = send_email_from(accs, "to@x.com", "Hi", "Body", "from_account=weird")

    assert "Could not find a sender account" in result
    assert "primary" in result
    assert "second" in result


def test_agent_keeps_conversation_memory() -> None:
    service = AgentService(model=FakeModel())  # type: ignore[arg-type]

    service.graph.invoke(
        {"messages": [{"role": "user", "content": "first message"}]},
        config={"configurable": {"thread_id": "memory-session"}},
    )
    second = service.graph.invoke(
        {"messages": [{"role": "user", "content": "second message"}]},
        config={"configurable": {"thread_id": "memory-session"}},
    )

    # The checkpointer should have accumulated the conversation.
    assert len(second["messages"]) == 4
