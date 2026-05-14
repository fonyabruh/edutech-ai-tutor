from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    subject_code: str = Field(index=True)
    topic_id: int = Field(foreign_key="topic.id", index=True)
    difficulty: int
    type: str
    statement_md: str
    options: str | None = None
    answer: str
    solution_md: str
