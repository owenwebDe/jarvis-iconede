import pytest
from core.database import Base, engine
from services import shared_memory


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_prospect_lifecycle():
    # 1. Upsert new global prospect
    prospect = shared_memory.upsert_prospect(
        company_name="Apex Logistics UK",
        contact_name="Sarah Jenkins",
        email="sarah@apexlogistics.co.uk",
        country="United Kingdom",
        city="London",
        industry="Freight & Supply Chain",
        source_agent="LeadResearchAgent",
        status="new",
        lead_score=85,
        notes="High-intent inbound prospect looking for Meta Ads scale.",
    )
    assert prospect["id"] is not None
    assert prospect["company_name"] == "Apex Logistics UK"
    assert prospect["lead_score"] == 85

    # 2. Search prospects
    results = shared_memory.search_prospects(query="Apex", country="United Kingdom")
    assert len(results) >= 1
    assert results[0]["company_name"] == "Apex Logistics UK"

    # 3. Update status
    updated = shared_memory.upsert_prospect(
        company_name="Apex Logistics UK",
        email="sarah@apexlogistics.co.uk",
        status="contacted",
        notes="Sent initial WhatsApp & email value pitch.",
    )
    assert updated["status"] == "contacted"
    assert "Sent initial WhatsApp" in updated["notes"]


def test_ad_creative_lifecycle():
    creative = shared_memory.upsert_ad_creative(
        title="Apex Supply Chain Q3 Campaign",
        headline="Cut International Freight Delays by 40%",
        body_copy="Struggling with cross-border customs bottlenecks? Apex provides automated tracking.",
        call_to_action="Get Free Audit",
        hook_type="pain_point",
        target_audience="Supply Chain Directors in UK & Europe",
        image_prompt="High-tech cargo container terminal at dusk with glowing data overlays, photorealistic 8k",
        variations=[
            {"headline": "Stop Losing Revenue to Shipping Delays", "body": "Apex eliminates customs headaches."},
        ],
    )
    assert creative["id"] is not None
    assert creative["headline"] == "Cut International Freight Delays by 40%"
    assert creative["status"] == "draft"

    listed = shared_memory.list_ad_creatives(status="draft")
    assert len(listed) >= 1
    assert any(c["title"] == "Apex Supply Chain Q3 Campaign" for c in listed)


def test_campaign_safety_defaults():
    campaign = shared_memory.create_or_update_campaign(
        name="Apex Q3 Meta Leads Campaign",
        objective="OUTCOME_LEADS",
        daily_budget=50.0,
        targeting={"geos": ["GB", "DE"], "age_min": 30, "age_max": 65},
        creative_ids=[1],
    )
    assert campaign["id"] is not None
    # Crucial safety rule verification: default status must be PAUSED
    assert campaign["status"] == "PAUSED"
    assert campaign["daily_budget"] == 50.0


def test_board_meeting_protocol():
    meeting_id = "meeting-2026-apex-strategy"
    
    # 1. Jarvis convenes board meeting
    started = shared_memory.start_board_meeting(
        meeting_id=meeting_id,
        title="Apex Logistics Global Meta Ads Strategy",
        agenda="1. Profile prospect 2. Develop creative angles 3. Set ad campaign parameters",
        participants=["Jarvis", "LeadResearchAgent", "CreativeAgent", "AdsAgent"],
    )
    assert started["status"] == "in_progress"

    # 2. Sub-agents contribute to the deliberation
    t1 = shared_memory.add_board_meeting_transcript(
        meeting_id=meeting_id,
        speaker="LeadResearchAgent",
        message="Apex Logistics UK has 150 employees, expanding into European freight. Key pain point: customs delays.",
    )
    assert t1["turn_index"] == 1

    t2 = shared_memory.add_board_meeting_transcript(
        meeting_id=meeting_id,
        speaker="CreativeAgent",
        message="I recommend a 3-part hook: pain-point angle addressing customs fines, plus a free customs ROI audit.",
    )
    assert t2["turn_index"] == 2

    t3 = shared_memory.add_board_meeting_transcript(
        meeting_id=meeting_id,
        speaker="AdsAgent",
        message="Will draft a Lead Gen campaign targeting B2B Logistics Decision Makers in UK and Germany with $50/day in PAUSED mode.",
    )
    assert t3["turn_index"] == 3

    # 3. Jarvis concludes the board meeting with the unified action plan
    concluded = shared_memory.conclude_board_meeting(
        meeting_id=meeting_id,
        action_plan="1. Deploy 3 creative variations. 2. Launch $50/day campaign in PAUSED state. 3. Outreach follow-up on day 2.",
    )
    assert concluded["status"] == "concluded"

    # 4. Verify complete record and chronological transcript
    details = shared_memory.get_board_meeting_details(meeting_id)
    assert details is not None
    assert len(details["transcript"]) == 3
    assert details["transcript"][0]["speaker"] == "LeadResearchAgent"
    assert details["transcript"][1]["speaker"] == "CreativeAgent"
    assert details["transcript"][2]["speaker"] == "AdsAgent"
    assert details["action_plan"] == concluded["action_plan"]
