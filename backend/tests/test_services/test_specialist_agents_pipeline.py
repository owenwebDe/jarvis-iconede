import pytest
from core.database import Base, engine
from services import shared_memory
from tools import meta_marketing_server


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_end_to_end_specialist_agents_pipeline():
    """End-to-End Test: Lead Research ➔ Creative ➔ Ads ➔ Outreach ➔ Board Meeting."""
    
    # ── Step 1: Lead Research Agent discovers global prospect ──────────────
    lead = shared_memory.upsert_prospect(
        company_name="Nova Logistics Berlin GmbH",
        contact_name="Klaus Weber",
        email="klaus.weber@novalogistics.de",
        phone="+493012345678",
        website="https://novalogistics.de",
        country="Germany",
        city="Berlin",
        industry="European Freight & Supply Chain",
        source_agent="LeadResearchAgent",
        status="new",
        lead_score=92,
        notes="Fast-growing mid-market freight company. Pain point: 35% manual customs clearance overhead.",
    )
    assert lead["id"] is not None
    assert lead["lead_score"] == 92

    # ── Step 2: Creative Agent crafts multi-angle ad copy & visual prompts ─
    prospects = shared_memory.search_prospects(query="Nova Logistics")
    assert len(prospects) == 1
    target_lead = prospects[0]

    creative = shared_memory.upsert_ad_creative(
        title="Nova Logistics Customs Automation Campaign",
        headline="Cut EU Customs Processing Time by 65%",
        body_copy=f"Dear {target_lead['contact_name']}, manual customs bottlenecks cost European freight forwarders thousands each week. Discover automated real-time dispatch.",
        call_to_action="Claim Customs Audit",
        hook_type="pain_point",
        target_audience=f"{target_lead['industry']} in {target_lead['country']}",
        image_prompt="Modern German logistics warehouse with automated cargo scanning and glowing data visualization, 8k photorealistic",
        variations=[
            {"headline": "Zero Customs Delays Across Germany & EU", "hook_type": "direct_offer"},
            {"headline": "How Top German Forwarders Save 120+ Hours Monthly", "hook_type": "story"},
        ],
    )
    assert creative["id"] is not None
    assert creative["hook_type"] == "pain_point"

    # ── Step 3: Ads Agent drafts campaign with PAUSED safety rule ──────────
    ad_camp = meta_marketing_server.meta_ads_create_campaign(
        ad_account_id="act_iconedge_meta_01",
        name="Nova Logistics - EU Freight Growth Q3",
        objective="OUTCOME_LEADS",
        daily_budget_dollars=120.0,
    )
    assert ad_camp["delivery_status"] == "PAUSED"
    assert "No spend will occur" in ad_camp["safety_note"]

    # ── Step 4: Outreach Agent builds personalized multi-channel sequence ──
    whatsapp_pitch = (
        f"Hi {target_lead['contact_name']}, noticed {target_lead['company_name']} is scaling cross-border freight in {target_lead['country']}. "
        f"We just helped a similar freight operator reduce customs clearance delays by 65%. Mind if I share a 2-min breakdown?"
    )
    updated_lead = shared_memory.upsert_prospect(
        company_name=target_lead["company_name"],
        email=target_lead["email"],
        status="contacted",
        notes=f"Outreach Touch 1 (WhatsApp): {whatsapp_pitch}",
    )
    assert updated_lead["status"] == "contacted"
    assert "Outreach Touch 1" in updated_lead["notes"]

    # ── Step 5: Jarvis convenes Board Meeting to finalize execution ───────
    meeting_id = "board-meeting-nova-growth"
    shared_memory.start_board_meeting(
        meeting_id=meeting_id,
        title="Nova Logistics Germany Expansion Action Plan",
        agenda="1. Review lead intelligence 2. Confirm creative hooks 3. Review Meta Ads payload (PAUSED) 4. Authorize outreach",
        participants=["Jarvis", "LeadResearchAgent", "CreativeAgent", "AdsAgent", "OutreachAgent"],
    )

    shared_memory.add_board_meeting_transcript(
        meeting_id=meeting_id,
        speaker="LeadResearchAgent",
        message="Klaus Weber identified as COO of Nova Logistics. Lead score 92/100 based on freight volume.",
    )
    shared_memory.add_board_meeting_transcript(
        meeting_id=meeting_id,
        speaker="CreativeAgent",
        message="Crafted pain-point and direct-offer hooks emphasizing 65% customs time reduction.",
    )
    shared_memory.add_board_meeting_transcript(
        meeting_id=meeting_id,
        speaker="AdsAgent",
        message="Meta Ads campaign drafted ($120/day) in PAUSED status targeting DE/AT freight forwarders.",
    )
    shared_memory.add_board_meeting_transcript(
        meeting_id=meeting_id,
        speaker="OutreachAgent",
        message="Personalized WhatsApp and email Touch 1 deployed. Follow-up scheduled in 3 days.",
    )

    concluded = shared_memory.conclude_board_meeting(
        meeting_id=meeting_id,
        action_plan="1. Monitor Outreach Touch 1 response. 2. Await Owen's manual authorization before Meta Ad set live activation.",
    )

    meeting_record = shared_memory.get_board_meeting_details(meeting_id)
    assert meeting_record["status"] == "concluded"
    assert len(meeting_record["transcript"]) == 4
    assert "Await Owen's manual authorization" in meeting_record["action_plan"]
