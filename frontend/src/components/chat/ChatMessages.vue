<script setup>
import { ref, watch, nextTick, computed, reactive } from 'vue'
import { useBreakpoint } from '../../composables/useBreakpoint'
import { parseYoutubeTags, youtubeEmbedUrl } from '../../utils/youtubeTags'
import { normalizeTs } from '../../utils/timeFormat.js'
import { useVoiceSession } from '../../composables/useVoiceSession.js'
import { useLang } from '../../composables/useLang'
import { useChatStore } from '../../stores/chat'
import MarkdownRenderer from '../MarkdownRenderer.vue'
import MemoryIcon from './MemoryIcon.vue'

/**
 * ChatMessages — restyled to match design tokens.
 *
 * Bubble system:
 *   - User: var(--bg-3) bg, plain border, right-aligned, avatar 'U'
 *   - Jarvis: var(--primary-bg) bg, var(--primary-bg-strong) border,
 *             left-aligned, avatar 'J' (indigo gradient)
 *   - STT streaming (user-side): cyan blinking caret '|' at message tail
 *   - TTS streaming (jarvis-side): 3 indigo wave dots at message tail
 *   - Interrupted (jarvis-side): warning border + INTERRUPTED chip badge
 *   - Barge-in (user-side, after interrupt): cyan BARGE-IN chip above bubble
 *
 * Streaming flags come from existing chatStore.message.isStreaming + the
 * voice session's wasInterrupted reactive. Voice composable is unmodified —
 * we only consume its state.
 */

const props = defineProps({
  messages: { type: Array, default: () => [] },
  agent: { type: Object, default: null },
  isStreaming: { type: Boolean, default: false },
})

const scrollContainer = ref(null)
const expandedTools = reactive({})
const expandedRows = reactive({})
const { isMobile } = useBreakpoint()
const voice = useVoiceSession()
const { t } = useLang()
const chat = useChatStore()

// ── Memory-SAVED chip (live capture: auto-saved or pending approval) ──
// Distinct from the recall chip: blocks carry `isMemorySaved` + a `memorySaved`
// array of {candidateId, content, memoryType, status, recordId}. Rejected items
// are hidden; counts drive the collapsed summary.
function savedVisible(msg) { return (msg.memorySaved || []).filter(it => it.status !== 'rejected') }
function savedCount(msg, status) { return (msg.memorySaved || []).filter(it => it.status === status).length }

function toggleTools(msgId) { expandedTools[msgId] = !expandedTools[msgId] }
function toggleRow(msgId, idx) { expandedRows[`${msgId}-${idx}`] = !expandedRows[`${msgId}-${idx}`] }
function isRowExpanded(msgId, idx) { return !!expandedRows[`${msgId}-${idx}`] }

// ── Memory-used chip (auto-injected recall block) ──
// The retrieval hook injects a message tagged with this marker. Instead of
// rendering it as a raw user bubble, we collapse it into a subtle chip with an
// expandable list of the recalled excerpts. Marker mirrors
// services/memory/retrieval_hook.MEMORY_MARKER.
const MEMORY_MARKER = '⟦memory:recalled⟧'
const expandedMemory = reactive({})
const memLabel = computed(() => t('chat.memoryUsed'))
function isMemoryBlock(msg) {
  return msg.role === 'user' && typeof msg.content === 'string' && msg.content.includes(MEMORY_MARKER)
}
function memoryLines(msg) {
  return String(msg.content || '')
    .split('\n')
    .filter((l) => l.trim().startsWith('- '))
    .map((l) => l.replace(/^\s*-\s*/, ''))
}
function toggleMemory(msgId) { expandedMemory[msgId] = !expandedMemory[msgId] }

// Lane provenance per recalled line (fts/dense/graph). Comes from the backend
// `recall_lanes` field — ONE list per line, SAME ORDER as memoryLines — which
// rides the recall block's persisted channel, so it's correct on reload (not a
// live-only signal). Empty for blocks recalled before this shipped.
function laneFor(msg, i) { return (msg.recallLanes && msg.recallLanes[i]) || [] }
// How many recalled memories the graph (MENTIONS) lane surfaced for this block.
function memoryGraphCount(msg) {
  return (msg.recallLanes || []).filter((ls) => Array.isArray(ls) && ls.includes('graph')).length
}

// RAW retrieval scores per line: { rel (RRF match score), conf (fact-truth),
// authority }. Shown as-is (no %) — the unit is opaque on purpose; a reader who
// cares learns it. Null for blocks recalled before this shipped.
const VERIFIED_AUTHORITIES = ['user_confirmed', 'tool_verified']
function scoreFor(msg, i) { return (msg.recallScores && msg.recallScores[i]) || null }
function isVerified(s) { return !!s && VERIFIED_AUTHORITIES.includes(s.authority) }
// Show rrf (lane fusion) and rerank (cross-encoder) SEPARATELY — they answer
// different questions and diverge a lot (rerank ~1.0 on a near-verbatim restate).
// `rel` fallback keeps any pre-split cached block rendering until its next reload.
function scoreLabel(s) {
  if (!s) return ''
  const p = []
  if (s.rrf != null) p.push(`rrf ${s.rrf}`)
  if (s.rerank != null) p.push(`rerank ${s.rerank}`)
  if (s.rrf == null && s.rerank == null && s.rel != null) p.push(`score ${s.rel}`)
  if (s.conf != null) p.push(`conf ${s.conf}`)
  return p.join(' · ')
}

// Auto-scroll to bottom on new messages
watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
    }
  }
)

