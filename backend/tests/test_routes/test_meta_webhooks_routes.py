import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.database import Base, engine
from routes.meta_webhooks import router as meta_webhooks_router
from core import auth as core_auth


@pytest.fixture(autouse=True)
def setup_db_and_auth(monkeypatch):
    monkeypatch.setattr(core_auth, "JARVIS_API_KEY", "")
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    app = FastAPI()
    app.include_router(meta_webhooks_router)
    return TestClient(app)


def test_meta_webhook_verification_endpoint(client):
    # Valid handshake
    res = client.get(
        "/api/meta/webhook?hub.mode=subscribe&hub.verify_token=iconedge_meta_verify_token_2026&hub.challenge=test_challenge_code"
    )
    assert res.status_code == 200
    assert res.text == "test_challenge_code"

    # Invalid token handshake -> 403 Forbidden
    res_bad = client.get(
        "/api/meta/webhook?hub.mode=subscribe&hub.verify_token=bad_token&hub.challenge=test_challenge_code"
    )
    assert res_bad.status_code == 403


def test_meta_webhook_event_endpoint(client):
    payload = {
        "object": "page",
        "entry": [
            {
                "id": "page_test_101",
                "messaging": [
                    {
                        "sender": {"id": "fb_user_443322"},
                        "message": {"text": "Can you share pricing for Meta Ads scale?"},
                    }
                ],
            }
        ],
    }
    res = client.post("/api/meta/webhook", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "EVENT_RECEIVED"
    assert data["summary"]["count"] == 1


def test_meta_simulate_inbound_endpoint(client):
    res = client.post(
        "/api/meta/simulate-inbound",
        json={
            "sender_id": "sim_user_7788",
            "message_text": "I want to hire IconEdge for our B2B SaaS marketing.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_high_intent"] is True
    assert data["lead_status"] == "qualified"
