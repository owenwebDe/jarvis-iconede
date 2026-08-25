import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.database import Base, engine
from routes.shared_memory import router as shared_memory_router
from core import auth as core_auth


@pytest.fixture(autouse=True)
def setup_db_and_auth(monkeypatch):
    monkeypatch.setattr(core_auth, "JARVIS_API_KEY", "")
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    app = FastAPI()
    app.include_router(shared_memory_router)
    return TestClient(app)


def test_prospects_api(client):
    # Create prospect
    res = client.post(
        "/api/shared-memory/prospects",
        json={
            "company_name": "Zenith Global Tech",
            "contact_name": "David Oladipo",
            "email": "david@zenithglobal.tech",
            "country": "Nigeria",
            "city": "Lagos",
            "industry": "FinTech & Enterprise Software",
            "status": "new",
            "lead_score": 90,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["company_name"] == "Zenith Global Tech"
    assert data["country"] == "Nigeria"

    # Search prospect
    res2 = client.get("/api/shared-memory/prospects?query=Zenith")
    assert res2.status_code == 200
    search_data = res2.json()
    assert search_data["count"] >= 1
    assert search_data["prospects"][0]["company_name"] == "Zenith Global Tech"


def test_creatives_api(client):
    res = client.post(
        "/api/shared-memory/creatives",
        json={
            "title": "Zenith FinTech Scale Ad",
            "headline": "Scale Payments Across Africa with Zero Friction",
            "body_copy": "Zenith Global Tech enables cross-border settlements in seconds.",
            "call_to_action": "Request Demo",
            "hook_type": "direct_offer",
            "target_audience": "Fintech CFOs and Founders",
            "status": "draft",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["headline"] == "Scale Payments Across Africa with Zero Friction"

    res2 = client.get("/api/shared-memory/creatives?status=draft")
    assert res2.status_code == 200
    assert res2.json()["count"] >= 1


def test_campaigns_api(client):
    res = client.post(
        "/api/shared-memory/campaigns",
        json={
            "name": "Zenith Lead Generation Q3",
            "objective": "OUTCOME_LEADS",
            "status": "PAUSED",
            "daily_budget": 100.0,
            "targeting": {"geos": ["NG", "GH", "KE", "ZA"]},
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Zenith Lead Generation Q3"
    assert data["status"] == "PAUSED"


def test_board_meetings_api(client):
    meeting_id = "meeting-zenith-expansion"

    # 1. Start meeting
    res1 = client.post(
        "/api/shared-memory/meetings",
        json={
            "meeting_id": meeting_id,
            "title": "Zenith Global Expansion Strategy",
            "agenda": "Coordinate lead research, ad creatives, and cold outreach",
            "participants": ["Jarvis", "LeadResearchAgent", "CreativeAgent", "OutreachAgent"],
        },
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "in_progress"

    # 2. Add deliberation entries
    res2 = client.post(
        f"/api/shared-memory/meetings/{meeting_id}/speak",
        json={"speaker": "LeadResearchAgent", "message": "Identified 45 top FinTech prospects across West & East Africa."},
    )
    assert res2.status_code == 200
    assert res2.json()["turn_index"] == 1

    # 3. Conclude meeting
    res3 = client.post(
        f"/api/shared-memory/meetings/{meeting_id}/conclude",
        json={"action_plan": "1. Launch Outreach sequence. 2. Prepare creative split-test."},
    )
    assert res3.status_code == 200
    assert res3.json()["status"] == "concluded"

    # 4. Get full meeting details
    res4 = client.get(f"/api/shared-memory/meetings/{meeting_id}")
    assert res4.status_code == 200
    meeting_data = res4.json()
    assert meeting_data["status"] == "concluded"
    assert len(meeting_data["transcript"]) == 1
    assert meeting_data["action_plan"] == "1. Launch Outreach sequence. 2. Prepare creative split-test."
