import pytest
from fastapi.testclient import TestClient
from fastapi.testclient import TestClient
import datetime
from jose import jwt
from sqlalchemy.orm.session import Session
from backend.app.config import settings as ss
from backend.app.database import models
from sqlalchemy import select


class TestLogin:
    def test_post_login_returns_200(self, register: None, client: TestClient):
        resp = client.post(
            "/api/login",
            data={"username": "example", "password": "example123"},
        )
        assert resp.status_code == 200

    @pytest.mark.parametrize(
        "username,password", [("false", "example123"), ("example", "false")]
    )
    def test_post_login_with_invalid_credentials_returns_400(
        self, register: None, username: str, password: str, client: TestClient
    ):
        resp = client.post(
            "/api/login",
            data={"username": username, "password": password},
        )
        assert resp.status_code == 400

    @pytest.mark.parametrize(
        "data",
        [
            ({"username": None, "password": "example123"}),
            ({"username": "example", "password": None}),
        ],
    )
    def test_post_login_with_missing_fields_returns_400(
        self, register: None, data: dict, client: TestClient
    ):
        resp = client.post(
            "/api/login",
            data=data,
        )
        assert resp.status_code == 400


class TestRegister:
    @pytest.mark.parametrize(
        "body",
        (
            {
                "name": "example",
                "password": "example123",
                "email": "example@gmail.com",
            },
            {
                "name": "example",
                "password": "example123",
            },
        ),
    )
    def test_post_register_returns_201(self, body: dict[str, str], client: TestClient):
        resp = client.post("/api/register", json=body)
        assert resp.status_code == 201

    @pytest.mark.parametrize(
        "body",
        ({"name": "example", "email": "example@gmail.com"}, {"password": "example123"}),
    )
    def test_post_register_with_invalid_body_returns_422(
        self, body: dict[str, str], client: TestClient
    ):
        resp = client.post("/api/register", json=body)
        assert resp.status_code == 422


class TestLogout:
    def test_logout_without_auth_returns_401(self, client: TestClient):
        response = client.delete("/api/logout")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_logout_success_returns_204(
        self, client: TestClient, token: dict[str, str], test_db: Session
    ):
        user_id = test_db.scalar(
            select(models.User.id).where(models.User.name == "example")
        )
        refresh_token = jwt.encode(
            {
                "sub": str(user_id),
                "exp": datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=1),
            },
            ss.REFRESH_SECRET_KEY,
            algorithm=ss.REFRESH_ALGORITHM,
        )

        test_db.add(
            models.RefreshToken(
                token=refresh_token,
                owner=user_id,
                expires_at=datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=1),
            )
        )
        test_db.commit()
        client.cookies = {"refresh_token": refresh_token}
        response = client.delete("/api/logout", headers=token)

        assert response.status_code == 204
        assert "access_token" not in response.cookies
        assert "refresh_token" not in response.cookies

        assert (
            test_db.scalar(
                select(models.RefreshToken).where(
                    models.RefreshToken.token == refresh_token
                )
            )
            is None
        )


class TestRefreshToken:
    def test_refresh_token_success_returns_200(
        self, client: TestClient, token: dict[str, str], test_db: Session
    ):
        user_id = test_db.scalar(
            select(models.User.id).where(models.User.name == "example")
        )
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=ss.REFRESH_TOKEN_EXPIRE_MINUTES
        )
        refresh_token = jwt.encode(
            {
                "sub": str(user_id),
                "exp": expires_at.timestamp(),
                "iat": datetime.datetime.now(datetime.timezone.utc).timestamp(),
            },
            ss.REFRESH_SECRET_KEY,
            algorithm=ss.REFRESH_ALGORITHM,
        )

        test_db.add(
            models.RefreshToken(
                token=refresh_token,
                owner=user_id,
                expires_at=datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=1),
            )
        )
        test_db.commit()

        db_token = test_db.scalar(
            select(models.RefreshToken).where(
                models.RefreshToken.token == refresh_token
            )
        )
        assert db_token is not None

        client.cookies = {"refresh_token": refresh_token}
        response = client.post("/api/refresh")

        print("Response:", response.json())
        assert response.status_code == 200

    def test_refresh_token_missing_returns_400(
        self, client: TestClient, token: dict[str, str]
    ):
        response = client.post("/api/refresh")
        assert response.status_code == 400
        assert response.json()["detail"] == "Refresh token missing"

    def test_refresh_token_expired_returns_401(
        self, client: TestClient, test_db: Session, token: dict[str, str]
    ):
        user_id = test_db.scalar(
            select(models.User.id).where(models.User.name == "example")
        )
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=ss.REFRESH_TOKEN_EXPIRE_MINUTES
        )
        expired_token = jwt.encode(
            {
                "sub": str(user_id),
                "exp": expires_at.timestamp(),
                "iat": datetime.datetime.now(datetime.timezone.utc).timestamp(),
            },
            ss.REFRESH_SECRET_KEY,
            algorithm=ss.REFRESH_ALGORITHM,
        )
        client.cookies = {"refresh_token": expired_token}
        response = client.post("/api/refresh")

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_refresh_token_not_in_db_returns_401(
        self, client: TestClient, token: dict[str, str], test_db: Session
    ):
        user_id = test_db.scalar(
            select(models.User.id).where(models.User.name == "example")
        )
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=ss.REFRESH_TOKEN_EXPIRE_MINUTES
        )
        refresh_token = jwt.encode(
            {
                "sub": str(user_id),
                "exp": expires_at.timestamp(),
                "iat": datetime.datetime.now(datetime.timezone.utc).timestamp(),
            },
            ss.REFRESH_SECRET_KEY,
            algorithm=ss.REFRESH_ALGORITHM,
        )
        client.cookies = {"refresh_token": refresh_token}
        response = client.post("/api/refresh")

        assert response.status_code == 401
        assert "detail" in response.json()
