from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class DiagnosticResult(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    subject_code: str = Field(index=True)
    weak_topics: str = "[]"
    strong_topics: str = "[]"
    priority_skills: str = "[]"
    estimated_score: int | None = None
    llm_summary: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
