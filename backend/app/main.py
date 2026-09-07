from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.templating import Jinja2Templates
from .routers import profile, recurring_tasks, tasks, auth, frontend

app = FastAPI(docs_url=None, redoc_url=None)
# app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")


# @app.get("/")
# async def root():
#     return RedirectResponse(url="/register")


# @app.get("/favicon.ico", include_in_schema=False)
# async def favicon():
#     return FileResponse("frontend/static/icons/favicon.ico")


# @app.exception_handler(401)
# async def http_exception_handler_401(request: Request, exc: HTTPException):
#     return templates.TemplateResponse(
#         "errors/401.html", {"request": request}, status_code=401
#     )


# @app.exception_handler(Exception)
# async def http_exception_handler(request: Request, exc: Exception):
#     return templates.TemplateResponse(
#         "errors/error.html", {"request": request}, status_code=500
#     )


# @app.exception_handler(404)
# async def http_exception_handler_404(request: Request, exc: HTTPException):
#     return templates.TemplateResponse(
#         "errors/404.html", {"request": request}, status_code=404
#     )


app.include_router(profile.router)
app.include_router(auth.router)
app.include_router(recurring_tasks.router)
app.include_router(tasks.router)
app.include_router(frontend.router)
