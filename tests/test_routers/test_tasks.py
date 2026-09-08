from typing import Sequence
from _pytest.mark.structures import ParameterSet
from fastapi.testclient import TestClient
import pytest


class TestGetTasks:
    def test_get_tasks_returns_200(
        self, token: dict[str, str], create_tasks: None, client: TestClient
    ):
        resp = client.get("/api/tasks", headers=token)
        assert resp.status_code == 200

    def test_get_tasks_auth_returns_401(self, create_tasks: None, client: TestClient):
        resp = client.get("/api/tasks")
        assert resp.status_code == 401


class TestCompleteUncompleteTask:
    def test_put_task_status_returns_200(
        self, token: dict[str, str], create_tasks: None, client: TestClient
    ):
        resp = client.put("/api/tasks/1/status", headers=token)
        assert resp.status_code == 200
        assert resp.json()["is_completed"] == True
        resp = client.put("/api/tasks/1/status", headers=token)
        assert resp.status_code == 200
        assert resp.json()["is_completed"] == False

    def test_put_task_status_auth_returns_401(
        self, create_tasks: None, client: TestClient
    ):
        resp = client.put("/api/tasks/1/status")
        assert resp.status_code == 401

    def test_put_task_status_returns_404(
        self, token: dict[str, str], create_tasks: None, client: TestClient
    ):
        resp = client.put("/api/tasks/0/status", headers=token)
        assert resp.status_code == 404

    def test_put_task_status_user_doesnt_own_returns_404(
        self,
        token: dict[str, str],
        token_2: dict[str, str],
        create_tasks: None,
        client: TestClient,
    ):
        resp1 = client.put("/api/tasks/1/status", headers=token)
        assert resp1.status_code == 200
        assert resp1.json()["is_completed"] is True

        task1 = client.get("/api/tasks/1", headers=token).json()
        task2 = client.get("/api/tasks/1", headers=token_2).json()
        assert task1["is_completed"] != task2["is_completed"]


class TestCreateTask:
    def test_create_task_returns_201(
        self, token: dict[str, str], create_tasks: None, client: TestClient
    ):
        resp = client.post(
            "/api/tasks",
            json={"name": "new task", "description": "new description", "priority": 8},
            headers=token,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "new task"
        assert data["user_task_id"] == 4

    @pytest.mark.parametrize(
        "body",
        ({"description": "new description", "priority": 5}),
    )
    def test_create_task_with_invalid_input_returns_422(
        self,
        body: dict[ParameterSet | Sequence[object] | object, str | int],
        token: dict[str, str],
        client: TestClient,
    ):
        resp = client.post(
            "/api/tasks",
            json=body,
            headers=token,
        )
        assert resp.status_code == 422

    def test_create_task_auth_returns_401(self, client: TestClient):
        resp = client.post(
            "/api/tasks",
            json={"description": "new description", "priority": 5},
        )
        assert resp.status_code == 401


class TestGetTask:
    def test_get_task_returns_200(
        self, create_tasks: None, client: TestClient, token: dict[str, str]
    ):
        resp = client.get("/api/tasks/1", headers=token)
        assert resp.status_code == 200
        assert resp.json()["name"] == "task 1"

    def test_get_task_returns_401(self, create_tasks: None, client: TestClient):
        resp = client.get("/api/tasks/1")
        assert resp.status_code == 401

    def test_get_task_returns_404(
        self, create_tasks: None, client: TestClient, token: dict[str, str]
    ):
        resp = client.get("/api/tasks/0", headers=token)
        assert resp.status_code == 404

    def test_get_task_user_doesnt_own_returns_404(
        self,
        token: dict[str, str],
        token_2: dict[str, str],
        create_tasks: None,
        client: TestClient,
    ):
        resp = client.get("/api/tasks/1", headers=token)
        assert resp.status_code == 200
        resp_2 = client.get("/api/tasks/1", headers=token_2)
        assert resp_2.status_code == 200
        assert resp.json() != resp_2.json()


class TestUpdateTask:
    @pytest.mark.parametrize(
        "body",
        (
            {
                "name": "new",
                "description": "new desc",
                "priority": 4,
            },
            {"name": "new", "description": "new desc"},
            {
                "name": "new",
                "priority": 4,
            },
            {"name": "new"},
        ),
    )
    def test_update_task_returns_200(
        self,
        body: dict[str, str | int] | dict[str, str],
        create_tasks: None,
        token: dict[str, str],
        client: TestClient,
    ):
        resp = client.put(
            "/api/tasks/1",
            json=body,
            headers=token,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "new"

    def test_update_task_returns_401(self, create_tasks: None, client: TestClient):
        resp = client.put(
            "/api/tasks/1",
            json={
                "name": "new",
                "description": "new desc",
                "priority": 4,
            },
        )
        assert resp.status_code == 401

    @pytest.mark.parametrize(
        "body",
        (
            {"description": "new desc", "priority": "num"},
            {"priority": 4.8},
            {"name": 13.1},
        ),
    )
    def test_update_task_with_invalid_body_returns_422(
        self, body, create_tasks: None, client: TestClient, token: dict[str, str]
    ):
        resp = client.put(
            "/api/tasks/1",
            json=body,
            headers=token,
        )
        assert resp.status_code == 422

    def test_update_task_returns_404(
        self, create_tasks: None, client: TestClient, token: dict[str, str]
    ):
        resp = client.put("/api/tasks/0", json={"name": "new"}, headers=token)
        assert resp.status_code == 404

    def test_update_task_user_doesnt_own_returns_404(
        self,
        token: dict[str, str],
        token_2: dict[str, str],
        create_tasks: None,
        client: TestClient,
    ):
        resp = client.put(
            "/api/tasks/1",
            json={"name": "new", "description": "new desc"},
            headers=token,
        )
        assert resp.status_code == 200
        resp_2 = client.get("/api/tasks/1", headers=token_2)
        assert resp_2.status_code == 200
        assert resp.json() != resp_2.json()


class TestDeleteTask:
    def test_delete_task_returns_204_and_removes_task(
        self, client: TestClient, token: dict[str, str], create_tasks: None
    ):
        resp = client.delete("/api/tasks/1", headers=token)
        assert resp.status_code == 204
        resp = client.get("/api/tasks/1", headers=token)
        assert resp.status_code == 404

    def test_delete_task_auth_returns_401(self, client: TestClient, create_tasks: None):
        resp = client.delete("/api/tasks/1")
        assert resp.status_code == 401

    def test_delete_nonexistent_task_returns_404(
        self, client: TestClient, token: dict[str, str], create_tasks: None
    ):
        resp = client.delete("/api/tasks/0", headers=token)
        assert resp.status_code == 404

    def test_delete_task_user_doesnt_own_returns_404_and_preserves_task(
        self,
        token: dict[str, str],
        token_2: dict[str, str],
        create_tasks: None,
        client: TestClient,
    ):
        resp = client.delete("/api/tasks/1", headers=token)
        assert resp.status_code == 204
        resp_2 = client.get("/api/tasks/1", headers=token_2)
        assert resp_2.status_code == 200
