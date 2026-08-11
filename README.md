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
- Python 3.11.14
- uv
- Docker
- n8n
- Supabase account
- Groq API key
- Gmail/Google Cloud OAuth credentials

## Installation

uv sync

## Environment Variables

N8N_WEBHOOK_URL=...

## Run

uv run ...

## n8n

Run n8n with Docker and import the workflow.

## Supabase

Configure PostgreSQL connection and chat-memory table.

## Gmail

Configure Google OAuth credentials in n8n.

## Testing

Test basic chat, memory, Gmail, and memory + Gmail.