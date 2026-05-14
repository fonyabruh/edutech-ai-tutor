import json
import random

import httpx
from sqlmodel import Session, select

from app.llm.client import LLMClient
from app.llm.prompts import load_prompt
from app.models import Attempt, DiagnosticResult, Mastery, Subject, Task, Topic, User
from app.services.mastery import get_mastery_value, update_mastery


def pick_diagnostic_tasks(session: Session, subject_code: str) -> list[Task]:
    topics = session.exec(select(Topic).where(Topic.subject_code == subject_code)).all()
    random.shuffle(topics)
    selected = []
    difficulties = [1, 1, 2, 2, 2, 3]
    for i, topic in enumerate(topics[:6]):
        diff = difficulties[i] if i < len(difficulties) else 2
        tasks = session.exec(
            select(Task).where(Task.topic_id == topic.id, Task.difficulty == diff)
        ).all()
        if not tasks:
            tasks = session.exec(select(Task).where(Task.topic_id == topic.id)).all()
        if tasks:
            selected.append(random.choice(tasks))
    return selected


async def finalize_diagnostic(
    session: Session,
    user: User,
    subject_code: str,
    session_id: str,
    llm: LLMClient,
) -> DiagnosticResult:
    attempts = session.exec(
        select(Attempt).where(Attempt.user_id == user.id, Attempt.session_id == session_id)
    ).all()

    task_ids = [a.task_id for a in attempts]
    tasks = {t.id: t for t in session.exec(select(Task).where(Task.id.in_(task_ids))).all()}
    topics = {t.id: t for t in session.exec(select(Topic)).all()}

    for a in attempts:
        task = tasks.get(a.task_id)
        if task:
            update_mastery(session, user.id, task.topic_id, a.is_correct)
    session.flush()

    masteries = session.exec(
        select(Mastery).join(Topic).where(
            Mastery.user_id == user.id, Topic.subject_code == subject_code
        )
    ).all()
    mastery_map = {m.topic_id: get_mastery_value(m) for m in masteries}

    answers_summary = "\n".join(
        f"topic_id={tasks[a.task_id].topic_id}"
        f" ({topics.get(tasks[a.task_id].topic_id, Topic()).name}):"
        f" {'верно' if a.is_correct else 'неверно'}"
        for a in attempts
        if a.task_id in tasks
    )
    mastery_summary = "\n".join(
        f"topic_id={tid} ({topics[tid].name}): {v:.2f}"
        for tid, v in mastery_map.items()
        if tid in topics
    )

    subject = session.exec(select(Subject).where(Subject.code == subject_code)).first()
    subject_name = subject.name if subject else subject_code

    llm_data = {}
    try:
        msgs = load_prompt(
            "diagnose",
            grade=user.grade or 9,
            exam=user.exam or "ОГЭ",
            subject_name=subject_name,
            goal=user.goal or "хороший балл",
            answers_summary=answers_summary or "нет данных",
            mastery_summary=mastery_summary or "нет данных",
        )
        llm_data = await llm.chat(msgs, response_format="json")
    except (httpx.HTTPStatusError, httpx.ConnectError, json.JSONDecodeError) as e:
        print(f"\nLLM error in finalize_diagnostic: {e}")

    # validate/remap topic_ids from LLM against known IDs
    valid_ids = set(topics.keys())
    def filter_topics(lst):
        return [t for t in (lst or []) if isinstance(t, dict) and t.get("topic_id") in valid_ids]

    weak_fallback = [{"topic_id": tid} for tid, v in mastery_map.items() if v < 0.5]
    strong_fallback = [{"topic_id": tid} for tid, v in mastery_map.items() if v >= 0.5]

    weak_topics = filter_topics(llm_data.get("weak_topics")) or weak_fallback
    strong_topics = filter_topics(llm_data.get("strong_topics")) or strong_fallback

    avg_mastery = sum(mastery_map.values()) / len(mastery_map) if mastery_map else 0.5
    estimated_score = llm_data.get("estimated_score") or int(avg_mastery * 32)

    priority_skills = llm_data.get("priority_skills") or []
    if not isinstance(priority_skills, list):
        priority_skills = []

    result = DiagnosticResult(
        user_id=user.id,
        subject_code=subject_code,
        weak_topics=json.dumps(weak_topics, ensure_ascii=False),
        strong_topics=json.dumps(strong_topics, ensure_ascii=False),
        priority_skills=json.dumps(priority_skills, ensure_ascii=False),
        estimated_score=estimated_score,
        llm_summary=llm_data.get("overall_comment"),
    )
    session.add(result)
    session.commit()
    session.refresh(result)
    return result
