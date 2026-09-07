from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from ..utils.dependencies import get_current_user
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..services import users

router = APIRouter(tags=["Frontend", "For Users"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("/home", status_code=200)
def dashboard(request: Request, user_id: int = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/profile", status_code=200)
def profile_page(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    user = users.get_user(user_id, db)
    # user = schemas.UserOut(
    #     name="Roma", email="email@gmail.com", created_at=datetime.now(timezone.utc)
    # )
    return templates.TemplateResponse(
        "pages/profile/view.html",
        {"request": request, "user": user, "now": datetime.now(timezone.utc)},
    )


@router.get("/login", status_code=200)
def get_login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/register", status_code=200)
def get_register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})