// Track previous interrupt state so we know which user bubble is the
// "barge-in" one (= the most recent user message added right around a
// wasInterrupted flip). Cheap, presentation-only.
const lastBargeUserMsgId = ref(null)
watch(
  () => voice.wasInterrupted.value,
  (now, prev) => {
    if (now && !prev) {
      // Find most recent user message — mark it as the barge-in turn.
      for (let i = props.messages.length - 1; i >= 0; i--) {
        if (props.messages[i].role === 'user') {
          lastBargeUserMsgId.value = props.messages[i].id
          break
        }
      }
    }
  },
)

// Per-message INTERRUPTED flag (set by chatStore.markMessageInterrupted
// when the LLM-in-progress placeholder gets cancelled mid-generation —
// see useVoiceSession.js ``tts_interruption`` handler). Was previously
// derived from ``voice.wasInterrupted`` (a single global ref) + last
// assistant message id, which tagged the wrong bubble whenever a barge-in
// happened *after* the LLM had already finalised (Case B — only TTS was
// cancelled, the message itself was complete).
function isInterrupted(msg) {
  return msg.role === 'assistant' && msg.isInterrupted === true
}

function isBargeIn(msg) {
  return msg.role === 'user' && msg.id === lastBargeUserMsgId.value
}

const agentInitials = computed(() => {
  if (!props.agent?.name) return '?'
  return props.agent.name
    .split(/[\s_-]+/)
    .map(w => w[0]?.toUpperCase() || '')
    .join('')
    .slice(0, 2)
})

