from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    device_id: str = Field(unique=True, index=True)
    grade: int | None = None
    exam: str | None = None
    goal: str | None = None
    subjects: str = Field(default="[]")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
