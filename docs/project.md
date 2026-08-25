# IconEdge Multi-Agent System — "Jarvis" Build Reference
*Last updated: August 18, 2026*

---

## 1. Vision (in Owen's own words, formalized)

Build a JARVIS-style AI system for IconEdge Technologies:
- **One main/orchestrator agent** — talks to Owen (voice + chat), holds the big picture, assigns tasks to specialist agents, can call all sub-agents into a "board meeting" to coordinate on complex tasks.
- **Multiple specialist agents** — each handles one job (Facebook outreach, ad creative, lead research, DM replies, etc.)
- **Shared memory** — all agents pull from and write to one central memory/database, so switching LLM providers mid-task doesn't lose context.
- **Dashboard** — visual interface to see what each agent is doing, talk to Jarvis by voice, like Iron Man's JARVIS.
- **Zero/low budget** — powered by free-tier APIs from Owen + 8 friends, routed intelligently so no single key gets exhausted.

---

## 2. Recommended Foundation: Fork, Don't Build From Zero

**Base repo: `omnigentx/jarvis`** — https://github.com/omnigentx/jarvis

Why this fits almost exactly:
- MIT licensed, self-hosted, single-user — free to fork and modify for IconEdge
- Root "Jarvis" agent delegates tasks to sub-agents (research, finance, IoT, music, etc. in the demo — swap for outreach, creative, lead-research, DM-reply for IconEdge)
- Built-in **meeting-room protocol** + **inter-agent email bus** — this IS the "board meeting" feature Owen wants, already implemented
- Durable memory system (not just chat history) — facts persist across sessions
- Vue dashboard included — visual agent monitoring out of the box
- Uses Fast Agent (MCP) — meaning it can plug into Pipeboard's Meta Ads MCP, Meta Messenger API, and any other MCP server directly
- Skills = Markdown files with YAML frontmatter — matches how Owen already thinks in docs/specs

**Setup (from the repo):**
```bash
git clone --recurse-submodules https://github.com/omnigentx/jarvis.git
cd jarvis
cp backend/.env.example backend/.env
cp backend/fastagent.secrets.yaml.example backend/fastagent.secrets.yaml
# Edit both files with your API keys (Groq, DeepSeek, etc.)
```
Sessions, agent registry, and secrets live in SQLite under `backend/data/` — this is your shared memory layer, already built. No need to design a database schema from scratch.

**Voice interface note:** the repo is described as "voice + chat" — confirm exact voice stack (likely Whisper for speech-to-text + some TTS) once you clone it and read `AGENTS.md` inside the repo.

---

## 3. Meta APIs You Actually Need (three separate systems, not one)

Facebook/Meta does NOT have one unified "automation API." You need to combine three:

### A. Meta Marketing API (Ads)
- **What it does:** create/manage campaigns, ad sets, ads, creatives, budgets, targeting, performance insights
- **Access path:** Meta Business Manager account → Ad Account (`act_XXXXXXXXX`) → OAuth
- **Tool to use:** `pipeboard-co/meta-ads-mcp` (already found) — https://github.com/pipeboard-co/meta-ads-mcp
  - 42 MCP tools covering campaigns, creatives, targeting, insights
  - Licensed under Business Source License 1.1 — free to use/modify for IconEdge, becomes fully Apache 2.0 in 2029
  - Only restriction: can't resell as a competing hosted MCP service
  - New campaigns start PAUSED by default (safety) — real ad spend only happens on explicit confirmation

### B. Meta Messenger Platform API (DM auto-replies)
- **What it does:** auto-reply to Page DMs, handle comment-to-DM conversion, qualify leads conversationally
- **Access path:** Meta Developer App → `pages_messaging` permission → Page connection (separate from Ads OAuth)
- **Docs to read first:** https://developers.facebook.com/docs/messenger-platform
- **No ready-made open-source MCP found yet for this** — this is the piece IconEdge will likely have to build directly on Meta's API, OR use a paid layer like Chatfuel/ManyChat if the timeline is tight and budget allows later.

### C. Meta Graph API (Pages/Posts/Comments)
- **What it does:** publish posts, read/reply to public comments, manage Page content
- **Access path:** same Meta Developer App, `pages_manage_posts` + `pages_read_engagement` permissions
- **Docs:** https://developers.facebook.com/docs/graph-api