function formatTime(ts) {
  const ms = normalizeTs(ts)
  if (ms === null) return ''
  const d = new Date(ms)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return t('chat.justNow')
  if (diff < 3600000) return t('chat.minutesAgo', { n: Math.floor(diff / 60000) })
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function groupToolCalls(toolCalls) {
  if (!toolCalls?.length) return []
  const grouped = []
  for (const tc of toolCalls) {
    if (tc.isResult) {
      const match = [...grouped].reverse().find(g => g.tool === tc.tool && !g.duration)
      if (match) {
        match.duration = tc.duration
        match.status = 'done'
        match.resultPreview = tc.resultPreview || null
        continue
      }
    }
    grouped.push({
      tool: tc.tool || 'tool',
      duration: tc.duration || null,
      status: tc.isResult ? 'done' : (tc.status || 'running'),
      args: tc.args || null,
      resultPreview: tc.resultPreview || null,
    })
  }
  return grouped
}

function hasDetail(g) {
  return (g.args && Object.keys(g.args).length > 0) || g.resultPreview
}

function totalDuration(toolCalls) {
  const groups = groupToolCalls(toolCalls)
  if (!groups.length) return ''
  let total = 0
  for (const g of groups) {
    if (g.duration) total += parseFloat(g.duration) || 0
  }
  return total === 0 ? '' : `${total.toFixed(1)}s`
}

function toolCount(toolCalls) { return groupToolCalls(toolCalls).length }

function getToolIcon(tool) {
  if (!tool) return 'terminal'
  const t = tool.toLowerCase()
  if (t.includes('agent')) return 'agent'
  if (t.includes('search') || t.includes('serpapi') || t.includes('brave')) return 'search'
  if (t.includes('read') || t.includes('file') || t.includes('write')) return 'file'
  return 'terminal'
}

function formatToolName(tool) {
  if (!tool) return 'tool'
  if (tool.includes('agent__')) return tool.replace('agent__', '')
  return tool.replace(/__/g, ' › ')
}

function parsedAgentContent(content) {
  return parseYoutubeTags(content)
}

// ── Multi-Agent Board Meeting Helpers ─────────────────────────────────────
const AGENT_BADGES = {
  Jarvis: { emoji: '🛡️', role: 'Executive Lead', color: '#6366f1' },
  LeadResearchAgent: { emoji: '🎯', role: 'Lead Discovery', color: '#38bdf8' },
  CreativeAgent: { emoji: '🎨', role: 'Brand & Copywriting', color: '#f43f5e' },
  OutreachAgent: { emoji: '📨', role: 'Cold Outreach', color: '#a855f7' },
  AdsAgent: { emoji: '📊', role: 'Meta Ads Optimization', color: '#ec4899' },
  FinanceAgent: { emoji: '💰', role: 'Financial Analysis', color: '#eab308' },
  ResearchAgent: { emoji: '🔬', role: 'Market Intelligence', color: '#06b6d4' },
  AudioReaderAgent: { emoji: '🎧', role: 'Storyteller', color: '#10b981' },
  CrawlStoriesAgent: { emoji: '🕸️', role: 'Web Crawler', color: '#84cc16' },
  PersonalAgent: { emoji: '👔', role: 'Productivity', color: '#f97316' },
  IoTAgent: { emoji: '⚡', role: 'Smart Office & IoT', color: '#14b8a6' },
  MusicAgent: { emoji: '🎵', role: 'Soundtracks', color: '#8b5cf6' },
}

function getAgentMeta(name) {
  if (!name) return { emoji: '🤖', role: 'Specialist Agent', color: '#6366f1' }
  const clean = String(name).replace(/[^a-zA-Z0-9]/g, '')
  for (const [k, v] of Object.entries(AGENT_BADGES)) {
    if (clean.toLowerCase().includes(k.toLowerCase())) return v
  }
  return { emoji: '🤖', role: 'Specialist Agent', color: '#6366f1' }
}

function isBoardMeetingTool(tool) {
  return typeof tool === 'string' && tool.includes('board_meeting')
}

function hasBoardMeeting(toolCalls) {
  return (toolCalls || []).some(tc => isBoardMeetingTool(tc.tool))
}

function getBoardMeetingInfo(toolCalls) {
  const groups = groupToolCalls(toolCalls)
  let title = 'Executive Board Meeting'
  let agenda = 'Strategic Planning & Inter-Agent Coordination'
  let meetingId = ''
  let participants = []

  for (const g of groups) {
    if (g.tool?.includes('board_meeting_start') && g.args) {
      if (g.args.title) title = g.args.title
      if (g.args.topic && !g.args.title) title = g.args.topic
      if (g.args.agenda) agenda = g.args.agenda
      if (g.args.meeting_id) meetingId = g.args.meeting_id
      const p = g.args.participants || g.args.participants_json || g.args.agents
      if (Array.isArray(p)) participants = p
      else if (typeof p === 'string') {
        try {
          const parsed = JSON.parse(p)
          participants = Array.isArray(parsed) ? parsed : [p]
        } catch {
          participants = p.split(',').map(x => x.trim())
        }
      }
    }
  }

  for (const g of groups) {
    if (g.tool?.includes('board_meeting_speak') && g.args) {
      const spk = g.args.speaker || g.args.agent
      if (spk && !participants.includes(spk)) {
        participants.push(spk)
      }
      if (g.args.meeting_id && !meetingId) {
        meetingId = g.args.meeting_id
      }
    }
    if (g.tool?.includes('board_meeting_conclude') && g.args?.meeting_id) {
      if (!meetingId) meetingId = g.args.meeting_id
    }
  }

  if (!participants.length) {
    participants = ['Jarvis', 'LeadResearchAgent', 'CreativeAgent']
  }

  return { title, agenda, meetingId, participants }
}

function getBoardMeetingTurns(toolCalls) {
  const groups = groupToolCalls(toolCalls)
  const turns = []
  let idx = 1
  for (const g of groups) {
    if (g.tool?.includes('board_meeting_speak') && g.args) {
      const speaker = g.args.speaker || g.args.agent || 'Specialist Agent'
      const message = g.args.message || g.args.statement || g.args.proposal || ''
      if (message) {
        turns.push({
          speaker,
          message,
          turnIndex: idx++,
          duration: g.duration,
        })
      }
    }
  }
  return turns
}

function getBoardMeetingConclusion(toolCalls) {
  const groups = groupToolCalls(toolCalls)
  for (const g of groups) {
    if (g.tool?.includes('board_meeting_conclude') && g.args) {
      return g.args.action_plan || g.args.summary || g.resultPreview || 'Action plan agreed and finalized.'
    }
  }
  return null
}

function getStandardToolCalls(toolCalls) {
  return (toolCalls || []).filter(tc => !isBoardMeetingTool(tc.tool))
}
</script>

<template>
  <div
    ref="scrollContainer"
    data-testid="chat-messages"
    class="msgs-scroll"
    :class="{ 'is-mobile': isMobile }"
  >
    <!-- Empty state -->
    <div v-if="!messages.length && !isStreaming" class="empty-state">
      <div class="empty-jarvis-icon">
        <div class="empty-ring empty-ring-1"></div>
        <div class="empty-ring empty-ring-2"></div>
        <div class="empty-core">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8" y1="23" x2="16" y2="23"/>
          </svg>
        </div>
      </div>
      <div class="empty-brand">JARVIS</div>
      <div class="empty-title">{{ t('chat.startConversation') }}</div>
      <div class="empty-sub">
        {{ t('chat.emptySub', { name: agent?.name || t('chat.anAgent') }) }}
      </div>
      <div class="empty-hints">
        <span class="empty-hint">Try: "Find leads in Abuja"</span>
        <span class="empty-hint">Try: "Build me a demo website"</span>
        <span class="empty-hint">Try: "Send WhatsApp to prospects"</span>
      </div>
    </div>

    <div class="msgs-stack">
      <template v-for="msg in messages" :key="msg.id">
        <!-- ── MEMORY-USED CHIP (auto-injected recall block) ───────────── -->
        <div v-if="isMemoryBlock(msg)" class="row row-memory">
          <button class="memory-chip" @click="toggleMemory(msg.id)">
            <MemoryIcon class="mc-icon" />
            {{ memoryLines(msg).length }} {{ memLabel }}
            <span v-if="memoryGraphCount(msg)" class="lane lane-graph"
                  :title="t('memory.lane.graph')">graph {{ memoryGraphCount(msg) }}</span>
            <span class="mc-chevron" :class="{ expanded: !!expandedMemory[msg.id] }">▾</span>
          </button>
          <div v-if="expandedMemory[msg.id]" class="memory-detail">
            <div v-for="(line, i) in memoryLines(msg)" :key="i" class="memory-line">
              <span v-for="ln in laneFor(msg, i)" :key="ln" class="lane" :class="'lane-' + ln"
                    :title="t('memory.lane.' + ln)">{{ ln }}</span>
              {{ line }}
              <span v-if="scoreFor(msg, i)" class="mscore" :title="t('memory.scoreHint')">
                {{ scoreLabel(scoreFor(msg, i))
                }}<span v-if="isVerified(scoreFor(msg, i))" class="ok">✓</span>
              </span>
            </div>
          </div>
        </div>

        <!-- ── MEMORY-SAVED CHIP (live capture: auto-saved or pending) ──── -->
        <div v-else-if="msg.isMemorySaved" class="row row-memory">
          <button class="memory-chip" :class="savedCount(msg, 'pending') ? 'chip-pending' : 'chip-saved'"
                  @click="toggleMemory(msg.id)">
            <MemoryIcon class="mc-icon" />
            <span v-if="savedCount(msg, 'saved')">{{ savedCount(msg, 'saved') }} {{ t('memory.saved.remembered') }}</span>
            <span v-if="savedCount(msg, 'pending')">{{ savedCount(msg, 'saved') ? ' · ' : '' }}{{ savedCount(msg, 'pending') }} {{ t('memory.saved.pending') }}</span>
            <span class="mc-chevron" :class="{ expanded: !!expandedMemory[msg.id] }">▾</span>
          </button>
          <div v-if="expandedMemory[msg.id]" class="memory-detail">
            <div v-for="it in savedVisible(msg)" :key="it.candidateId" class="memory-line saved-line"
                 :class="{ archived: it.status === 'archived' }">
              <span class="mtype">[{{ it.memoryType }}]</span> {{ it.content }}
              <span class="saved-actions">
                <button v-if="it.status === 'saved'" class="s-btn ghost" @click="chat.archiveSavedMemory(it)">{{ t('memory.saved.undo') }}</button>
                <template v-else-if="it.status === 'pending'">
                  <button class="s-btn primary" @click="chat.approveSavedMemory(it)">{{ t('memory.saved.approve') }}</button>
                  <button class="s-btn ghost" @click="chat.rejectSavedMemory(it)">{{ t('memory.saved.reject') }}</button>
                </template>
                <span v-else-if="it.status === 'archived'" class="archived-tag">{{ t('memory.saved.archived') }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- ── USER MESSAGE ────────────────────────────────────────────── -->
        <div v-else-if="msg.role === 'user'" class="row row-user">
          <div class="bubble-wrap">
            <span v-if="isBargeIn(msg)" class="chip chip-bargein">
              <span class="chip-dot" /> {{ t('chat.bargeIn') }}
            </span>
            <div class="bubble bubble-user">
              <span class="bubble-text">{{ msg.content }}</span>
              <span v-if="msg.isStreaming" class="stt-caret" aria-hidden="true">|</span>
            </div>
            <div class="msg-time msg-time-right">{{ formatTime(msg.timestamp) }}</div>
          </div>
          <div class="ava ava-user">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
        </div>

        <!-- ── AGENT MESSAGE ──────────────────────────────────────────── -->
        <div v-else class="row row-jarvis">
          <div class="ava ava-jarvis">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
          </div>

          <div class="bubble-wrap">
            <div v-if="!msg.isStreaming" class="msg-meta">
              <span class="msg-agent">{{ agent?.name || 'Jarvis' }}</span>
              <span class="msg-time">{{ formatTime(msg.timestamp) }}</span>
            </div>

            <!-- Content bubble -->
            <div
              v-if="msg.content || msg.isStreaming"
              class="bubble bubble-jarvis"
              :class="{
                'bubble-error': msg.isError,
                'bubble-interrupted': isInterrupted(msg),
              }"
            >
              <!-- Thinking placeholder (no content yet) -->
              <div v-if="msg.isStreaming && !msg.content" class="typing-row">
                <span class="typing-dot" />
                <span class="typing-dot" />
                <span class="typing-dot" />
              </div>
              <template v-else>
                <MarkdownRenderer
                  :content="parsedAgentContent(msg.content).text"
                  content-type="markdown"
                />
                <!-- TTS streaming indicator (Jarvis is speaking) -->
                <span v-if="msg.isStreaming" class="tts-wave" aria-hidden="true">
                  <span class="tts-dot" />
                  <span class="tts-dot" />
                  <span class="tts-dot" />
                </span>
              </template>

              <!-- Interrupted badge -->
              <div v-if="isInterrupted(msg)" class="interrupted-strip">
                <span class="chip chip-interrupted">◼ {{ t('chat.interrupted') }}</span>
              </div>
            </div>

            <!-- YouTube embeds -->
            <div
              v-for="videoId in parsedAgentContent(msg.content).videoIds"
              :key="videoId"
              class="yt-embed"
              data-testid="chat-youtube-embed"
            >
              <iframe
                :src="youtubeEmbedUrl(videoId)"
                :data-video-id="videoId"
                title="YouTube video player"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                referrerpolicy="strict-origin-when-cross-origin"
                allowfullscreen
              ></iframe>
            </div>

            <!-- ── EXECUTIVE BOARD MEETING LIVE INTER-AGENT CARD ── -->
            <div v-if="hasBoardMeeting(msg.toolCalls)" class="boardroom-card">
              <div class="boardroom-header">
                <div class="boardroom-header-top">
                  <div class="boardroom-badge">
                    <span class="boardroom-live-dot"></span>
                    <span class="boardroom-badge-text">EXECUTIVE BOARD MEETING</span>
                  </div>
                  <router-link
                    v-if="getBoardMeetingInfo(msg.toolCalls).meetingId"
                    :to="`/meetings?id=${getBoardMeetingInfo(msg.toolCalls).meetingId}`"
                    class="boardroom-open-btn"
                  >
                    <span>Full Boardroom</span>
                    <svg width="10" height="10" viewBox="0 0 16 16" fill="none">
                      <path d="M4 12L12 4M12 4H6M12 4V10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </router-link>
                </div>
                
                <h4 class="boardroom-title">{{ getBoardMeetingInfo(msg.toolCalls).title }}</h4>
                <p v-if="getBoardMeetingInfo(msg.toolCalls).agenda" class="boardroom-agenda">
                  <span class="agenda-tag">AGENDA</span> {{ getBoardMeetingInfo(msg.toolCalls).agenda }}
                </p>

                <!-- Participants Roster -->
                <div class="boardroom-roster">
                  <div
                    v-for="agentName in getBoardMeetingInfo(msg.toolCalls).participants"
                    :key="agentName"
                    class="roster-chip"
                    :style="{
                      borderColor: getAgentMeta(agentName).color + '44',
                      background: getAgentMeta(agentName).color + '14',
                    }"
                  >
                    <span class="roster-emoji">{{ getAgentMeta(agentName).emoji }}</span>
                    <span class="roster-name" :style="{ color: getAgentMeta(agentName).color }">{{ agentName }}</span>
                    <span class="roster-role">{{ getAgentMeta(agentName).role }}</span>
                  </div>
                </div>
              </div>

              <!-- Live Deliberation Turns -->
              <div class="boardroom-turns" v-if="getBoardMeetingTurns(msg.toolCalls).length">
                <div
                  v-for="(turn, idx) in getBoardMeetingTurns(msg.toolCalls)"
                  :key="idx"
                  class="boardroom-speech-card"
                  :style="{ borderLeftColor: getAgentMeta(turn.speaker).color }"
                >
                  <div class="speech-header">
                    <div class="speech-speaker-row">
                      <span class="speech-avatar">{{ getAgentMeta(turn.speaker).emoji }}</span>
                      <span class="speech-speaker-name" :style="{ color: getAgentMeta(turn.speaker).color }">
                        {{ turn.speaker }}
                      </span>
                      <span class="speech-speaker-role">
                        {{ getAgentMeta(turn.speaker).role }}
                      </span>
                    </div>
                    <span class="speech-turn-pill">Turn {{ turn.turnIndex }}</span>
                  </div>
                  <div class="speech-body">
                    <MarkdownRenderer :content="turn.message" content-type="markdown" />
                  </div>
                </div>
              </div>

              <!-- Final Concluded Action Plan -->
              <div v-if="getBoardMeetingConclusion(msg.toolCalls)" class="boardroom-conclusion">
                <div class="conclusion-title">
                  <span class="conclusion-icon">📋</span>
                  <span>AGREED STRATEGIC ACTION PLAN</span>
                </div>
                <div class="conclusion-content">
                  <MarkdownRenderer :content="getBoardMeetingConclusion(msg.toolCalls)" content-type="markdown" />
                </div>
              </div>
            </div>

            <!-- Standard Tool calls (non-board meeting) -->
            <div v-if="getStandardToolCalls(msg.toolCalls)?.length" class="tc-section">
              <button class="tc-header" @click="toggleTools(msg.id)">
                <span class="tc-header-left">
                  <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
                    <path d="M9.77 4.23a4 4 0 0 1 2 3.27 4 4 0 0 1-1.15 3.12L6.5 14.74a1.5 1.5 0 0 1-2.12 0l-.12-.12a1.5 1.5 0 0 1 0-2.12l4.12-4.12A4 4 0 0 1 9.77 4.23z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <span class="tc-summary">
                    {{ t('chat.toolsUsed', { n: toolCount(getStandardToolCalls(msg.toolCalls)) }) }}
                  </span>
                  <span v-if="totalDuration(getStandardToolCalls(msg.toolCalls))" class="tc-duration-label">
                    · {{ totalDuration(getStandardToolCalls(msg.toolCalls)) }}
                  </span>
                </span>
                <svg
                  :class="['tc-chevron', { expanded: expandedTools[msg.id] }]"
                  width="12" height="12" viewBox="0 0 16 16" fill="none"
                >
                  <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <transition name="tc-expand">
                <div v-if="expandedTools[msg.id]" class="tc-list">
                  <div
                    v-for="(g, idx) in groupToolCalls(getStandardToolCalls(msg.toolCalls))"
                    :key="idx"
                    class="tc-entry"
                  >
                    <div
                      :class="['tc-row', { 'tc-row-clickable': hasDetail(g) }]"
                      @click="hasDetail(g) && toggleRow(msg.id, idx)"
                    >
                      <div class="tc-icon">
                        <svg v-if="getToolIcon(g.tool) === 'agent'" width="12" height="12" viewBox="0 0 16 16" fill="none">
                          <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM3 14c0-2.8 2.2-5 5-5s5 2.2 5 5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                        </svg>
                        <svg v-else-if="getToolIcon(g.tool) === 'search'" width="12" height="12" viewBox="0 0 16 16" fill="none">
                          <circle cx="7" cy="7" r="4" stroke="currentColor" stroke-width="1.2"/>
                          <path d="M10 10l3.5 3.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                        </svg>
                        <svg v-else width="12" height="12" viewBox="0 0 16 16" fill="none">
                          <rect x="1.5" y="2.5" width="13" height="11" rx="2" stroke="currentColor" stroke-width="1.2"/>
                          <path d="M5 7l2 2-2 2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                          <path d="M9 11h3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                        </svg>
                      </div>
                      <span class="tc-name">{{ formatToolName(g.tool) }}</span>
                      <div class="tc-row-right">
                        <span v-if="g.duration" class="tc-dur">{{ g.duration }}</span>
                        <svg v-if="g.status === 'done'" width="14" height="14" viewBox="0 0 16 16" fill="none">
                          <path d="M4.5 8.5L7 11l4.5-5" stroke="var(--success)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <div v-else class="tc-spinner"></div>
                        <svg
                          v-if="hasDetail(g)"
                          :class="['tc-row-chevron', { expanded: isRowExpanded(msg.id, idx) }]"
                          width="10" height="10" viewBox="0 0 16 16" fill="none"
                        >
                          <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                      </div>
                    </div>
                    <transition name="tc-expand">
                      <div v-if="isRowExpanded(msg.id, idx)" class="tc-detail">
                        <div v-if="g.args && Object.keys(g.args).length" class="tc-detail-block">
                          <div class="tc-detail-label">{{ t('chat.arguments') }}</div>
                          <div class="tc-detail-args">
                            <div v-for="(val, key) in g.args" :key="key" class="tc-arg-row">
                              <span class="tc-arg-key">{{ key }}</span>
                              <span class="tc-arg-val">{{ val }}</span>
                            </div>
                          </div>
                        </div>
                        <div v-if="g.resultPreview" class="tc-detail-block">
                          <div class="tc-detail-label">{{ t('chat.result') }}</div>
                          <div class="tc-detail-result">
                            <MarkdownRenderer
                              :content="g.resultPreview"
                              content-type="markdown"
                              :enable-mermaid="false"
                            />
                          </div>
                        </div>
                      </div>
                    </transition>
                  </div>
                </div>
              </transition>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.msgs-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 28px 36px 20px;
  background: var(--bg-0);
  scroll-behavior: smooth;
}
.msgs-scroll.is-mobile { padding: 16px 14px; }

