import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.config import settings
from app.db import engine, get_session
from app.llm.client import LLMClient
from app.llm.prompts import load_prompt
from app.models import ChatMessage, DiagnosticResult, Subject, Topic, User

router = APIRouter(prefix="/chat", tags=["chat"])
llm = LLMClient(settings)


class SendRequest(BaseModel):
    subject_code: str
    message: str


@router.get("/history")
def get_history(
    subject_code: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    msgs = session.exec(
        select(ChatMessage)
        .where(ChatMessage.user_id == user.id, ChatMessage.subject_code == subject_code)
        .order_by(ChatMessage.created_at.desc())
        .limit(50)
    ).all()
    return list(reversed(msgs))


@router.post("/message")
async def send_message(
    body: SendRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user_msg = ChatMessage(
        user_id=user.id,
        subject_code=body.subject_code,
        role="user",
        content=body.message,
    )
    session.add(user_msg)
    session.commit()

    history = session.exec(
        select(ChatMessage)
        .where(ChatMessage.user_id == user.id, ChatMessage.subject_code == body.subject_code)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    ).all()

    subject = session.exec(select(Subject).where(Subject.code == body.subject_code)).first()
    subject_name = subject.name if subject else body.subject_code

    last_result = session.exec(
        select(DiagnosticResult)
        .where(
            DiagnosticResult.user_id == user.id,
            DiagnosticResult.subject_code == body.subject_code,
        )
        .order_by(DiagnosticResult.created_at.desc())
    ).first()

    if last_result:
        weak_ids = [w.get("topic_id") for w in json.loads(last_result.weak_topics)]
        weak_topics_objs = session.exec(select(Topic).where(Topic.id.in_(weak_ids))).all()
        weak_topics_str = ", ".join(t.name for t in weak_topics_objs)
    else:
        weak_topics_str = "нет данных"

    system_msgs = load_prompt(
        "tutor_chat",
        subject_name=subject_name,
        weak_topics=weak_topics_str,
    )

    history_msgs = [
        {"role": m.role, "text": m.content}
        for m in reversed(history)
    ]
    all_msgs = system_msgs + history_msgs

    collected = []
    user_id = user.id
    subject_code = body.subject_code

    async def sse_stream():
        try:
            async for chunk in llm.stream(all_msgs):
                collected.append(chunk)
                data = json.dumps({"text": chunk}, ensure_ascii=False)
                yield f"event: chunk\ndata: {data}\n\n"
            full_text = "".join(collected)
            with Session(engine) as s:
                assistant_msg = ChatMessage(
                    user_id=user_id,
                    subject_code=subject_code,
                    role="assistant",
                    content=full_text,
                )
                s.add(assistant_msg)
                s.commit()
            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(sse_stream(), media_type="text/event-stream")
