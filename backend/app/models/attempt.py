from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Attempt(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    task_id: int = Field(foreign_key="task.id")
    session_id: str | None = Field(default=None, index=True)
    user_answer: str | None = None
    is_correct: bool
    is_diagnostic: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