.msgs-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 780px;
  margin: 0 auto;
  width: 100%;
}

/* ── Empty state ────────────────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
  text-align: center;
  gap: 8px;
  padding-bottom: 80px;
}
.empty-jarvis-icon {
  position: relative;
  width: 96px; height: 96px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 8px;
}
.empty-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(99,102,241,0.15);
}
.empty-ring-1 {
  width: 96px; height: 96px;
  animation: empty-ring-rotate 12s linear infinite;
  border-style: dashed;
  border-color: rgba(99,102,241,0.2);
}
.empty-ring-2 {
  width: 72px; height: 72px;
  border-color: rgba(34,211,238,0.15);
  animation: empty-ring-rotate 8s linear infinite reverse;
}
@keyframes empty-ring-rotate { to { transform: rotate(360deg); } }
.empty-core {
  width: 48px; height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(34,211,238,0.1));
  border: 1px solid rgba(99,102,241,0.3);
  display: flex; align-items: center; justify-content: center;
  color: var(--primary-hover);
  box-shadow: 0 0 30px rgba(99,102,241,0.15);
}
.empty-brand {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.35em;
  color: var(--primary-hover);
  opacity: 0.7;
  margin-bottom: 4px;
}
.empty-title { font-size: 17px; font-weight: 700; color: var(--text); letter-spacing: -0.01em; }
.empty-sub { font-size: 13px; color: var(--text-muted); max-width: 360px; line-height: 1.5; }
.empty-hints {
  display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
  margin-top: 12px;
}
.empty-hint {
  padding: 5px 12px;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--r-full);
  font-size: 11.5px;
  color: var(--text-dim);
  transition: all 0.15s ease;
  cursor: default;
}
.empty-hint:hover {
  border-color: var(--primary-bg-strong);
  color: var(--primary-hover);
  background: var(--primary-bg);
}

/* ── Row layout ─────────────────────────────────────────────────────── */
.row { display: flex; gap: 12px; align-items: flex-start; }
.row-user { flex-direction: row-reverse; }
.bubble-wrap { display: flex; flex-direction: column; min-width: 0; max-width: 80%; }

