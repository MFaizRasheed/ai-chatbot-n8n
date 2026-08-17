"""LangGraph-powered conversational agent with automatic provider failover.

The agent is a small state graph: an LLM node that can optionally route to
a tool node and back. Conversation memory is kept per session using a
checkpointer keyed by ``thread_id`` (the client's ``session_id``).

Provider failover: the primary provider (``LLM_PROVIDER``) is tried first;
if it fails for any reason (auth error, rate limit, timeout, model error),
the same prompt is retried with each provider in ``LLM_FALLBACK_PROVIDERS``
in order. Providers without an API key configured are skipped. If every
provider fails, the last error is raised.

For production on serverless platforms (Vercel), ``MemorySaver`` keeps
memory only while an instance stays warm. Swap it for a durable
checkpointer (e.g. Postgres via Supabase) when memory must survive cold
starts — see the README.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are AI Assistant, a helpful and knowledgeable assistant. "
    "Answer the user's questions clearly and concisely. "
    "Use tools when they help answer the question."
)

# Sensible defaults per provider; override the primary with LLM_MODEL.
DEFAULT_MODELS = {
    "groq": "openai/gpt-oss-120b",
    "gemini": "gemini-3.6-flash",
    "openrouter": "openrouter/auto",
}

# The Settings field holding the API key for each provider.
PROVIDER_KEY_FIELD = {
    "groq": "groq_api_key",
    "gemini": "gemini_api_key",
    "openrouter": "openrouter_api_key",
}


def _provider_key(provider: str) -> str:
    try:
        return PROVIDER_KEY_FIELD[provider]
    except KeyError:
        raise ValueError(
            f"Unsupported LLM provider: {provider!r} "
            "(expected 'groq', 'gemini', or 'openrouter')"
        ) from None


def build_model(provider: str, model: str | None = None) -> BaseChatModel:
    """Create a chat model for the given provider."""
    settings = get_settings()
    _provider_key(provider)  # validate the provider name
    model_name = model or DEFAULT_MODELS[provider]
    timeout = settings.request_timeout

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=model_name,
            api_key=settings.groq_api_key,
            temperature=0.7,
            timeout=timeout,
        )

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model_name,
            api_key=settings.gemini_api_key,
            temperature=0.7,
            timeout=timeout,
        )

    if provider == "openrouter":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7,
            timeout=timeout,
        )

    raise ValueError(f"Unsupported LLM provider: {provider!r}")


def build_tools() -> list:
    """Default tool set for the agent."""
    from app.services.tools import build_send_email_tool

    return [build_send_email_tool()]


def build_models() -> list[BaseChatModel]:
    """Ordered model list: primary provider first, then fallbacks."""
    settings = get_settings()

    providers = [settings.llm_provider]
    providers += [
        p.strip()
        for p in settings.llm_fallback_providers.split(",")
        if p.strip()
    ]

    models: list[BaseChatModel] = []
    seen: set[str] = set()

    for index, provider in enumerate(providers):
        provider = provider.lower()
        if provider in seen:
            continue
        seen.add(provider)

        if not getattr(settings, _provider_key(provider), ""):
            logger.warning("Skipping LLM provider '%s': no API key configured", provider)
            continue

        # LLM_MODEL overrides the primary provider's model only.
        model_name = settings.llm_model if index == 0 else None
        models.append(build_model(provider, model=model_name))

    if not models:
        raise ValueError(
            "No LLM providers available. Set LLM_PROVIDER and the matching API "
            "key (and optionally LLM_FALLBACK_PROVIDERS)."
        )

    return models


def build_agent(models: list[BaseChatModel], tools: list | None = None) -> StateGraph:
    """Build the LangGraph agent: LLM node <-> optional tool node."""
    tools = list(tools or [])
    bound_models = [model.bind_tools(tools) if tools else model for model in models]

    def call_model(state: MessagesState) -> dict[str, list[BaseMessage]]:
        messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
        messages.extend(state["messages"])

        last_error: Exception | None = None
        for model in bound_models:
            try:
                return {"messages": [model.invoke(messages)]}
            except Exception as exc:  # noqa: BLE001 - fail over on any error
                last_error = exc
                logger.warning(
                    "LLM provider '%s' failed (%s): %s",
                    type(model).__name__,
                    type(exc).__name__,
                    exc,
                )

        assert last_error is not None
        raise last_error

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph


def _extract_text(content: Any) -> str:
    """Normalize an LLM response into plain text."""
    if isinstance(content, str):
        return content

    parts: list[str] = []
    for block in content or []:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    return "".join(parts)


class AgentService:
    def __init__(
        self,
        model: BaseChatModel | None = None,
        models: list[BaseChatModel] | None = None,
        tools: list | None = None,
    ) -> None:
        if models:
            self.models = list(models)
        elif model is not None:
            self.models = [model]
        else:
            self.models = build_models()

        self.tools = list(tools if tools is not None else build_tools())
        self.checkpointer = MemorySaver()
        self.graph = build_agent(self.models, self.tools).compile(
            checkpointer=self.checkpointer
        )

    async def chat(self, message: str, session_id: str) -> str:
        """Run the agent for one user message within a session."""
        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config={"configurable": {"thread_id": session_id}},
        )

        last = result["messages"][-1]
        return _extract_text(last.content)


# Module-level singleton used by the API routes.
agent_service = AgentService()
