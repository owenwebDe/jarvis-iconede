<script setup>
import { ref, computed } from 'vue'
import { useChatStore } from '../../stores/chat'
import { useVoiceSession } from '../../composables/useVoiceSession.js'
import { useLang } from '../../composables/useLang'

/**
 * ChatHeader — top strip with agent info, voice readiness, mode toggle, and agent switcher.
 *
 * New: text/voice mode toggle. The mode is a local UI state — it controls
 * whether ChatInput (text) or the full VoiceBar (hands-free) is shown below.
 */
const props = defineProps({
  agent: { type: Object, default: null },
  agents: { type: Array, default: () => [] },
  showHamburger: { type: Boolean, default: false },
  mode: { type: String, default: 'text' }, // 'text' | 'voice'
})

const emit = defineEmits(['switch-agent', 'toggle-conversations', 'update:mode'])
const chatStore = useChatStore()
const voice = useVoiceSession()
const { t } = useLang()
const showDropdown = ref(false)

const initials = computed(() => {
  if (!props.agent?.name) return '?'
  return props.agent.name
    .split(/[\s_-]+/)
    .map(w => w[0]?.toUpperCase() || '')
    .join('')
    .slice(0, 2)
})

const voiceStrip = computed(() => {
  const s = voice.status.value
  if (s === 'idle') return t('chat.voiceOff')
  if (s === 'loading_stt') return t('chat.voiceSttLoading')
  if (s === 'connecting') return t('chat.voiceConnecting')
  if (s === 'speaking')  return t('chat.voiceSpeaking')
  if (s === 'thinking')  return t('chat.voiceThinking')
  return t('chat.voiceReady')
})

const isVoiceOn = computed(() => voice.status.value !== 'idle' && voice.status.value !== 'error')

const wsChip = computed(() => {
  const s = voice.wsStatus?.value || 'idle'
  if (s === 'connected')    return { label: 'WS',       cls: 'chip-success', pulse: false }
  if (s === 'connecting')   return { label: 'WS…',      cls: 'chip-warning', pulse: true }
  if (s === 'reconnecting') return { label: 'RECONNECT', cls: 'chip-warning', pulse: true }
  if (s === 'error')        return { label: 'WS ERR',   cls: 'chip-danger',  pulse: false }
  return                      { label: 'OFF',      cls: 'chip-muted',   pulse: false }
})

function selectAgent(name) {
  emit('switch-agent', name)
  showDropdown.value = false
}

function setMode(mode) {
  emit('update:mode', mode)
}
</script>

