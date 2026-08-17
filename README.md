# AI Chat Assistant

A conversational AI assistant powered by **LangChain + LangGraph**, served by
FastAPI and deployable to Vercel.

## Features
- AI conversational assistant (LangGraph agent with tool-calling support)
- Per-session conversation memory (LangGraph checkpointer)
- Multi-provider LLM support: Groq, Google Gemini, OpenRouter
- Static frontend served by FastAPI
- Vercel-ready (Python runtime, `pyproject.toml` + `uv.lock`)

## Requirements
- Python 3.12+
- uv
- An LLM API key (Groq, Gemini, or OpenRouter)

## Installation

```
uv sync
```

## Environment Variables

| Variable            | Description                              | Example                              |
| ------------------- | ---------------------------------------- | ------------------------------------ |
| `LLM_PROVIDER`      | Primary provider: `groq` \| `gemini` \| `openrouter` | `groq`                     |
| `LLM_FALLBACK_PROVIDERS` | Comma-separated fallbacks tried when the primary fails | `gemini,openrouter` |
| `LLM_MODEL`         | Optional model override for the primary provider | `gemini-3.6-flash`        |
| `GROQ_API_KEY`      | Groq API key                             | `gsk_...`                            |
| `GEMINI_API_KEY`    | Google Gemini API key                    | `AIza...`                            |
| `OPENROUTER_API_KEY`| OpenRouter API key                       | `sk-or-v1-...`                       |
| `GMAIL_USER`        | Primary Gmail address that sends emails   | `you@gmail.com`                      |
| `GMAIL_APP_PASSWORD`| App Password for the primary account      | `abcd efgh ijkl mnop`                |
| `GMAIL_USER_2`      | Optional second sender account            | `you2@gmail.com`                     |
| `GMAIL_APP_PASSWORD_2` | App Password for the second account    | `wxyz uvwx yzab cdef`                |

Copy `.env.example` to `.env` and fill in your values. The `.env` file is
gitignored — never commit secrets.

## Run

```
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Architecture

- `app/main.py` — FastAPI app, CORS, static frontend mount
- `app/api/chat.py` — `POST /api/chat` endpoint
- `app/services/agent.py` — LangGraph agent (LLM node + tool node, checkpointer)
- `app/config.py` — settings loaded from environment / `.env`

The agent keeps conversation memory per session via a LangGraph checkpointer
keyed by `session_id`. The in-memory `MemorySaver` works locally and on warm
serverless instances; for durable memory across cold starts on Vercel, swap in
a database-backed checkpointer (e.g. LangGraph's Postgres/Supabase
checkpointer).

### Sending emails

The agent has a `send_email` tool: ask it to "send the summary to
example@gmail.com" and it composes the summary from the conversation and
emails it from your Gmail account. You can configure up to two sender
accounts (`GMAIL_USER`/`GMAIL_APP_PASSWORD` plus optional
`GMAIL_USER_2`/`GMAIL_APP_PASSWORD_2`); say "send it **from my second
email**" and the agent uses that account. Set up each account once:

1. In your Google account, enable **2-Step Verification**.
2. Go to **Google Account → Security → App passwords**, create an App
   Password (16 characters), and copy it.
3. Set `GMAIL_USER` (the full Gmail address) and `GMAIL_APP_PASSWORD` (the
   16-character App Password, spaces optional).

> Gmail App Passwords require 2-Step Verification. If the account can't use
> them, you'd need the Gmail API with OAuth instead.

### Provider failover

If the primary provider (`LLM_PROVIDER`) fails — auth error, rate limit,
timeout, retired model, etc. — the same prompt is automatically retried with
each provider in `LLM_FALLBACK_PROVIDERS` in order. Providers without an API
key configured are skipped; if every provider fails, the request returns 502.
Example: `LLM_PROVIDER=groq` with `LLM_FALLBACK_PROVIDERS=gemini,openrouter`
means Groq is tried first, then Gemini, then OpenRouter.

## Deploy to Vercel

The app is configured for Vercel:

- **Framework**: FastAPI (auto-detected from `pyproject.toml`)
- **Entrypoint**: `app.main:app` (set via `tool.vercel.entrypoint`)
- **Runtime**: Python 3.12+ (Vercel supported versions: 3.12, 3.13, 3.14)
- **Function config**: `vercel.json` (`maxDuration: 60`, excludes dev files)

Steps:

1. Push this repository to GitHub.
2. In the [Vercel dashboard](https://vercel.com/new), click **Add New → Project** and import the repo.
3. Vercel auto-detects the FastAPI framework — leave the default build settings.
4. Add the environment variables under **Settings → Environment Variables**:
   - `LLM_PROVIDER` — e.g. `groq`
   - The matching API key (`GROQ_API_KEY`, `GEMINI_API_KEY`, or `OPENROUTER_API_KEY`)
   - `LLM_FALLBACK_PROVIDERS` — e.g. `gemini,openrouter` (optional)
   - `LLM_MODEL` — optional
5. Click **Deploy**.

Local preview: `npx vercel dev` (after `uv sync`).

> Note: the frontend in `frontend/` is served by FastAPI's static mount, so no
> extra static file config is needed.

## Testing

```
uv run pytest
```
