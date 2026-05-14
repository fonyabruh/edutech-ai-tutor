import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select

from app.db import engine, init_db
from app.models import Subject, Task, Topic

CONTENT = Path(__file__).parent.parent.parent / "content"


def load(name):
    return json.loads((CONTENT / name).read_text())


def upsert_subject(session, data):
    existing = session.exec(select(Subject).where(Subject.code == data["code"])).first()
    if existing:
        return existing
    obj = Subject(**data)
    session.add(obj)
    session.flush()
    return obj


def upsert_topic(session, subject_code, data):
    existing = session.exec(
        select(Topic).where(
            Topic.subject_code == subject_code, Topic.codifier_code == data["codifier_code"]
        )
    ).first()
    if existing:
        existing.name = data["name"]
        existing.exam_weight = data["exam_weight"]
        existing.theory_md = data.get("theory_md")
        session.flush()
        return existing
    obj = Topic(subject_code=subject_code, **data)
    session.add(obj)
    session.flush()
    return obj


def seed_tasks(session, subject_code, tasks_data, topic_map):
    for t in tasks_data:
        code = t["topic_codifier_code"]
        topic = topic_map.get(code)
        if not topic:
            print(f"\nWARN: topic {code} not found, skipping task")
            continue
        options = t.get("options")
        obj = Task(
            subject_code=subject_code,
            topic_id=topic.id,
            difficulty=t["difficulty"],
            type=t["type"],
            statement_md=t["statement_md"],
            options=(
                options if isinstance(options, str)
                else json.dumps(options, ensure_ascii=False) if options
                else None
            ),
            answer=t["answer"],
            solution_md=t["solution_md"],
        )
        session.add(obj)
    session.flush()


def run():
    init_db()
    with Session(engine) as session:
        for s in load("subjects.json"):
            upsert_subject(session, s)
        session.commit()

        for subject_code, topics_file, tasks_file in [
            ("math_base", "topics_math.json", "tasks_math.json"),
            ("rus", "topics_rus.json", "tasks_rus.json"),
            ("soc", "topics_soc.json", "tasks_soc.json"),
        ]:
            topics_data = load(topics_file)
            topic_map = {}
            for td in topics_data:
                topic = upsert_topic(session, subject_code, td)
                topic_map[td["codifier_code"]] = topic
            session.commit()

            tasks_data = load(tasks_file)
            # wipe existing tasks for this subject to re-seed cleanly
            existing = session.exec(select(Task).where(Task.subject_code == subject_code)).all()
            for t in existing:
                session.delete(t)
            session.flush()
            seed_tasks(session, subject_code, tasks_data, topic_map)
            session.commit()
            print(f"\nseeded {subject_code}: {len(topics_data)} topics, {len(tasks_data)} tasks")

    print("\ndone")


run()
