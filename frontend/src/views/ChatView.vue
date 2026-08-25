<script setup>
/**
 * ChatView — Track 5 redesign with text/voice mode switching.
 *
 * Layout:
 *   text mode:  ConversationsPanel | ChatHeader + VoiceBar(compact) + ChatMessages + ChatInput
 *   voice mode: ConversationsPanel | ChatHeader + VoiceBar(full)
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useChatStore } from '../stores/chat'
import { useAudioPlayerStore } from '../stores/audioPlayer'
import { useAgentsStore } from '../stores/agents'
import { useCrawlStatus } from '../composables/useCrawlStatus'
import { useLang } from '../composables/useLang'
import { EVENTS, on } from '../auth/bus.js'
import { useChatStream } from '../composables/useChatStream'
import { useConfirm } from '../composables/useConfirm'
import { useToast } from '../composables/useToast'
import { useVoiceSession } from '../composables/useVoiceSession'
import { useBreakpoint } from '../composables/useBreakpoint'
import { expandToolRequest, expandToolDone } from '../utils/toolEvents'
import ConversationsPanel from '../components/chat/ConversationsPanel.vue'
import ChatHeader from '../components/chat/ChatHeader.vue'
import ChatMessages from '../components/chat/ChatMessages.vue'
import ChatInput from '../components/chat/ChatInput.vue'
import VoiceBar from '../components/chat/VoiceBar.vue'
import JarvisVoiceUI from '../components/chat/JarvisVoiceUI.vue'

defineOptions({ name: 'Chat' })

const { isMobile } = useBreakpoint()
const showMobileConversations = ref(false)

const chatStore = useChatStore()
const audioStore = useAudioPlayerStore()
const agentsStore = useAgentsStore()
const crawl = useCrawlStatus()
const { t } = useLang()
const { isStreaming, send, cancel } = useChatStream()
const { confirm } = useConfirm()
const toast = useToast()
const voice = useVoiceSession()

// ── Mode: 'text' | 'voice' ──
const chatMode = ref('text')

function loadWorkspace() {
  chatStore.fetchConversations()
  if (!agentsStore.agentsList.length) agentsStore.fetchAgents()
}

onMounted(() => {
  loadWorkspace()
})

const offRestored = on(EVENTS.RESTORED, () => {
  loadWorkspace()
})
onUnmounted(() => {
  offRestored()
})

watch(
  () => agentsStore.agentsList,
  (list) => {
    if (list.length && !chatStore.activeAgentName) {
      const jarvis = list.find(a => a.name === 'Jarvis')
      chatStore.setActiveAgent(jarvis ? jarvis.name : list[0].name)
    }
  },
  { immediate: true }
)

const currentAgent = computed(() => {
  const name = chatStore.activeAgentName
  return agentsStore.agentsList.find(a => a.name === name) || null
})

// Status footer
const statusFooter = computed(() => {
  if (isStreaming.value) return t('chat.responding')
  if (voice.status.value === 'listening') return 'Voice active — listening'
  if (voice.status.value === 'thinking') return 'Voice active — thinking'
  if (voice.status.value === 'speaking') return 'Voice active — speaking'
  return ''
})
const statusFooterActive = computed(() => isStreaming.value || voice.status.value !== 'idle')

async function handleStop({ mode }) {
  if (mode === 'hard') {
    const proceed = await confirm({
      title: 'Force Stop',
      message: 'This will kill all running agents. Side effects may have committed.',
      confirmText: 'Force Stop',
      cancelText: 'Cancel',
      variant: 'danger',
    })
    if (!proceed) return
  }
  const res = await cancel(mode)
  chatStore.isStreaming = false
  if (mode === 'soft') {
    toast.info('Stopped', { description: 'Generation stopped.', duration: 4000 })
  } else if (res?.killed_pids?.length) {
    const names = res.killed_pids.map(k => k.name).filter(Boolean).join(', ')
    toast.warning(`Killed ${res.killed_pids.length} agents`, { description: names, duration: 6000 })
  }
}

async function handleSend(payload) {
  const text = payload.text || ''
  const files = payload.files || null
  if (!text.trim() && !files?.length) return
  if (isStreaming.value) return

  if (!chatStore.activeConversation) {
    chatStore.createConversation(chatStore.activeAgentName)
  }

  const displayText = files?.length
    ? `${text}${text ? ' ' : ''}📎 ${files.map(f => f.name).join(', ')}`
    : text
  chatStore.addUserMessage(displayText)

  const msgId = chatStore.addAgentMessagePlaceholder()
  chatStore.isStreaming = true

  await send(
    text,
    chatStore.activeConversation?.backendConversationId,
    (event) => {
      switch (event.type) {
        case 'tool_call':
        case 'tool_request':
          for (const p of expandToolRequest(event)) chatStore.pushToolCall(msgId, p)
          break
        case 'tool_result':
        case 'tool_done':
          for (const p of expandToolDone(event)) chatStore.pushToolCall(msgId, p)
          break
        case 'done':
          chatStore.finalizeAgentMessage(msgId, event.response || '', {
            conversation_id: event.conversation_id,
            audio: event.audio,
            total_tokens: event.total_tokens,
          })
          audioStore.playFromChat(event, chatStore.ttsEnabled)
          if (event.crawl_job_id) crawl.track(event.crawl_job_id)
          break
        case 'error':
          chatStore.setMessageError(msgId, event.message || 'Unknown error')
          break
      }
    },
    files,
    chatStore.activeAgentName,
  )
  chatStore.isStreaming = false
}

function handleSwitchAgent(name) {
  chatStore.setActiveAgent(name)
}
</script>

<template>
  <div class="chat-root" :class="{ 'chat-root--mobile': isMobile }">
    <!-- Desktop sidebar -->
    <ConversationsPanel v-if="!isMobile" />

    <!-- Mobile slide-out conversations -->
    <teleport to="body">
      <transition name="conv-overlay">
        <div
          v-if="isMobile && showMobileConversations"
          class="conv-overlay"
          @click.self="showMobileConversations = false"
        >
          <div class="conv-slide-panel">
            <ConversationsPanel
              :show-close="true"
              @close="showMobileConversations = false"
              @select="showMobileConversations = false"
            />
          </div>
        </div>
      </transition>
    </teleport>

    <!-- Right column -->
    <main class="chat-main">
      <ChatHeader
        :agent="currentAgent"
        :agents="agentsStore.agentsList"
        :show-hamburger="isMobile"
        :mode="chatMode"
        @switch-agent="handleSwitchAgent"
        @toggle-conversations="showMobileConversations = !showMobileConversations"
        @update:mode="chatMode = $event"
      />

      <!-- ═══ TEXT MODE ═══ -->
      <template v-if="chatMode === 'text'">
        <!-- Compact voice strip -->
        <VoiceBar :compact="true" />

        <ChatMessages
          :messages="chatStore.activeMessages"
          :agent="currentAgent"
          :isStreaming="isStreaming"
        />

        <!-- TTS Now Playing -->
        <div v-if="chatStore.ttsPlaying" class="tts-now-playing">
          <div class="tts-eq">
            <div class="tts-bar" style="animation-delay: 0s"></div>
            <div class="tts-bar" style="animation-delay: 0.2s"></div>
            <div class="tts-bar" style="animation-delay: 0.4s"></div>
            <div class="tts-bar" style="animation-delay: 0.1s"></div>
          </div>
          <span class="tts-label">Playing response...</span>
          <button class="tts-stop" @click="chatStore.stopTts()">
            <svg width="9" height="9" viewBox="0 0 10 10" fill="none">
              <rect x="1" y="1" width="8" height="8" rx="1" fill="var(--danger)"/>
            </svg>
            <span>Stop</span>
          </button>
        </div>

        <!-- Crawl progress -->
        <div
          v-if="crawl.jobId.value"
          class="crawl-strip"
          :class="{ done: !crawl.isActive.value, warn: crawl.needsAttention.value }"
        >
          <span class="crawl-spinner" v-if="crawl.isActive.value" />
          <span class="crawl-label">
            <template v-if="crawl.status.value === 'completed'">
              Downloaded "{{ crawl.storyTitle.value }}" — {{ crawl.current.value }}/{{ crawl.total.value }} chapters
            </template>
            <template v-else-if="crawl.status.value === 'failed' || crawl.status.value === 'error'">
              Crawl failed{{ crawl.message.value ? `: ${crawl.message.value}` : '' }}
            </template>
            <template v-else>
              Downloading{{ crawl.storyTitle.value ? ` "${crawl.storyTitle.value}"` : '' }}…
              {{ crawl.current.value }}/{{ crawl.total.value || '?' }} chapters
              <span v-if="crawl.total.value" class="crawl-pct">{{ crawl.percent.value }}%</span>
            </template>
          </span>
          <button v-if="crawl.isActive.value" class="crawl-btn" @click="crawl.cancel()">Cancel</button>
          <button v-else class="crawl-btn" @click="crawl.dismiss()">Dismiss</button>
        </div>

        <!-- Status footer -->
        <div v-if="statusFooter" class="status-footer">
          <span class="status-footer-dot" :class="{ pulse: statusFooterActive }" />
          <span class="status-footer-text">{{ statusFooter }}</span>
        </div>

        <ChatInput
          :isStreaming="isStreaming"
          @send="handleSend"
          @stop="handleStop"
        />
      </template>

      <!-- ═══ VOICE MODE ═══ -->
      <template v-else>
        <JarvisVoiceUI />
      </template>
    </main>
  </div>
</template>

<style scoped>
.chat-root {
  display: flex;
  height: calc(100% + 48px);
  margin: -24px -36px;
  background: var(--bg-0);
  color: var(--text);
  position: relative;
}
/* Subtle grid overlay for premium feel */
.chat-root::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    radial-gradient(circle at 1px 1px, rgba(99, 102, 241, 0.03) 1px, transparent 0);
  background-size: 48px 48px;
  z-index: 0;
}
.chat-root--mobile {
  --chat-bottom-pad: calc(var(--mobile-tabbar-h) + var(--mini-player-h, 0px) + max(16px, var(--safe-bottom)));
  margin: -16px -12px;
  margin-bottom: calc(-1 * (var(--chat-bottom-pad) + var(--mobile-fab-band)));
  height: calc(100% + 16px + var(--chat-bottom-pad) + var(--mobile-fab-band));
  padding-bottom: var(--chat-bottom-pad);
}
.chat-root--mobile::before { display: none; }

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-0);
  position: relative;
  /* z-index removed — it trapped the agent dropdown below the
     teleported hd-dropdown-mask, preventing agent switching. */
}

