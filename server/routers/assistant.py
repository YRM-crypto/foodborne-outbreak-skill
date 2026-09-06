"""AI 助手：上下文感知问答 + 循证来源。"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import assistant as service

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatIn(BaseModel):
    event_id: str | None = None
    question: str
    history: list[ChatMessage] = []


@router.post("/chat")
async def chat(body: ChatIn):
    try:
        return await service.answer(body.event_id, body.question,
                                    [m.model_dump() for m in body.history])
    except ValueError as e:
        raise HTTPException(404 if "事件不存在" in str(e) else 400, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))
