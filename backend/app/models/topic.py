from sqlmodel import Field, SQLModel, UniqueConstraint


class Topic(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("subject_code", "codifier_code"),)

    id: int | None = Field(default=None, primary_key=True)
    subject_code: str = Field(foreign_key="subject.code", index=True)
    name: str
    codifier_code: str = Field(index=True)
    exam_weight: float = 0.1
    theory_md: str | None = None
