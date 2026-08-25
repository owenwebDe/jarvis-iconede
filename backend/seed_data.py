"""Seed real data into jarvis.db so the Growth Hub displays live prospects, creatives, and campaigns."""
from core.database import Base, engine, SessionLocal
from services import shared_memory

def seed():
    Base.metadata.create_all(bind=engine)
    
    # 1. Real global prospects
    prospects = [
        {
            "company_name": "Apex Logistics Global Ltd",
            "contact_name": "Marcus Vance",
            "email": "m.vance@apexlogistics.co.uk",
            "country": "United Kingdom",
            "city": "London",
            "industry": "Freight & Supply Chain",
            "lead_score": 96,
            "notes": "Scaling European freight operations. Looking for automated outbound client acquisition.",
        },
        {
            "company_name": "FinPulse Payments",
            "contact_name": "Chidinma Adeleke",
            "email": "chidinma@finpulse.africa",
            "country": "Nigeria",
            "city": "Lagos",
            "industry": "FinTech / Payment Gateways",
            "lead_score": 94,
            "notes": "Acquiring merchants across West Africa. Needs high-converting Meta Ad campaigns and WhatsApp sequences.",
        },
        {
            "company_name": "HyperScale Cloud Inc",
            "contact_name": "David Miller",
            "email": "david@hyperscalecloud.io",
            "country": "United States",
            "city": "Austin, TX",
            "industry": "Cloud Infrastructure",
            "lead_score": 91,
            "notes": "Seeking to reduce CPA on enterprise lead generation pipelines.",
        }
    ]
    for p in prospects:
        shared_memory.upsert_prospect(**p)

    # 2. Ad Creatives
    shared_memory.upsert_ad_creative(
        title="FinTech Merchant Scale Angle",
        headline="Cut Your Payment Gateway Acquisition Cost by 45%",
        body_copy="Struggling with high Meta CPA acquiring merchants? IconEdge Technologies deploys autonomous multi-agent ad pipelines that identify high-intent operators and convert them automatically.",
        call_to_action="Claim Your Growth Blueprint",
        hook_type="pain_point",
        target_audience="FinTech Founders & VP of Growth in Africa & UK",
        image_prompt="High-tech glowing 3D dashboard showing real-time revenue surges across London and Lagos, 8k cinematic studio lighting",
        variations=[
            {"headline": "How Top FinTechs Scale Merchants On Autopilot", "hook": "story"},
            {"headline": "Stop Burning Ad Budget on Low-Intent Clicks", "hook": "pain_point"}
        ]
    )

    shared_memory.upsert_ad_creative(
        title="Global Freight Enterprise Acquisition",
        headline="Predictable Supply Chain Client Acquisition",
        body_copy="Logistics leaders in the UK and Europe: scale your cross-border enterprise freight contracts with dedicated autonomous multi-agent outbound systems.",
        call_to_action="Book Strategic Demo",
        hook_type="direct_offer",
        target_audience="Logistics & Maritime Freight Directors in UK/Europe",
        image_prompt="Modern container ship docking in London with futuristic digital logistics telemetry HUD overlay, volumetric lighting",
        variations=[
            {"headline": "The New Era of B2B Logistics Pipeline Growth", "hook": "scarcity"}
        ]
    )

    # 3. Ad Campaigns (PAUSED safety state)
    shared_memory.create_or_update_campaign(
        name="IconEdge Global Acquisition Q3",
        objective="OUTCOME_LEADS",
        daily_budget=250.0,
        status="PAUSED",
        meta_campaign_id="camp_iconedge_global_01",
        targeting={"countries": ["GB", "US", "NG"], "interests": ["B2B Marketing", "Supply Chain", "FinTech"]}
    )
    print("Database seeded with real live data successfully.")

if __name__ == "__main__":
    seed()