<template>
  <div class="hd" :class="{ 'hd-mobile': showHamburger }">
    <button
      v-if="showHamburger"
      class="hd-hamburger"
      @click="emit('toggle-conversations')"
      :aria-label="t('chat.openConversations')"
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <line x1="2" y1="4" x2="14" y2="4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="2" y1="8" x2="14" y2="8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="2" y1="12" x2="14" y2="12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </button>

    <div class="hd-ava">{{ initials }}</div>

    <div class="hd-info">
      <div class="hd-name-row">
        <span class="hd-name">{{ agent?.name || t('chat.noAgent') }}</span>
        <span v-if="agent" class="hd-role">· {{ t('chat.orchestrator') }}</span>
      </div>
      <div class="hd-status-row">
        <span class="hd-dot" :class="{ on: isVoiceOn }" />
        <span class="hd-status">{{ voiceStrip }}</span>
      </div>
    </div>

    <!-- Mode Toggle: Text ↔ Voice -->
    <div class="hd-mode-toggle">
      <button
        class="mode-btn"
        :class="{ active: mode === 'text' }"
        @click="setMode('text')"
        title="Text Chat"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span class="mode-label">Chat</span>
      </button>
      <button
        class="mode-btn"
        :class="{ active: mode === 'voice' }"
        @click="setMode('voice')"
        title="Voice Mode"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="23"/>
          <line x1="8" y1="23" x2="16" y2="23"/>
        </svg>
        <span class="mode-label">Voice</span>
      </button>
    </div>

    <!-- WS chip -->
    <span class="hd-chip" :class="wsChip.cls" :title="`STT WS: ${voice.wsStatus?.value || 'idle'}`">
      <span class="hd-chip-dot" :class="{ pulse: wsChip.pulse }" /> {{ wsChip.label }}
    </span>

    <!-- Switch agent -->
    <div class="hd-switch">
      <button class="hd-switch-btn" @click="showDropdown = !showDropdown">
        <span>{{ t('chat.switch') }}</span>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M3 5L6 8L9 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <div v-if="showDropdown" class="hd-dropdown">
        <div
          v-for="a in agents"
          :key="a.name"
          class="hd-dropdown-item"
          :class="{ active: a.name === agent?.name }"
          @click="selectAgent(a.name)"
        >
          <div class="hd-mini-ava">
            {{ a.name.split(/[\s_-]+/).map(w => w[0]?.toUpperCase()).join('').slice(0,2) }}
          </div>
          <span>{{ a.name }}</span>
        </div>
      </div>
    </div>

    <!-- TTS button -->
    <button
      class="hd-tts"
      :class="{ playing: chatStore.ttsPlaying, on: chatStore.ttsEnabled }"
      :title="chatStore.ttsPlaying ? 'Stop playback' : chatStore.ttsEnabled ? 'TTS On' : 'TTS Off'"
      @click="chatStore.ttsPlaying ? chatStore.stopTts() : chatStore.toggleTts()"
    >
      <svg v-if="chatStore.ttsPlaying" width="14" height="14" viewBox="0 0 15 15" fill="none">
        <rect x="3" y="3" width="9" height="9" rx="1.5" fill="var(--danger)"/>
      </svg>
      <svg v-else-if="chatStore.ttsEnabled" width="14" height="14" viewBox="0 0 15 15" fill="none">
        <path d="M2 5.5H4L7.5 2V13L4 9.5H2C1.5 9.5 1 9 1 8.5V6.5C1 6 1.5 5.5 2 5.5Z" fill="currentColor" stroke="currentColor" stroke-width="0.8"/>
        <path d="M10 4.5C11 5.5 11.5 6.5 11.5 7.5C11.5 8.5 11 9.5 10 10.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
      </svg>
      <svg v-else width="14" height="14" viewBox="0 0 15 15" fill="none">
        <path d="M2 5.5H4L7.5 2V13L4 9.5H2C1.5 9.5 1 9 1 8.5V6.5C1 6 1.5 5.5 2 5.5Z" stroke="currentColor" stroke-width="1.2"/>
        <path d="M10 5.5L14 9.5M14 5.5L10 9.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
      </svg>
    </button>

    <teleport to="body">
      <div v-if="showDropdown" class="hd-dropdown-mask" @click="showDropdown = false"></div>
    </teleport>
  </div>
</template>

<style scoped>
.hd {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 60px;
  padding: 0 24px;
  background: linear-gradient(180deg, var(--bg-1) 0%, rgba(11,13,18,0.95) 100%);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  backdrop-filter: blur(12px);
  position: relative;
}
/* Subtle glow accent line under header */
.hd::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(99,102,241,0.3) 30%, rgba(34,211,238,0.2) 70%, transparent 100%);
}
.hd.hd-mobile { height: 54px; padding: 0 14px; gap: 10px; }

.hd-hamburger {
  width: 34px; height: 34px;
  display: flex; align-items: center; justify-content: center;
  background: var(--bg-2);
  border: 1px solid var(--border-strong);
  border-radius: var(--r-md);
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s ease;
}
.hd-hamburger:hover { background: var(--bg-3); color: var(--text); border-color: var(--border-bright); }

.hd-ava {
  width: 36px; height: 36px;
  flex-shrink: 0;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: white;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  box-shadow: 0 0 0 2px rgba(99,102,241,0.2), 0 4px 12px rgba(99,102,241,0.25);
  transition: box-shadow 0.2s ease;
}
.hd-ava:hover { box-shadow: 0 0 0 2px rgba(99,102,241,0.3), 0 4px 20px rgba(99,102,241,0.4); }

.hd-info { flex: 1; min-width: 0; }
.hd-name-row { display: flex; align-items: baseline; gap: 8px; }
.hd-name {
  font-size: 15px; font-weight: 700; color: var(--text);
  letter-spacing: -0.01em;
}
.hd-role { font-size: 12px; color: var(--text-muted); font-weight: 400; }

