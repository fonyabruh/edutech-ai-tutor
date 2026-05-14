import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.config import settings
from app.db import get_session
from app.llm.client import LLMClient
from app.models import LearningPlan, User
from app.services.plan import generate_plan

router = APIRouter(prefix="/plan", tags=["plan"])
llm = LLMClient(settings)


class GenerateRequest(BaseModel):
    subject_code: str


@router.post("/generate")
async def generate(
    body: GenerateRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    plan = await generate_plan(session, user, body.subject_code, llm)
    return {"id": plan.id, "subject_code": plan.subject_code, "days": json.loads(plan.days)}


@router.get("/current")
async def get_current_plan(
    subject_code: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    plan = session.exec(
        select(LearningPlan)
        .where(LearningPlan.user_id == user.id, LearningPlan.subject_code == subject_code)
        .order_by(LearningPlan.created_at.desc())
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No plan found")
    return {"id": plan.id, "subject_code": plan.subject_code, "days": json.loads(plan.days)}


@router.post("/day/{day_index}/complete")
async def complete_day(
    day_index: int,
    subject_code: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    plan = session.exec(
        select(LearningPlan)
        .where(LearningPlan.user_id == user.id, LearningPlan.subject_code == subject_code)
        .order_by(LearningPlan.created_at.desc())
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No plan found")
    days = json.loads(plan.days)
    for day in days:
        if day["day_index"] == day_index:
            day["status"] = "complete"
            break
    plan.days = json.dumps(days, ensure_ascii=False)
    session.add(plan)
    session.commit()
    return {"day_index": day_index, "status": "complete"}