/* ── Avatars ────────────────────────────────────────────────────────── */
.ava {
  flex-shrink: 0;
  width: 34px; height: 34px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  margin-top: 2px;
}
.ava-user {
  background: var(--bg-3);
  color: var(--text-dim);
  border: 1px solid var(--border-strong);
}
.ava-jarvis {
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: white;
  box-shadow: 0 2px 8px rgba(99,102,241,0.3);
}

/* ── Bubbles ────────────────────────────────────────────────────────── */
.bubble {
  padding: 12px 16px;
  border-radius: var(--r-lg);
  font-size: 13.5px;
  line-height: 1.6;
  color: var(--text);
  position: relative;
  word-break: break-word;
}
.bubble-text { white-space: pre-wrap; }

.bubble-user {
  background: var(--bg-3);
  border: 1px solid var(--border-strong);
  border-top-right-radius: 4px;
}
.bubble-jarvis {
  background: var(--primary-bg);
  border: 1px solid var(--primary-bg-strong);
  border-top-left-radius: 4px;
}
.bubble-error { color: var(--danger); border-color: rgba(239, 68, 68, 0.35); }
.bubble-interrupted { border-color: var(--warning); border-width: 1px; }

/* ── STT caret (user is speaking, message still streaming via STT) ── */
.stt-caret {
  display: inline-block;
  margin-left: 2px;
  font-family: var(--font-mono);
  color: var(--accent);
  font-weight: 600;
  vertical-align: -2px;
  animation: stt-blink 1s steps(2, end) infinite;
}
@keyframes stt-blink {
  0%, 50% { opacity: 1; }
  50.01%, 100% { opacity: 0; }
}

