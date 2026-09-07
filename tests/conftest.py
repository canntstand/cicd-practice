from fastapi.security import OAuth2PasswordRequestForm
import pytest
from sqlalchemy import delete, select
from fastapi.testclient import TestClient
from backend.app.database import models
from backend.app.database.database import get_db
from backend.app.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.app.config import settings as ss
from backend.app.services.auth import login
from backend.app.services.recurring_tasks import create_recur_task
from backend.app.services.tasks import create_task
from backend.app.utils.dependencies import get_current_user
from backend.app.utils.hash import hash_pwd
from backend.app.validation import schemas


@pytest.fixture
def test_db():
    engine = create_engine(ss.DB_URL)
    SessionLocal = sessionmaker(autoflush=False, bind=engine)
    test_db = SessionLocal()
    try:
        yield test_db
    finally:
        test_db.rollback()
        test_db.execute(delete(models.RefreshToken))
        test_db.execute(delete(models.Task))
        test_db.execute(delete(models.RecurringTask))
        test_db.execute(delete(models.User))
        test_db.commit()
        test_db.close()
        engine.dispose()


@pytest.fixture
def client(test_db):
    app.dependency_overrides[get_db] = lambda: test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def register(test_db: Session):
    try:
        user = models.User(
            name="example",
            email="example@gmail.com",
            password=hash_pwd("example123"),
        )
        test_db.add(user)
        test_db.commit()
        yield
    finally:
        test_db.rollback()
        test_db.execute(
            delete(models.RefreshToken).where(
                models.RefreshToken.owner.in_(
                    select(models.User.id).where(models.User.name == "example")
                )
            )
        )
        test_db.execute(
            delete(models.RecurringTask).where(
                models.RecurringTask.owner.in_(
                    select(models.User.id).where(models.User.name == "example")
                )
            )
        )
        test_db.execute(
            delete(models.Task).where(
                models.Task.owner.in_(
                    select(models.User.id).where(models.User.name == "example")
                )
            )
        )
        test_db.execute(delete(models.User).where(models.User.name == "example"))
        test_db.commit()


@pytest.fixture
def token(register: None, test_db: Session):
    token: schemas.TokenResp = login(
        OAuth2PasswordRequestForm(username="example", password="example123"), test_db
    )
    return {"Authorization": f"Bearer {token.access_token}"}


@pytest.fixture
def register_2(test_db: Session):
    try:
        user = models.User(
            name="example_2",
            email="example_2@gmail.com",
            password=hash_pwd("example_2123"),
        )
        test_db.add(user)
        test_db.commit()
        yield
    finally:
        test_db.rollback()
        test_db.execute(
            delete(models.RefreshToken).where(
                models.RefreshToken.owner.in_(
                    select(models.User.id).where(models.User.name == "example_2")
                )
            )
        )
        test_db.execute(
            delete(models.RecurringTask).where(
                models.RecurringTask.owner.in_(
                    select(models.User.id).where(models.User.name == "example_2")
                )
            )
        )
        test_db.execute(
            delete(models.Task).where(
                models.Task.owner.in_(
                    select(models.User.id).where(models.User.name == "example_2")
                )
            )
        )
        test_db.execute(delete(models.User).where(models.User.name == "example_2"))
        test_db.commit()


@pytest.fixture
def token_2(register_2: None, test_db: Session):
    token: schemas.TokenResp = login(
        OAuth2PasswordRequestForm(username="example_2", password="example_2123"),
        test_db,
    )
    return {"Authorization": f"Bearer {token.access_token}"}


@pytest.fixture
def create_tasks(token_2: dict, token: dict, test_db: Session):
    user_id = get_current_user(token["Authorization"].split()[1], test_db)
    user_id_2 = get_current_user(token_2["Authorization"].split()[1], test_db)
    for num in range(1, 4):
        create_task(
            schemas.TaskWithOwner(
                name=f"task {num}",
                description=f"desc {num}",
                priority=num,
                owner=user_id,
            ),
            test_db,
        )
    for num in range(1, 4):
        create_task(
            schemas.TaskWithOwner(
                name=f"task {num}",
                description=f"desc {num}",
                priority=num,
                owner=user_id_2,
            ),
            test_db,
        )
    test_db.commit()
    yield


@pytest.fixture
def create_recur_tasks(token_2: dict, token: dict, test_db: Session):
    weekdays = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    user_id = get_current_user(token["Authorization"].split()[1], test_db)
    user_id_2 = get_current_user(token_2["Authorization"].split()[1], test_db)
    for num in range(1, 4):
        create_recur_task(
            schemas.RecurTaskWithOwner(
                name=f"task {num}",
                description=f"desc {num}",
                priority=num,
                days=weekdays[num - 1 : num + 2],
                owner=user_id,
            ),
            test_db,
        )
    for num in range(1, 4):
        create_recur_task(
            schemas.RecurTaskWithOwner(
                name=f"task {num}",
                description=f"desc {num}",
                priority=num,
                days=weekdays[num - 1 : num + 2],
                owner=user_id_2,
            ),
            test_db,
        )
    test_db.commit()
    yield
