import json

import httpx
from sqlmodel import Session, select

from app.llm.client import LLMClient
from app.llm.prompts import load_prompt
from app.models import LearningPlan, Mastery, Subject, Topic, User
from app.services.mastery import get_mastery_value


async def generate_plan(
    session: Session, user: User, subject_code: str, llm: LLMClient
) -> LearningPlan:
    topics = session.exec(select(Topic).where(Topic.subject_code == subject_code)).all()
    masteries = {
        m.topic_id: m
        for m in session.exec(select(Mastery).where(Mastery.user_id == user.id)).all()
    }

    prioritized = sorted(
        topics,
        key=lambda t: (1 - get_mastery_value(masteries.get(t.id, Mastery()))) * t.exam_weight,
        reverse=True,
    )

    topics_priority = "\n".join(
        f"{i+1}. topic_id={t.id} «{t.name}»"
        f" (mastery={get_mastery_value(masteries.get(t.id, Mastery())):.2f},"
        f" weight={t.exam_weight})"
        for i, t in enumerate(prioritized)
    )

    subject = session.exec(select(Subject).where(Subject.code == subject_code)).first()
    subject_name = subject.name if subject else subject_code

    days_data = []
    try:
        msgs = load_prompt(
            "plan",
            grade=user.grade or 9,
            exam=user.exam or "ОГЭ",
            subject_name=subject_name,
            goal=user.goal or "хороший балл",
            topics_priority=topics_priority,
        )
        result = await llm.chat(msgs, response_format="json")
        days_data = result.get("days", [])
    except (httpx.HTTPStatusError, httpx.ConnectError, json.JSONDecodeError) as e:
        print(f"\nLLM error in generate_plan: {e}")
        for day in range(1, 15):
            topic = prioritized[(day - 1) % len(prioritized)] if prioritized else None
            days_data.append({
                "day_index": day,
                "topics": [{"topic_id": topic.id, "minutes": 20, "focus": "практика"}]
                if topic else [],
                "summary": f"День {day}",
            })

    plan = LearningPlan(
        user_id=user.id,
        subject_code=subject_code,
        days=json.dumps(days_data, ensure_ascii=False),
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan
