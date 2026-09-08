from fastapi import FastAPI

from .routers import profile, recurring_tasks, tasks, auth

app = FastAPI(docs_url=False, redoc_url=False)

app.include_router(profile.router)
app.include_router(auth.router)
app.include_router(recurring_tasks.router)
app.include_router(tasks.router)