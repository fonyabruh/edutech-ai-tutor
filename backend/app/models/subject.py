from sqlmodel import Field, SQLModel


class Subject(SQLModel, table=True):
    code: str = Field(primary_key=True)
    name: str