/* ── TTS wave dots (Jarvis is speaking) ───────────────────────────── */
.tts-wave {
  display: inline-flex;
  gap: 4px;
  margin-left: 8px;
  vertical-align: middle;
}
.tts-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--primary);
  display: inline-block;
  animation: tts-wave-bounce 0.8s ease-in-out infinite;
}
.tts-dot:nth-child(2) { animation-delay: 0.2s; }
.tts-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes tts-wave-bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.5; }
  40%           { transform: translateY(-4px); opacity: 1; }
}

/* ── Typing dots (thinking placeholder, no content yet) ──────────── */
.typing-row { display: inline-flex; gap: 5px; align-items: center; height: 18px; }
.typing-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: typing-bounce 1.4s ease-in-out infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing-bounce {
  0%, 60%, 100% { opacity: 0.3; transform: scale(0.85); }
  30%           { opacity: 1;   transform: scale(1);    }
}

/* ── Interrupted strip ───────────────────────────────────────────── */
.interrupted-strip {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed rgba(245, 158, 11, 0.35);
  display: flex;
  align-items: center;
  gap: 6px;
}

/* ── Chips ────────────────────────────────────────────────────────── */
.chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 18px;
  padding: 0 7px;
  border-radius: var(--r-full);
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 500;
  border: 1px solid var(--border-strong);
  background: var(--bg-2);
  color: var(--text-muted);
}
.chip-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: currentColor;
  display: inline-block;
}
.chip-bargein {
  background: var(--accent-bg);
  color: var(--accent);
  border-color: rgba(34, 211, 238, 0.30);
  margin-bottom: 6px;
  align-self: flex-end;
}
.chip-bargein .chip-dot { animation: typing-bounce 1.2s ease-in-out infinite; }
.chip-interrupted {
  background: var(--warning-bg);
  color: var(--warning);
  border-color: rgba(245, 158, 11, 0.30);
}

