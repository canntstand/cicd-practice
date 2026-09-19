from fastapi import FastAPI

from .routers import auth, profile, recurring_tasks, tasks

app = FastAPI(docs_url="/docs", redoc_url="/redoc")

app.include_router(profile.router)
app.include_router(auth.router)
app.include_router(recurring_tasks.router)
app.include_router(tasks.router)