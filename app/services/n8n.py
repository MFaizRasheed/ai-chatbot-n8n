import httpx

from app.config import get_settings
from app.models.chat import ChatRequest, ChatResponse


class N8NService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def send_message(self, request: ChatRequest) -> ChatResponse:
        if not self.settings.n8n_webhook_url:
            raise RuntimeError("N8N_WEBHOOK_URL is not configured.")

        payload = {
            "message": request.message,
            "sessionId": request.session_id,
        }

        timeout = httpx.Timeout(self.settings.request_timeout)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                self.settings.n8n_webhook_url,
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

        # n8n may return either "response" or "reply".
        result = data.get("response") or data.get("reply")

        if result is None:
            raise RuntimeError(f"Unexpected n8n response format: {data}")

        return ChatResponse(response=str(result))