.hd-status-row { display: flex; align-items: center; gap: 6px; margin-top: 2px; }
.hd-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text-subtle); flex-shrink: 0;
  transition: all 0.3s ease;
}
.hd-dot.on {
  background: var(--accent);
  box-shadow: 0 0 8px var(--accent);
}
.hd-status {
  font-family: var(--font-mono); font-size: 10px;
  letter-spacing: 0.10em; text-transform: uppercase; color: var(--text-muted);
}

/* ── Mode Toggle ── */
.hd-mode-toggle {
  display: flex;
  background: var(--bg-2);
  border: 1px solid var(--border-strong);
  border-radius: var(--r-full);
  padding: 3px;
  gap: 2px;
}
.mode-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border: none;
  border-radius: var(--r-full);
  background: transparent;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
  white-space: nowrap;
}
.mode-btn:hover { color: var(--text); background: rgba(255,255,255,0.03); }
.mode-btn.active {
  background: linear-gradient(135deg, var(--primary), #5B5FE8);
  color: white;
  box-shadow: 0 2px 12px var(--primary-glow), inset 0 1px 0 rgba(255,255,255,0.15);
}
.mode-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hd-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: var(--r-full);
  font-family: var(--font-mono); font-size: 10px;
  letter-spacing: 0.10em; text-transform: uppercase;
  border: 1px solid var(--border-strong);
  transition: all 0.2s ease;
}
.hd-chip.chip-success { background: var(--success-bg); color: var(--success); border-color: rgba(16,185,129,0.25); }
.hd-chip.chip-muted { background: var(--bg-3); color: var(--text-muted); }
.hd-chip.chip-warning { background: var(--warning-bg); color: var(--warning); border-color: rgba(245,158,11,0.30); }
.hd-chip.chip-danger { background: var(--danger-bg); color: var(--danger); border-color: rgba(239,68,68,0.30); }
.hd-chip-dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; box-shadow: 0 0 6px currentColor; }
.hd-chip-dot.pulse { animation: hd-chip-pulse 0.9s ease-in-out infinite; }
@keyframes hd-chip-pulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.4; transform:scale(1.3); } }

.hd-switch { position: relative; }
.hd-switch-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 6px 12px; background: transparent; border: 1px solid transparent;
  color: var(--text-muted); font-size: 11.5px; cursor: pointer;
  border-radius: var(--r-md); transition: all 0.15s ease;
}
.hd-switch-btn:hover { color: var(--text); background: var(--bg-2); border-color: var(--border); }
.hd-dropdown {
  position: absolute; top: calc(100% + 6px); right: 0;
  width: 220px; background: var(--bg-2);
  border: 1px solid var(--border-strong);
  border-radius: var(--r-lg); padding: 6px;
  box-shadow: var(--shadow-lg); z-index: 50;
}
.hd-dropdown-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; border-radius: var(--r-md); cursor: pointer;
  transition: all 0.12s ease;
}
.hd-dropdown-item:hover { background: var(--bg-3); }
.hd-dropdown-item.active { background: var(--primary-bg); }
.hd-mini-ava {
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--primary-bg-strong); color: var(--primary-hover);
  font-family: var(--font-mono); font-size: 9px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.hd-dropdown-item span { font-size: 12.5px; color: var(--text-dim); font-weight: 500; }
.hd-dropdown-mask { position: fixed; inset: 0; z-index: 40; }

.hd-tts {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  background: transparent; border: 1px solid transparent;
  border-radius: var(--r-md); color: var(--text-muted);
  cursor: pointer; transition: all 0.15s ease;
}
.hd-tts:hover { color: var(--text); background: var(--bg-2); border-color: var(--border); }
.hd-tts.on { background: var(--success-bg); border-color: rgba(16,185,129,0.25); color: var(--success); }
.hd-tts.playing { background: var(--danger-bg); border-color: rgba(239,68,68,0.30); color: var(--danger); }

@media (max-width: 480px) {
  .hd-role { display: none; }
  .hd-chip { display: none; }
  .hd-mode-toggle { display: none; }
}
</style>