/* Conversations slide-out (mobile) */
.conv-overlay {
  position: fixed; inset: 0; z-index: 200;
  background: var(--bg-overlay); display: flex;
}
.conv-slide-panel { width: 300px; max-width: 80vw; height: 100%; background: var(--bg-1); }
.conv-overlay-enter-active, .conv-overlay-leave-active { transition: opacity 0.2s ease; }
.conv-overlay-enter-active .conv-slide-panel, .conv-overlay-leave-active .conv-slide-panel { transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
.conv-overlay-enter-from, .conv-overlay-leave-to { opacity: 0; }
.conv-overlay-enter-from .conv-slide-panel, .conv-overlay-leave-to .conv-slide-panel { transform: translateX(-100%); }

/* Crawl */
.crawl-strip {
  flex-shrink: 0; display: flex; align-items: center; gap: 10px;
  padding: 8px 24px; background: var(--primary-bg);
  border-top: 1px solid var(--primary-bg-strong);
  font-size: 12px; color: var(--text);
}
.crawl-strip.done { background: var(--bg-2); border-top-color: var(--border); }
.crawl-strip.warn { background: var(--warning-bg); border-top-color: rgba(245,158,11,0.30); }
.crawl-label { flex: 1; }
.crawl-pct { color: var(--primary-hover); font-weight: 600; margin-left: 4px; }
.crawl-spinner {
  width: 14px; height: 14px; flex-shrink: 0;
  border: 2px solid var(--primary-bg-strong); border-top-color: var(--primary-hover);
  border-radius: 50%; animation: crawl-spin 0.8s linear infinite;
}
@keyframes crawl-spin { to { transform: rotate(360deg); } }
.crawl-btn {
  flex-shrink: 0; padding: 4px 12px; background: var(--bg-3);
  border: 1px solid var(--border-strong); border-radius: var(--r-sm);
  color: var(--text-dim); font-size: 11px; cursor: pointer;
}
.crawl-btn:hover { color: var(--text); background: var(--bg-4); }

/* Status footer */
.status-footer {
  flex-shrink: 0; display: flex; align-items: center; gap: 8px;
  padding: 8px 28px;
  background: linear-gradient(90deg, rgba(99,102,241,0.06) 0%, transparent 100%);
  border-top: 1px solid var(--border);
  font-family: var(--font-mono); font-size: 11px;
  color: var(--text-muted); letter-spacing: 0.08em;
}
.status-footer-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text-muted);
  box-shadow: 0 0 0 2px rgba(123,128,148,0.15);
}
.status-footer-dot.pulse {
  background: var(--accent);
  box-shadow: 0 0 0 2px rgba(34,211,238,0.15), 0 0 12px rgba(34,211,238,0.4);
  animation: status-pulse 1.2s ease-in-out infinite;
}
@keyframes status-pulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.55; transform:scale(1.3); } }

/* TTS Now Playing */
.tts-now-playing {
  flex-shrink: 0; display: flex; align-items: center; gap: 10px;
  padding: 8px 28px;
  background: linear-gradient(90deg, rgba(16,185,129,0.08) 0%, transparent 100%);
  border-top: 1px solid rgba(16,185,129,0.15);
}
.tts-eq { display: flex; align-items: end; gap: 2px; height: 14px; }
.tts-bar {
  width: 3px; background: var(--success); border-radius: 2px;
  animation: tts-bar-bounce 0.8s ease-in-out infinite alternate;
}
@keyframes tts-bar-bounce { 0% { height: 3px; } 100% { height: 14px; } }
.tts-label { flex: 1; font-size: 11px; font-weight: 500; color: var(--success); letter-spacing: 0.03em; }
.tts-stop {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 12px; background: var(--danger-bg);
  border: 1px solid rgba(239,68,68,0.25); border-radius: var(--r-full);
  cursor: pointer; color: var(--danger); font-size: 11px; font-weight: 500;
  transition: all 0.15s ease;
}
.tts-stop:hover { background: rgba(239,68,68,0.2); border-color: rgba(239,68,68,0.4); }
</style>
