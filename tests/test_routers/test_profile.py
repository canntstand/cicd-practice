from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select
import pytest
from typing import Any
from backend.app.database import models
from backend.app.utils.dependencies import get_current_user


class TestGetProfile:
    def test_get_profile_returns_correct_data_200(
        self, client: TestClient, token: dict[str, str], test_db: Session
    ):
        user_id = get_current_user(token["Authorization"].split()[1], test_db)
        user = test_db.execute(
            select(models.User).where(models.User.id == user_id)
        ).scalar_one()

        resp = client.get("/api/profile", headers=token)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == user.name
        assert data["email"] == user.email
        assert "password" not in data

    def test_get_profile_auth_returns_401(self, client: TestClient):
        resp = client.get("/api/profile")
        assert resp.status_code == 401


class TestDeleteProfile:
    def test_delete_profile_returns_204(
        self, client: TestClient, token: dict[str, str], test_db: Session
    ):
        user_id = get_current_user(token["Authorization"].split()[1], test_db)
        assert (
            test_db.execute(
                select(models.User).where(models.User.id == user_id)
            ).scalar_one_or_none()
            is not None
        )

        resp = client.delete("/api/profile", headers=token)
        assert resp.status_code == 204

        assert (
            test_db.execute(
                select(models.User).where(models.User.id == user_id)
            ).scalar_one_or_none()
            is None
        )

        assert (
            test_db.execute(
                select(models.RefreshToken).where(models.RefreshToken.owner == user_id)
            ).scalar_one_or_none()
            is None
        )

    def test_delete_profile_returns_401(self, client: TestClient):
        resp = client.delete("/api/profile")
        assert resp.status_code == 401

    def test_delete_profile_also_deletes_user_tasks(
        self,
        client: TestClient,
        token: dict[str, str],
        test_db: Session,
        create_tasks: None,
    ):
        user_id = get_current_user(token["Authorization"].split()[1], test_db)

        tasks = (
            test_db.execute(select(models.Task).where(models.Task.owner == user_id))
            .scalars()
            .all()
        )
        assert len(tasks) > 0

        resp = client.delete("/api/profile", headers=token)
        assert resp.status_code == 204

        tasks_after = (
            test_db.execute(select(models.Task).where(models.Task.owner == user_id))
            .scalars()
            .all()
        )
        assert len(tasks_after) == 0


class TestUpdateProfile:
    @pytest.mark.parametrize(
        "body",
        (
            {
                "name": "new example",
                "password": "new example123",
                "email": "newexample@gmail.com",
            },
            {"name": "new example123", "password": "new example123"},
            {
                "name": "example",
                "password": "new example123",
                "email": "newexample@gmail.com",
            },
        ),
    )
    def test_update_profile_returns_200(
        self, body: dict[str, str], client: TestClient, token: dict[str, str]
    ):
        resp = client.patch("/api/profile", json=body, headers=token)
        assert resp.status_code == 200

    def test_update_profile_auth_returns_401(self, client: TestClient):
        resp = client.patch(
            "/api/profile", json={"name": "example", "password": "example123"}
        )
        assert resp.status_code == 401

    @pytest.mark.parametrize(
        "email",
        [
            "invalid-email",
            "no@dot",
        ],
    )
    def test_update_profile_with_invalid_email_returns_422(
        self, email: str, client: TestClient, token: dict[str, str]
    ):
        resp = client.patch(
            "/api/profile",
            json={"name": "name", "password": "password123", "email": email},
            headers=token,
        )
        assert resp.status_code == 422

    def test_update_profile_changes_data_in_db(
        self, client: TestClient, token: dict[str, str], test_db: Session
    ):
        user_id = get_current_user(token["Authorization"].split()[1], test_db)
        new_data = {
            "name": "New Name",
            "password": "NewPassword123",
            "email": "new.email@example.com",
        }

        resp = client.patch("/api/profile", json=new_data, headers=token)
        assert resp.status_code == 200

        updated_user = test_db.execute(
            select(models.User).where(models.User.id == user_id)
        ).scalar_one()

        assert updated_user.name == new_data["name"]
        assert updated_user.email == new_data["email"]
        assert updated_user.password == new_data["password"]

    @pytest.mark.parametrize(
        "body",
        (
            {"name": 123},
            {"password": 1.234},
            {"email": "newexample@@gmail.com"},
        ),
    )
    def test_update_profile_with_invalid_data_returns_422(
        self, body: dict[Any, Any], client: TestClient, token: dict[str, str]
    ):
        resp = client.patch("/api/profile", json=body, headers=token)
        assert resp.status_code == 422
