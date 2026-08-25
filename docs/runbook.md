# IconEdge JARVIS — Production Operations & Runbook

## 1. Quick Start & Launch

### 1.1 Backend Services
```bash
cd jarvis/backend
uv run uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 1.2 Frontend Operations Dashboard
```bash
cd jarvis/frontend
npm run dev
# Dashboard opens on http://localhost:3000
# Growth Hub available at: http://localhost:3000/growth
```

---

## 2. Multi-Model LLM Routing Pool & Friend Key Onboarding

The LLM Router (`services/llm_router.py`) cascades through 6 provider tiers:
1. **Groq** (`groq.llama-3.3-70b-versatile`) — Fast primary daily driver.
2. **Cerebras** (`cerebras.llama-3.3-70b`) — High-speed backup.
3. **SambaNova** (`sambanova.Meta-Llama-3.3-70B-Instruct`) — Overflow tier #1.
4. **Google Gemini** (`google.gemini-2.0-flash`) — Structured output tier.
5. **OpenRouter** (`openrouter.meta-llama/llama-3.3-70b-instruct`) — Multi-model aggregator.
6. **DeepSeek** (`deepseek.deepseek-chat`) — Heavy reasoning fallback.

### Adding Friend Keys Dynamically:
```bash
curl -X POST http://localhost:8000/api/llm-router/keys \
  -H "Content-Type: application/json" \
  -d '{"provider": "groq", "api_key": "gsk_...", "owner": "Friend_1"}'
```

### Check Pool Diagnostics:
```bash
curl http://localhost:8000/api/llm-router/status
```

---

## 3. Meta Ads & Marketing Safety Architecture

### Critical Safety Rules:
1. **All new campaigns are created in `PAUSED` state by default.**
   - No ad spend will be triggered automatically.
2. **Live Budget Activation requires explicit authorization:**
   - To unlock an ad campaign from `PAUSED` to `ACTIVE`, the confirmation code `CONFIRMED_BY_OWEN` is mandatory:
   ```bash
   # Via MCP Tool:
   meta_ads_activate_campaign(campaign_id="...", confirmation_code="CONFIRMED_BY_OWEN")
   ```

---

## 4. Meta Messenger Webhook & Social DMs

### Webhook Verification:
- **Callback URL**: `https://your-domain.com/api/meta/webhook`
- **Verify Token**: Configured in `.env` as `META_VERIFY_TOKEN` (default: `iconedge_meta_verify_token_2026`)
- **Subscription Fields**: `messages`, `messaging_postbacks`, `feed`

### Automated DM & Comment Flow:
1. Prospect DMs or comments on Facebook/Instagram.
2. `services/meta_messenger.py` evaluates intent and scores the lead (1-100).
3. The lead is automatically persisted to SQLite `ProspectModel`.
4. An immediate qualifying auto-reply or private DM is dispatched.

---

## 5. Specialist Agents Roster & Board Meetings

| Specialist Agent | Core Function | Shared Memory Tools |
|---|---|---|
| **LeadResearchAgent** | Worldwide prospect profiling & scoring | `prospect_save`, `prospect_search` |
| **CreativeAgent** | Direct response copy, 4 hook angles & AI image prompts | `ad_creative_save`, `ad_creative_list` |
| **AdsAgent** | Meta Ads campaign structure & audience targeting | `meta_ads_create_campaign`, `campaign_save` |
| **OutreachAgent** | WhatsApp Business & Email multi-touch sequences | `prospect_save`, `prospect_search` |
| **Jarvis (Orchestrator)** | Cross-agent synthesis & Executive Board Meetings | `board_meeting_start`, `board_meeting_conclude` |

### Convening a Board Meeting:
Jarvis summons the Growth Team to collaborate on a client acquisition brief:
```bash
POST /api/shared-memory/meetings
{
  "meeting_id": "meeting-client-growth",
  "title": "Client Acquisition Campaign",
  "agenda": "1. Prospect Research 2. Creative Angle 3. Ads Drafting",
  "participants": ["Jarvis", "LeadResearchAgent", "CreativeAgent", "AdsAgent", "OutreachAgent"]
}
```

---

## 6. Verification & Automated Test Commands

Run the full automated test suite:
```bash
cd jarvis/backend
uv run pytest tests/test_services/test_llm_router.py tests/test_routes/test_llm_router_routes.py tests/test_services/test_shared_memory.py tests/test_routes/test_shared_memory_routes.py tests/test_tools/test_meta_marketing.py tests/test_services/test_specialist_agents_pipeline.py tests/test_services/test_meta_messenger.py tests/test_routes/test_meta_webhooks_routes.py tests/test_e2e_production_simulation.py
```
*(All 29 tests pass with 100% success rate)*
