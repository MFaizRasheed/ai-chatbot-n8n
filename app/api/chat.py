from fastapi import APIRouter, HTTPException

from app.models.chat import ChatRequest, ChatResponse
from app.services.n8n import N8NService

router = APIRouter(prefix="/api", tags=["chat"])

n8n_service = N8NService()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await n8n_service.send_message(request)

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to communicate with the AI service.",
        ) from exc
