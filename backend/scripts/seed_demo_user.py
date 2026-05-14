import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select

from app.db import engine, init_db
from app.models import Attempt, DiagnosticResult, LearningPlan, Mastery, Task, Topic, User


def run():
    init_db()
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.device_id == "demo-jury-001")).first()
        if existing:
            existing.grade = 11
            existing.exam = "ЕГЭ"
            existing.goal = "excellent"
            existing.subjects = json.dumps(["math_base", "rus"], ensure_ascii=False)
            user = existing
        else:
            user = User(
                device_id="demo-jury-001",
                grade=11,
                exam="ЕГЭ",
                goal="excellent",
                subjects=json.dumps(["math_base", "rus"], ensure_ascii=False),
            )
            session.add(user)
        session.flush()

        diag = session.exec(
            select(DiagnosticResult).where(
                DiagnosticResult.user_id == user.id,
                DiagnosticResult.subject_code == "math_base",
            )
        ).first()
        if not diag:
            diag = DiagnosticResult(user_id=user.id, subject_code="math_base")
            session.add(diag)
        diag.weak_topics = json.dumps(
            [
                {"topic_id": 1, "comment": "Тригонометрические уравнения требуют практики"},
                {"topic_id": 2, "comment": "Производные — проработай формулы"},
            ],
            ensure_ascii=False,
        )
        diag.strong_topics = json.dumps(
            [{"topic_id": 3, "comment": "Хорошее понимание линейных уравнений"}],
            ensure_ascii=False,
        )
        diag.priority_skills = json.dumps(
            ["Квадратные уравнения", "Тригонометрия", "Производные функций"],
            ensure_ascii=False,
        )
        diag.estimated_score = 68
        diag.llm_summary = (
            "Хороший базовый уровень. Основные пробелы — тригонометрия и производные. "
            "При работе 30 мин/день прогноз — 78+ баллов к маю."
        )
        session.flush()

        plan = session.exec(
            select(LearningPlan).where(
                LearningPlan.user_id == user.id,
                LearningPlan.subject_code == "math_base",
            )
        ).first()
        if not plan:
            plan = LearningPlan(user_id=user.id, subject_code="math_base")
            session.add(plan)
        days = [
            {
                "day_index": 1,
                "topics": [
                    {"topic_id": 1, "minutes": 20, "focus": "Тригонометрические уравнения"},
                    {"topic_id": 2, "minutes": 15, "focus": "Производные: базовые формулы"},
                ],
                "summary": "Разбор тригонометрии и производных",
                "status": "available",
            },
            {
                "day_index": 2,
                "topics": [
                    {"topic_id": 1, "minutes": 25, "focus": "Тригонометрические функции"},
                    {"topic_id": 3, "minutes": 10, "focus": "Линейные уравнения — повторение"},
                ],
                "summary": "Углублённая тригонометрия",
                "status": "locked",
            },
            {
                "day_index": 3,
                "topics": [
                    {"topic_id": 2, "minutes": 30, "focus": "Производные сложных функций"},
                ],
                "summary": "Практика производных",
                "status": "locked",
            },
            {
                "day_index": 4,
                "topics": [
                    {"topic_id": 1, "minutes": 20, "focus": "Тригонометрия: решение задач"},
                    {"topic_id": 2, "minutes": 15, "focus": "Производные: закрепление"},
                ],
                "summary": "Смешанная практика",
                "status": "locked",
            },
            {
                "day_index": 5,
                "topics": [
                    {"topic_id": 3, "minutes": 20, "focus": "Квадратные уравнения"},
                    {"topic_id": 1, "minutes": 15, "focus": "Тригонометрия: повторение"},
                ],
                "summary": "Квадратные уравнения и тригонометрия",
                "status": "locked",
            },
            {
                "day_index": 6,
                "topics": [
                    {"topic_id": 2, "minutes": 35, "focus": "Производные: мини-тест"},
                ],
                "summary": "Контрольная по производным",
                "status": "locked",
            },
            {
                "day_index": 7,
                "topics": [
                    {"topic_id": 1, "minutes": 20, "focus": "Тригонометрия: формулы приведения"},
                    {"topic_id": 3, "minutes": 15, "focus": "Уравнения — смешанный тип"},
                ],
                "summary": "Итоги первой недели",
                "status": "locked",
            },
            {
                "day_index": 8,
                "topics": [
                    {"topic_id": 2, "minutes": 25, "focus": "Дифференцирование — повторение"},
                    {"topic_id": 1, "minutes": 10, "focus": "Тригонометрия: закрепление"},
                ],
                "summary": "Начало второй недели",
                "status": "locked",
            },
            {
                "day_index": 9,
                "topics": [
                    {"topic_id": 3, "minutes": 30, "focus": "Системы уравнений"},
                ],
                "summary": "Системы уравнений",
                "status": "locked",
            },
            {
                "day_index": 10,
                "topics": [
                    {"topic_id": 1, "minutes": 20, "focus": "Тригонометрические неравенства"},
                    {"topic_id": 2, "minutes": 15, "focus": "Производные: применение"},
                ],
                "summary": "Неравенства и производные",
                "status": "locked",
            },
            {
                "day_index": 11,
                "topics": [
                    {"topic_id": 2, "minutes": 35, "focus": "Экстремумы функций"},
                ],
                "summary": "Нахождение экстремумов",
                "status": "locked",
            },
            {
                "day_index": 12,
                "topics": [
                    {"topic_id": 1, "minutes": 25, "focus": "Тригонометрия: финальная практика"},
                    {"topic_id": 3, "minutes": 10, "focus": "Уравнения — повторение"},
                ],
                "summary": "Финальная практика тригонометрии",
                "status": "locked",
            },
            {
                "day_index": 13,
                "topics": [
                    {"topic_id": 2, "minutes": 20, "focus": "Производные: итоговый разбор"},
                    {"topic_id": 3, "minutes": 15, "focus": "Смешанные задачи"},
                ],
                "summary": "Итоговый разбор",
                "status": "locked",
            },
            {
                "day_index": 14,
                "topics": [
                    {"topic_id": 1, "minutes": 20, "focus": "Финальный тест — тригонометрия"},
                    {"topic_id": 2, "minutes": 15, "focus": "Финальный тест — производные"},
                    {"topic_id": 3, "minutes": 10, "focus": "Финальный тест — уравнения"},
                ],
                "summary": "Финальное тестирование",
                "status": "locked",
            },
        ]
        plan.days = json.dumps(days, ensure_ascii=False)
        session.flush()

        first_topic = session.exec(
            select(Topic).where(Topic.subject_code == "math_base")
        ).first()

        if first_topic:
            tasks = session.exec(
                select(Task).where(Task.topic_id == first_topic.id).limit(5)
            ).all()
            for i, task in enumerate(tasks):
                attempt = Attempt(
                    user_id=user.id,
                    task_id=task.id,
                    session_id="demo-session-001",
                    is_correct=i < 2,
                    is_diagnostic=False,
                )
                session.add(attempt)
            session.flush()

        all_topics = session.exec(
            select(Topic).where(Topic.subject_code == "math_base")
        ).all()
        for topic in all_topics:
            exists = session.exec(
                select(Mastery).where(
                    Mastery.user_id == user.id, Mastery.topic_id == topic.id
                )
            ).first()
            if exists:
                exists.alpha = 2.0
                exists.beta = 3.0
            else:
                session.add(Mastery(user_id=user.id, topic_id=topic.id, alpha=2.0, beta=3.0))
        session.flush()

        session.commit()

    print("\nDemo user ready: device_id=demo-jury-001")


run()
