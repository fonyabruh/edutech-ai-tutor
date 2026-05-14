from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class ChatMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    subject_code: str = Field(index=True)
    role: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
