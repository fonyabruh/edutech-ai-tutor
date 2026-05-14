from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401
from app.api import auth, chat, diagnostic, lesson, plan, subjects, users
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="EduTech API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(subjects.router)
app.include_router(diagnostic.router)
app.include_router(plan.router)
app.include_router(lesson.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}
