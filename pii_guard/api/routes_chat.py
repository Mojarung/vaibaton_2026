"""OpenAI-совместимый прокси к внешней LLM."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ..errors import ApiError
from ..mask.restore import restore_tokens
from ..service import estimate_tokens
from .deps import current_system, log_outcome

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatMessage(BaseModel):
    model_config = {"extra": "allow"}

    role: str
    content: str | list | None


class ChatRequest(BaseModel):
    model_config = {"extra": "allow"}

    model: str | None = None
    messages: list[ChatMessage] = Field(min_length=1, max_length=200)
    stream: bool = False


def _content_text(content: str | list | None) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
    return "\n".join(parts)


@router.post("/chat/completions")
async def chat_completions(request: Request, body: ChatRequest) -> dict:
    system = current_system(request)
    if not system.policy.llm_proxy:
        raise ApiError("llm_proxy_disabled", 403, "Прокси к LLM отключён")
    if body.stream:
        raise ApiError("stream_not_supported", 400, "Потоковый режим не поддерживается")

    session = request.app.state.ctx.service.new_session(system)
    counts: Counter = Counter()
    masked_messages: list[dict] = []
    for msg in body.messages:
        text = _content_text(msg.content)
        mask_result = session.mask(text, request.app.state.ctx.service._detect(text, system, {}))
        counts.update(mask_result.counts)
        masked_messages.append({"role": msg.role, "content": mask_result.text})

    params = body.model_dump(exclude={"messages", "stream"}, exclude_none=True)
    llm = request.app.state.ctx.llm
    response = await llm.complete(masked_messages, params)

    tokens_in = sum(estimate_tokens(m["content"]) for m in masked_messages)
    restored = 0
    if system.policy.unmask:
        content = response["choices"][0]["message"]["content"]
        restored_content, restored = restore_tokens(content, session.token_map)
        response["choices"][0]["message"]["content"] = restored_content

    log_outcome(
        request,
        "llm",
        counts,
        {},
        sum(len(m["content"]) for m in masked_messages),
        tokens_in,
        restored,
    )

    if request.headers.get("x-pii-debug") == "1":
        response["pii_guard"] = {
            "system": system.id,
            "types": dict(counts),
            "sent_to_llm": masked_messages,
            "llm_raw_answer": response["choices"][0]["message"]["content"],
            "restored_tokens": restored,
        }
    return response