/* ── Message meta ─────────────────────────────────────────────────── */
.msg-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
}
.msg-agent {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--primary-hover);
}
.msg-time {
  font-family: var(--font-mono);
  font-size: 9.5px;
  color: var(--text-subtle);
  letter-spacing: 0.10em;
}
.msg-time-right { margin-top: 4px; text-align: right; }

/* ── YouTube ──────────────────────────────────────────────────────── */
.yt-embed {
  margin-top: 8px;
  border-radius: var(--r-md);
  overflow: hidden;
  border: 1px solid var(--border-strong);
  background: #000;
  aspect-ratio: 16 / 9;
  max-width: 560px;
}
.yt-embed iframe { width: 100%; height: 100%; display: block; border: 0; }

/* ── Tool calls ───────────────────────────────────────────────────── */
.tc-section { margin-top: 8px; }
.tc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 7px 12px;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  cursor: pointer;
  color: var(--text-dim);
  transition: border-color 0.15s ease;
}
.tc-header:hover { border-color: var(--border-strong); }
.tc-header-left { display: flex; align-items: center; gap: 6px; }
.tc-summary { font-size: 11.5px; font-weight: 500; color: var(--text-dim); }
.tc-duration-label { font-size: 11px; color: var(--text-muted); }
.tc-chevron { transition: transform 0.2s; flex-shrink: 0; color: var(--text-muted); }
.tc-chevron.expanded { transform: rotate(180deg); }

