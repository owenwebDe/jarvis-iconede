import pytest
from core.database import Base, engine
from services import meta_messenger, shared_memory


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_webhook_verification_handshake():
    # 1. Valid handshake token
    challenge = meta_messenger.verify_webhook(
        mode="subscribe",
        token="iconedge_meta_verify_token_2026",
        challenge="CHALLENGE_STRING_12345",
    )
    assert challenge == "CHALLENGE_STRING_12345"

    # 2. Invalid token rejected
    bad_challenge = meta_messenger.verify_webhook(
        mode="subscribe",
        token="wrong_token",
        challenge="CHALLENGE_STRING_12345",
    )
    assert bad_challenge is None


def test_inbound_dm_lead_qualification():
    # 1. Inbound high-intent message
    result = meta_messenger.handle_inbound_dm(
        sender_id="fb_user_998877",
        message_text="Hi, what is the price and cost for your full Meta Ads agency management?",
    )
    assert result["is_high_intent"] is True
    assert result["lead_status"] == "qualified"
    assert result["lead_score"] == 85
    assert "Would you like a complimentary audit" in result["auto_reply_sent"]

    # Verify prospect was saved in shared memory SQLite database
    prospects = shared_memory.search_prospects(query="fb_user_998877")
    assert len(prospects) == 1
    assert prospects[0]["status"] == "qualified"
    assert prospects[0]["lead_score"] == 85


def test_post_comment_and_private_dm_flow():
    result = meta_messenger.handle_post_comment(
        comment_id="comment_554433",
        post_id="post_112233",
        commenter_id="user_john_doe",
        commenter_name="John Doe",
        comment_text="I need this for my ecommerce store! How do I get started?",
    )
    assert result["commenter_name"] == "John Doe"
    assert "sent you a private message" in result["public_reply"]
    assert "Saw your comment on our post" in result["private_dm"]

    # Verify commenter was created as a prospect in shared memory
    prospects = shared_memory.search_prospects(query="John Doe")
    assert len(prospects) >= 1
    assert prospects[0]["contact_name"] == "John Doe"


def test_webhook_payload_batch_processing():
    payload = {
        "object": "page",
        "entry": [
            {
                "id": "page_iconedge_01",
                "messaging": [
                    {
                        "sender": {"id": "fb_user_111"},
                        "message": {"text": "How does your lead generation system work?"},
                    }
                ],
                "changes": [
                    {
                        "field": "feed",
                        "value": {
                            "item": "comment",
                            "verb": "add",
                            "comment_id": "comment_888",
                            "post_id": "post_777",
                            "from": {"id": "user_222", "name": "Alice Smith"},
                            "message": "Interested in pricing info.",
                        },
                    }
                ],
            }
        ],
    }
    batch_res = meta_messenger.process_webhook_payload(payload)
    assert batch_res["status"] == "success"
    assert batch_res["count"] == 2
