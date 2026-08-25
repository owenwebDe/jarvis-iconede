import pytest
from core.database import Base, engine
from tools import meta_marketing_server
from services import shared_memory


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_meta_ads_get_ad_account():
    result = meta_marketing_server.meta_ads_get_ad_account("123456789")
    assert "ad_account_id" in result
    assert result["ad_account_id"] == "act_123456789"
    assert result["account_status"] == "ACTIVE"


def test_meta_ads_create_campaign_safety_paused():
    # Attempt to create campaign
    result = meta_marketing_server.meta_ads_create_campaign(
        ad_account_id="act_987654321",
        name="Global B2B Lead Acquisition",
        objective="OUTCOME_LEADS",
        daily_budget_dollars=75.0,
    )
    assert result["name"] == "Global B2B Lead Acquisition"
    # STRICT SAFETY RULE CHECK
    assert result["delivery_status"] == "PAUSED"
    assert "safety_note" in result
    assert "No spend will occur" in result["safety_note"]

    # Verify campaign was synced to shared memory in PAUSED state
    campaigns = shared_memory.list_campaigns(status="PAUSED")
    assert any(c["name"] == "Global B2B Lead Acquisition" for c in campaigns)


def test_meta_ads_search_targeting():
    result = meta_marketing_server.meta_ads_search_targeting(
        ad_account_id="act_987654321",
        query="logistics",
    )
    assert "results" in result
    assert len(result["results"]) >= 1
    assert "Logistics" in result["results"][0]["name"]


def test_meta_ads_get_insights():
    result = meta_marketing_server.meta_ads_get_insights(
        ad_account_id="act_987654321",
        date_preset="last_7d",
    )
    assert "metrics" in result
    assert "spend" in result["metrics"]
    assert "leads" in result["metrics"]
    assert "ctr" in result["metrics"]


def test_meta_ads_activation_safety_guard():
    # 1. Invalid confirmation code should be REJECTED
    rejected = meta_marketing_server.meta_ads_activate_campaign(
        ad_account_id="act_987654321",
        campaign_id="camp_apex_001",
        confirmation_code="ACTIVATE_NOW",
    )
    assert "error" in rejected
    assert "Activation rejected" in rejected["error"]

    # 2. Valid authorization code should succeed
    approved = meta_marketing_server.meta_ads_activate_campaign(
        ad_account_id="act_987654321",
        campaign_id="camp_apex_001",
        confirmation_code="CONFIRMED_BY_OWEN",
    )
    assert approved["status"] == "active_sandbox"
    assert approved["delivery_status"] == "ACTIVE"