.tc-list {
  margin-top: 4px;
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  overflow: hidden;
  background: var(--bg-1);
}
.tc-row { display: flex; align-items: center; gap: 8px; padding: 6px 12px; min-height: 32px; }
.tc-entry:not(:last-child) { border-bottom: 1px solid var(--border); }
.tc-row-clickable { cursor: pointer; transition: background 0.12s; }
.tc-row-clickable:hover { background: var(--bg-2); }
.tc-row-right { display: flex; align-items: center; gap: 6px; margin-left: auto; color: var(--text-muted); }
.tc-row-chevron { transition: transform 0.2s; flex-shrink: 0; }
.tc-row-chevron.expanded { transform: rotate(180deg); }
.tc-icon {
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  width: 22px; height: 22px;
  border-radius: var(--r-sm);
  background: var(--bg-2);
  color: var(--text-muted);
}
.tc-name { font-size: 12px; font-weight: 500; color: var(--text-dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tc-dur {
  font-size: 10.5px; font-weight: 500;
  color: var(--text-muted);
  padding: 1px 5px;
  background: var(--bg-2);
  border-radius: var(--r-sm);
}
.tc-spinner {
  width: 12px; height: 12px;
  border: 1.5px solid var(--border);
  border-top-color: var(--text-muted);
  border-radius: 50%;
  animation: tc-spin 0.8s linear infinite;
}
@keyframes tc-spin { to { transform: rotate(360deg); } }

.tc-detail {
  padding: 8px 12px 10px 42px;
  background: var(--bg-0);
  border-top: 1px solid var(--border);
}
.tc-detail-block + .tc-detail-block { margin-top: 10px; }
.tc-detail-label {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  color: var(--text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.10em;
  margin-bottom: 4px;
}
.tc-detail-args { display: flex; flex-direction: column; gap: 2px; }
.tc-arg-row { display: flex; gap: 8px; font-size: 11.5px; line-height: 18px; }
.tc-arg-key {
  color: var(--text-muted);
  flex-shrink: 0;
  min-width: 60px;
  font-family: var(--font-mono);
}
.tc-arg-key::after { content: ':'; }
.tc-arg-val { color: var(--text-dim); word-break: break-word; }
.tc-detail-result {
  font-size: 11.5px;
  line-height: 17px;
  color: var(--text-dim);
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
  padding: 8px 10px;
  margin: 0;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}

.tc-expand-enter-active, .tc-expand-leave-active {
  transition: all 0.2s ease;
  max-height: 400px;
  overflow: hidden;
}
.tc-expand-enter-from, .tc-expand-leave-to { opacity: 0; max-height: 0; margin-top: 0; }

/* ── Mobile tuning ────────────────────────────────────────────────
   On <420px viewports, 78% bubble width minus a 32px avatar + 10px
   gap leaves only ~237px usable text width, which fragments URLs,
   code blocks, and long words. 88% buys back ~25px which is the
   difference between "code overflows" and "code wraps". msg-time was
   9.5px which is below the readability floor on high-DPI mobile. */
@media (max-width: 480px) {
  .bubble-wrap { max-width: 88%; }
  .msg-time { font-size: 11px; letter-spacing: 0.08em; }
  /* YouTube embed inside a bubble-wrap was capped at 78% × 560 →
     awkward letterboxing on phones. Let it expand to full bubble. */
  .yt-embed { max-width: 100%; }
}

/* ── Memory-used chip (auto-injected recall block) ── */
.row-memory { display: flex; flex-direction: column; align-items: center; gap: 6px; margin: 2px 0; }
.memory-chip { display: inline-flex; align-items: center; gap: 6px; cursor: pointer;
  background: var(--primary-bg); color: var(--primary); border: 1px solid var(--primary-bg-strong);
  border-radius: var(--r-full); padding: 3px 12px; font-size: 12px; }
.memory-chip:hover { background: var(--primary-bg-strong); }
.mc-icon { flex: none; }   /* line icon inherits the chip's currentColor (tints per state) */
.mc-chevron { transition: transform .15s; display: inline-block; }
.mc-chevron.expanded { transform: rotate(180deg); }
.memory-detail { max-width: 78%; background: var(--bg-2); border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 8px 12px; }
.memory-line { font-size: 12px; color: var(--text-dim); line-height: 1.5;
  padding: 2px 0; border-bottom: 1px solid var(--border); }
.memory-line:last-child { border-bottom: none; }
/* Retrieval-lane provenance chips — graph highlighted (the one to watch). */
.lane { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .04em;
  padding: 0 5px; border-radius: 999px; border: 1px solid transparent; margin-right: 2px; }
.lane-fts { color: var(--text-dim); background: var(--bg-4); border-color: var(--border-strong); }
.lane-dense { color: var(--primary); background: var(--primary-bg); border-color: var(--primary-bg-strong); }
.lane-graph { color: #fff; background: var(--primary); border-color: var(--primary); }
/* RAW relevance/confidence — dim, right of the line, monospace so the numbers
   line up; intentionally unobtrusive (debug detail, not primary content). */
.mscore { font-size: 10px; color: var(--text-faint); font-family: var(--font-mono, monospace);
  white-space: nowrap; margin-left: 4px; cursor: help; }
.mscore .ok { color: var(--success, #16a34a); margin-left: 2px; font-weight: 700; }

/* ── Memory-saved chip (live capture). Reuses the recall chip base (.memory-chip)
   and tints by STATE with the design-system semantic tokens — success (saved) /
   warning (pending, needs review). Hover fills the colour, mirroring .btn.danger
   in AgentMemoryPanel. Action buttons reuse that same .btn pattern. */
.memory-chip.chip-saved { background: var(--success-bg); color: var(--success); border-color: var(--success); }
.memory-chip.chip-saved:hover { background: var(--success); color: #fff; }
.memory-chip.chip-pending { background: var(--warning-bg); color: var(--warning); border-color: var(--warning); }
.memory-chip.chip-pending:hover { background: var(--warning); color: #fff; }
.saved-line { display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap; }
.saved-line.archived { opacity: .5; text-decoration: line-through; }
.mtype { color: var(--text-faint); font-family: var(--font-mono, monospace); }
.saved-actions { margin-left: auto; display: inline-flex; gap: 6px; white-space: nowrap; }
/* Mirrors AgentMemoryPanel's .btn / .btn.primary / .btn.ghost (same tokens,
   tightened for the inline chip context). */
.s-btn { background: transparent; color: var(--text-dim); border: 1px solid var(--border-strong);
  border-radius: var(--r-md); padding: 2px 10px; font-size: 11px; cursor: pointer; transition: all .15s; }
.s-btn:hover { color: var(--text); background: rgba(255,255,255,0.04); }
.s-btn.primary { background: var(--primary); color: #fff; border-color: var(--primary); }
.s-btn.primary:hover { background: var(--primary-hover); border-color: var(--primary-hover); }
.s-btn.ghost { border-color: transparent; }
.archived-tag { font-size: 11px; color: var(--text-faint); margin-left: auto; }

/* ── Executive Board Meeting Card ────────────────────────────────────── */
.boardroom-card {
  margin-top: 14px;
  background: rgba(18, 22, 36, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(99, 102, 241, 0.35);
  border-radius: 12px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.boardroom-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 12px;
}

.boardroom-header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.boardroom-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.4);
  border-radius: 999px;
  padding: 3px 10px;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  color: #818cf8;
  letter-spacing: 0.08em;
}

.boardroom-live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 8px #38bdf8;
  animation: pulse-live 1.8s infinite;
}

@keyframes pulse-live {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}

.boardroom-open-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #a5b4fc;
  text-decoration: none;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 3px 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
}
.boardroom-open-btn:hover {
  background: rgba(99, 102, 241, 0.25);
  color: #fff;
  border-color: rgba(99, 102, 241, 0.5);
}

.boardroom-title {
  font-size: 15px;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0;
  letter-spacing: -0.01em;
}

.boardroom-agenda {
  font-size: 12px;
  color: #94a3b8;
  margin: 0;
  line-height: 1.4;
}

.agenda-tag {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.08);
  padding: 2px 5px;
  border-radius: 4px;
  color: #cbd5e1;
  margin-right: 4px;
}

.boardroom-roster {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.roster-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: 1px solid transparent;
  border-radius: 6px;
  padding: 3px 8px;
  font-size: 11px;
}

.roster-emoji {
  font-size: 12px;
}

.roster-name {
  font-weight: 600;
}

.roster-role {
  font-size: 10px;
  color: var(--text-muted);
  border-left: 1px solid rgba(255, 255, 255, 0.12);
  padding-left: 5px;
  margin-left: 2px;
}

/* ── Deliberation turns ────────────────────────────────────────────── */
.boardroom-turns {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.boardroom-speech-card {
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-left-width: 3.5px;
  border-radius: 8px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.speech-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.speech-speaker-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.speech-avatar {
  font-size: 13px;
}

.speech-speaker-name {
  font-size: 12px;
  font-weight: 700;
}

.speech-speaker-role {
  font-size: 10px;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.05);
  padding: 1px 6px;
  border-radius: 4px;
}

.speech-turn-pill {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-subtle);
}

.speech-body {
  font-size: 12.5px;
  line-height: 1.55;
  color: #e2e8f0;
}

.speech-body :deep(p) {
  margin: 4px 0;
}

.speech-body :deep(ul), .speech-body :deep(ol) {
  padding-left: 18px;
  margin: 4px 0;
}

/* ── Conclusion Card ───────────────────────────────────────────────── */
.boardroom-conclusion {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.12) 0%, rgba(16, 185, 129, 0.06) 100%);
  border: 1px solid rgba(34, 197, 94, 0.4);
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.conclusion-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  color: #4ade80;
  letter-spacing: 0.06em;
}

.conclusion-content {
  font-size: 12.5px;
  line-height: 1.5;
  color: #f0fdf4;
}

.conclusion-content :deep(p) {
  margin: 4px 0;
}
</style>
