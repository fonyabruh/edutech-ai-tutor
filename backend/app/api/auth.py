from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from jose import jwt
from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import settings
from app.db import get_session
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class AnonymousRequest(BaseModel):
    device_id: str


def make_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_expires_days)
    return jwt.encode({"sub": user_id, "exp": expire}, settings.jwt_secret, algorithm="HS256")


def onboarding_completed(user: User) -> bool:
    return bool(user.grade and user.exam and user.subjects and user.subjects != "[]")


@router.post("/anonymous")
def anonymous_auth(body: AnonymousRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.device_id == body.device_id)).first()
    if not user:
        user = User(device_id=body.device_id)
        session.add(user)
        session.commit()
        session.refresh(user)
    return {
        "access_token": make_token(user.id),
        "user": {
            "id": user.id,
            "grade": user.grade,
            "exam": user.exam,
            "goal": user.goal,
            "subjects": user.subjects,
            "created_at": user.created_at,
            "onboarding_completed": onboarding_completed(user),
        },
    }
