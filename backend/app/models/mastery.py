from datetime import UTC, datetime

from sqlmodel import Field, SQLModel, UniqueConstraint


class Mastery(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "topic_id"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    topic_id: int = Field(foreign_key="topic.id", index=True)
    alpha: float = 1.0
    beta: float = 1.0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
