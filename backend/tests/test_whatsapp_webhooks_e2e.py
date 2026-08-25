"""End-to-end integration tests for WhatsApp Webhook and Lead Ingestion endpoints."""

import pytest
from fastapi.testclient import TestClient
from server import app
from tools.whatsapp_outreach_server import (
    whatsapp_get_waha_status,
    whatsapp_get_lead_pipeline,
    whatsapp_get_pending_escalations,
    whatsapp_record_opt_out,
    whatsapp_generate_chat_link,
)
import json


@pytest.fixture
def client():
    # Disable setup gate during testing
    with TestClient(app) as test_client:
        yield test_client


def test_website_lead_ingestion_endpoint(client):
    """Verify that website form submissions trigger lead logging in CRM."""
    payload = {
        "name": "Dr. Emeka Nnamdi",
        "phone": "2348055554444",
        "source": "ordanic_homes_luxury_demo",
        "interest": "Guzape Hilltop Pavilion",
        "notes": "Looking to inspect this weekend",
        "auto_contact": False, # avoid external network calls during test
    }
    response = client.post("/api/v1/webhooks/leads", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Verify lead in pipeline
    pipeline_res = json.loads(whatsapp_get_lead_pipeline(limit=10))
    assert pipeline_res["status"] == "success"
    lead = next((l for l in pipeline_res["pipeline"] if l["phone_number"] == "2348055554444"), None)
    assert lead is not None
    assert lead["name"] == "Dr. Emeka Nnamdi"
    assert lead["interest"] == "Guzape Hilltop Pavilion"


def test_whatsapp_waha_webhook_endpoint(client):
    """Verify that inbound WAHA webhook receives and accepts message payload."""
    payload = {
        "event": "message",
        "session": "default",
        "payload": {
            "id": "true_2348012345678@c.us_12345",
            "from": "2348012345678@c.us",
            "body": "Hello, how much for a 6-bedroom villa in Maitama?",
            "fromMe": False,
        }
    }
    response = client.post("/api/v1/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_fastmcp_whatsapp_tools():
    """Verify that FastMCP tools execute correctly and return structured JSON."""
    status_raw = whatsapp_get_waha_status("default")
    status = json.loads(status_raw)
    assert "status" in status
    assert "state" in status

    opt_out_raw = whatsapp_record_opt_out("2348012349999", reason="Test opt-out")
    opt_out = json.loads(opt_out_raw)
    assert opt_out["status"] == "success"

    link_raw = whatsapp_generate_chat_link("08012345678", "Hello from FastMCP")
    link = json.loads(link_raw)
    assert link["status"] == "success"
    assert "https://wa.me/2348012345678" in link["wa_link"]