**Practical build order:**
1. Wire Pipeboard MCP into Jarvis first (fastest win, already exists)
2. Build a custom Messenger Platform MCP tool/skill for Jarvis (DM auto-reply agent)
3. Build a Graph API skill for post publishing + comment replies

---

## 4. Agent Roster (proposed roles inside Jarvis)

| Agent | Job | Primary Tools/MCP |
|---|---|---|
| **Jarvis (orchestrator)** | Talks to Owen, assigns tasks, runs board meetings between agents, holds high-level strategy | All MCP servers, memory system |
| **Outreach Agent** | Multi-channel cold outreach (WhatsApp/Email/Social) to global prospects, follow-ups | WhatsApp Business API, Email/SMTP, memory of prospect list |
| **Creative Agent** | Ad copy, captions, A/B variations, image gen prompts | Groq/DeepSeek for text, Flux/Together for images |
| **Ads Agent** | Campaign creation, budget management, performance analysis | Pipeboard Meta Ads MCP |
| **DM/Comment Agent** | Auto-reply to Messenger DMs and Page comments, lead qualification | Meta Messenger Platform API, Graph API |
| **Lead Research Agent** | Finds, enriches, and profiles global SMB & enterprise prospects | Web search, Google Places / Maps, LinkedIn / B2B enrichment tools |

*This matches Owen's original CrewAI/AutoGen/LangGraph plan from earlier — Jarvis's Fast Agent/MCP architecture can absorb that same role structure without needing those frameworks separately.*

---

## 5. Friend API Key Roster (fill in as friends sign up)

Assign ONE provider per friend to avoid pattern-flagging as coordinated multi-accounting. Track status here:

| # | Friend Name | Provider Assigned | Signup Status | Key Stored? | Notes |
|---|---|---|---|---|---|
| 1 | Owen (primary) | Groq | ☐ | ☐ | Primary daily driver |
| 2 | | DeepSeek | ☐ | ☐ | 5M token grant, 30-day window |
| 3 | | Google Gemini (AI Studio) | ☐ | ☐ | Backup, structured output |
| 4 | | Cerebras | ☐ | ☐ | Fast inference backup |
| 5 | | SambaNova Cloud | ☐ | ☐ | Overflow #2 |
| 6 | | OpenRouter | ☐ | ☐ | Multi-model aggregator |
| 7 | | Hugging Face | ☐ | ☐ | Image gen backup |
| 8 | | (Groq #2 or Cerebras #2) | ☐ | ☐ | Extra overflow for whichever hits limits first |

**Key storage rule:** never hardcode in scripts. Store in `backend/fastagent.secrets.yaml` (Jarvis's own secrets file) or a `.env` — never commit to a public GitHub repo.

**Router logic (already planned):** Groq → Cerebras → SambaNova → OpenRouter → DeepSeek (paid fallback once free options exhausted). Jarvis's Fast Agent architecture should support multi-model routing per the "LLM Engine: multi-model routing" pattern seen in JARVIS OS references.

---

## 6. Honest Risk Notes (don't skip this section)

- **Multi-account free-tier stacking** — most providers' ToS technically discourage this. Low risk at small scale, but don't scale usage patterns that look automated/bot-like across the 8 keys. Budget to migrate to one paid IconEdge account once real client revenue comes in.
- **Meta API access requires a real Business Manager + verified Page** — this isn't optional. Both the Ads MCP and Messenger API need this set up per client (or under an agency-delegated access model).
- **Scraping-based "automation" tools are a trap** — anything using Selenium/pyautogui to fake browser actions violates Facebook's ToS and risks client page bans. Stick to official Graph API / Marketing API / Messenger API paths only.
- **Hardware constraint** — Jarvis's voice interface and multi-agent orchestration will be noticeably better on a stronger laptop. This ties into the EasyBuy Nigeria financing plan already in motion — worth prioritizing.

---

## 7. Next Steps (in order)

1. Clone `omnigentx/jarvis`, read `AGENTS.md` inside the repo fully before writing any code
2. Get Groq + DeepSeek keys wired in first (2 providers, prove the pipeline works end-to-end)
3. Wire in Pipeboard Meta Ads MCP as first tool
4. Build one working agent (Creative Agent) end-to-end before adding the rest
5. Onboard friends' API keys one at a time, testing the router fallback after each addition
6. Build Messenger Platform integration once ads + creative loop is stable
7. Dashboard customization (Jarvis's existing Vue dashboard) — rebrand for IconEdge last, after function is proven