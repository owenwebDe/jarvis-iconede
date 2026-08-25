import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.llm_router import router as llm_router
from core import auth as core_auth


@pytest.fixture(autouse=True)
def _mock_auth(monkeypatch):
    monkeypatch.setattr(core_auth, "JARVIS_API_KEY", "")
    yield


@pytest.fixture()
def client():
    app = FastAPI()
    app.include_router(llm_router)
    return TestClient(app)


def test_llm_router_status_endpoint(client):
    response = client.get("/api/llm-router/status")
    assert response.status_code == 200
    data = response.json()
    assert "cascade_order" in data
    assert "groq" in data["cascade_order"]
    assert "pool" in data


def test_llm_router_add_key_endpoint(client):
    response = client.post(
        "/api/llm-router/keys",
        json={
            "provider": "groq",
            "api_key": "gsk_test_key_abc",
            "owner": "Owen",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["provider"] == "groq"
    assert data["owner"] == "Owen"


def test_llm_router_complete_endpoint(client):
    mock_result = {
        "id": "chatcmpl-123",
        "choices": [{"message": {"role": "assistant", "content": "Routed test response"}}],
    }

    with patch("services.llm_router.MultiModelRouter.chat_completion", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = mock_result
        response = client.post(
            "/api/llm-router/complete",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["choices"][0]["message"]["content"] == "Routed test response"
