# AI Automation Assistant

## Features
- AI conversational assistant
- Persistent conversation memory
- Supabase PostgreSQL memory
- Gmail automation
- Natural-language email sending
- n8n automation workflow
- Python application

## Requirements
- Python 3.12+
- uv
- Docker
- n8n
- Supabase account
- Groq API key
- Gmail/Google Cloud OAuth credentials

## Installation

```
uv sync
```

## Environment Variables

| Variable          | Description                       | Example                              |
| ----------------- | --------------------------------- | ------------------------------------ |
| `N8N_WEBHOOK_URL` | n8n webhook that handles the chat | `https://your-n8n-host/webhook/chat` |
| `REQUEST_TIMEOUT` | Webhook timeout in seconds        | `30`                                 |

Copy `.env.example` to `.env` and fill in your values. The `.env` file is gitignored — never commit secrets.

## Run

```
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## n8n

Run n8n with Docker and import the workflow.

## Supabase

Configure PostgreSQL connection and chat-memory table.

## Gmail

Configure Google OAuth credentials in n8n.

## Deploy to Vercel

The app is already configured for Vercel:

- **Framework**: FastAPI (auto-detected from `pyproject.toml`)
- **Entrypoint**: `app.main:app` (set via `tool.vercel.entrypoint`)
- **Runtime**: Python 3.12+ (Vercel supported versions: 3.12, 3.13, 3.14)
- **Function config**: `vercel.json` (`maxDuration: 60` so the n8n webhook call has time to finish)

Steps:

1. Push this repository to GitHub.
2. In the [Vercel dashboard](https://vercel.com/new), click **Add New → Project** and import the repo.
3. Vercel auto-detects the FastAPI framework — leave the default build settings.
4. Add the environment variables under **Settings → Environment Variables**:
   - `N8N_WEBHOOK_URL` — your n8n webhook URL (required)
   - `REQUEST_TIMEOUT` — optional, defaults to `30`
5. Click **Deploy**.

Local preview: `npx vercel dev` (after `uv sync`).

> Note: the frontend in `frontend/` is served by FastAPI's static mount, so no extra static file config is needed.

## Testing

Test basic chat, memory, Gmail, and memory + Gmail.
