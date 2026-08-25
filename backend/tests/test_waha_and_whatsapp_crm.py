"""Comprehensive Test Suite for Upgraded WhatsApp OS (WAHA, Pacing, Handoff, Drip, Webhooks)."""

import pytest
import asyncio
from services.waha_service import WahaService, get_waha_service
from services.whatsapp_pacing_service import WhatsAppPacingService, get_whatsapp_pacing_service
from services.whatsapp_handoff_service import WhatsAppHandoffService, get_whatsapp_handoff_service
from services.whatsapp_drip_service import WhatsAppDripService, get_whatsapp_drip_service


def test_waha_service_fallback():
    """Verify that when WAHA daemon is offline, it gracefully provides fallback links."""
    service = WahaService(base_url="http://127.0.0.1:9999")  # Intentionally offline port
    status = service.get_session_status("test_session")
    assert status["status"] == "offline"
    assert status["state"] == "DISCONNECTED"

    # Send message should fallback to click-to-chat link
    res = service.send_message(phone_number="+2348012345678", text="Hello from Jarvis!")
    assert res["status"] == "fallback_link"
    assert "https://wa.me/2348012345678" in res["web_link"]
    assert "whatsapp://send?phone=2348012345678" in res["desktop_protocol"]


def test_whatsapp_pacing_and_anti_ban():
    """Verify anti-ban typing jitter and opt-out filters."""
    pacing = get_whatsapp_pacing_service()
    
    # 1. Typing delay calculation
    short_delay = pacing.calculate_typing_delay("Hello")
    long_delay = pacing.calculate_typing_delay("This is a much longer consultative sales pitch message detailing our full-stack engineering portfolio and turnaround time for your Abuja business.")
    assert 2.5 <= short_delay <= 9.0
    assert 2.5 <= long_delay <= 9.0
    assert long_delay >= short_delay

    # 2. Opt-out keyword detection
    assert pacing.check_for_opt_out_keywords("Please STOP sending messages") is True
    assert pacing.check_for_opt_out_keywords("unsubscribe me") is True
    assert pacing.check_for_opt_out_keywords("I want to buy the villa") is False

    # 3. Opt-out persistence
    test_phone = "2348099998888"
    pacing.record_opt_out(test_phone, reason="Test keyword")
    assert pacing.is_opted_out(test_phone) is True

    # 4. Outreach validation
    valid, reason = pacing.validate_outreach(test_phone, "Hello")
    assert valid is False
    assert "opted out" in reason


def test_whatsapp_handoff_and_escalation():
    """Verify AI to Human escalation triggers and logging."""
    handoff = get_whatsapp_handoff_service()

    # 1. Trigger detection
    is_esc, trigger = handoff.check_escalation_triggers("Can I speak to a human please?")
    assert is_esc is True

    is_esc, trigger = handoff.check_escalation_triggers("I want to discuss custom contract terms with Owen directly")
    assert is_esc is True

    is_esc, trigger = handoff.check_escalation_triggers("What are the bedroom specs?")
    assert is_esc is False

    # 2. Escalation creation
    test_phone = "2348011112222"
    alert = handoff.escalate_to_human(test_phone, "Wants to speak with owner", "Can I talk to Owen?")
    assert alert["escalated"] is True
    assert alert["phone_number"] == test_phone
    assert "WhatsApp Escalation Alert" in alert["alert_message"]

    # 3. Retrieve pending
    pending = handoff.get_pending_escalations()
    assert any(p["phone_number"] == test_phone for p in pending)


def test_whatsapp_drip_pipeline():
    """Verify CRM lead recording and pipeline tracking."""
    drip = get_whatsapp_drip_service()

    test_phone = "2348077776666"
    res = drip.record_or_update_lead(
        phone_number=test_phone,
        name="Chief Alabi",
        source="ordanic_homes_website",
        interest="The Obsidian Villa",
        notes="Interested in 6-bedroom Maitama acquisition",
    )
    assert res["status"] == "success"
    assert res["stage"] == "NEW"

    # Update stage
    drip.update_lead_stage(test_phone, "QUALIFIED")

    # Fetch pipeline
    pipeline = drip.get_pipeline(limit=20)
    lead = next((l for l in pipeline if l["phone_number"] == test_phone), None)
    assert lead is not None
    assert lead["name"] == "Chief Alabi"
    assert lead["stage"] == "QUALIFIED"
