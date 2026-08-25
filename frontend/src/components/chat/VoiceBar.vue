<script setup>
/**
 * VoiceBar — Professional hands-free voice interface.
 *
 * Two rendering modes controlled by `compact` prop:
 *   - compact=true:  Horizontal strip (for text-mode header bar)
 *   - compact=false: Full-height centered voice mode (large mic, waveform, transcript)
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useVoiceSession } from '../../composables/useVoiceSession.js'
import { useLang } from '../../composables/useLang'

const props = defineProps({
  compact: { type: Boolean, default: false },
})

const session = useVoiceSession()
const { t } = useLang()

const STATUS_LABELS = {
  idle: 'Ready',
  connecting: 'Connecting...',
  loading_stt: 'Loading STT...',
  listening: 'Listening',
  thinking: 'Thinking...',
  speaking: 'Speaking',
  error: 'Error',
}

const statusLabel = computed(() => {
  if (session.isSleeping.value && isOn.value) return 'STANDBY'
  return STATUS_LABELS[session.status.value] || session.status.value
})

const isOn = computed(() => session.status.value !== 'idle' && session.status.value !== 'error')
const canInterrupt = computed(() => session.status.value === 'thinking' || session.status.value === 'speaking')

// Waveform bars for visual feedback
const waveformBars = ref(Array.from({ length: 5 }, () => 3))
let waveformInterval = null

onMounted(() => {
  waveformInterval = setInterval(() => {
    if (session.status.value === 'listening') {
      waveformBars.value = Array.from({ length: 5 }, () => Math.random() * 18 + 4)
    } else if (session.status.value === 'speaking') {
      waveformBars.value = Array.from({ length: 5 }, () => Math.random() * 24 + 6)
    } else if (session.status.value === 'thinking') {
      waveformBars.value = Array.from({ length: 5 }, (_, i) => 6 + Math.sin(Date.now() / 300 + i) * 4)
    } else {
      waveformBars.value = Array.from({ length: 5 }, () => 3)
    }
  }, 100)
})

onUnmounted(() => {
  if (waveformInterval) clearInterval(waveformInterval)
})

async function toggle() {
  if (isOn.value) await session.stop()
  else await session.start()
}
</script>

<template>
  <!-- ═══ COMPACT MODE: horizontal strip for text-mode header ═══ -->
  <div v-if="compact" class="voice-compact" :class="{ on: isOn, error: session.status.value === 'error' }">
    <button class="mic-compact" :class="{ active: isOn }" @click="toggle">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
        <rect x="5.5" y="1.5" width="5" height="8.5" rx="2.5" stroke="currentColor" stroke-width="1.4"/>
        <path d="M3 8c0 2.8 2.2 5 5 5s5-2.2 5-5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        <line x1="8" y1="13" x2="8" y2="15" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
      </svg>
    </button>
    <span class="status-pill-compact" :class="`pill-${session.status.value}`">
      <span v-if="canInterrupt" class="dot pulse" />
      <span v-else-if="isOn" class="dot" />
      {{ statusLabel }}
    </span>
    <button v-if="canInterrupt" class="interrupt-compact" @click="session.bargeIn()">Interrupt</button>
  </div>

  <!-- ═══ FULL MODE: centered voice interface ═══ -->
  <div v-else class="voice-full" :class="{ active: isOn, speaking: session.status.value === 'speaking', error: session.status.value === 'error', sleeping: session.isSleeping.value }">
    <!-- Background gradient animation -->
    <div class="voice-bg" />

    <div class="voice-center">
      <!-- Status text -->
      <div class="voice-status">
        <span class="voice-status-text" :class="`st-${session.status.value}`">
          {{ statusLabel }}
        </span>
        <span v-if="session.isSleeping.value" class="voice-sleep-hint">
          Say "Hey Jarvis" or tap to wake
        </span>
      </div>

      <!-- Waveform visualization -->
      <div class="waveform">
        <div
          v-for="(h, i) in waveformBars"
          :key="i"
          class="wave-bar"
          :class="{ active: isOn }"
          :style="{ height: h + 'px', animationDelay: (i * 0.1) + 's' }"
        />
      </div>

      <!-- Main mic button -->
      <button class="mic-main" :class="{ active: isOn, pulse: session.status.value === 'listening' }" @click="toggle">
        <div class="mic-ring" />
        <div class="mic-inner">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8" y1="23" x2="16" y2="23"/>
          </svg>
        </div>
      </button>

      <!-- Transcript display -->
      <div class="voice-transcript">
        <template v-if="session.partialTranscript.value">
          <span class="transcript-partial">{{ session.partialTranscript.value }}</span>
        </template>
        <template v-else-if="session.lastFinalTranscript.value">
          <span class="transcript-final">"{{ session.lastFinalTranscript.value }}"</span>
        </template>
        <template v-else-if="session.sleepHint.value">
          <span class="transcript-hint">{{ session.sleepHint.value }}</span>
        </template>
        <template v-else>
          <span class="transcript-placeholder">Speak to Jarvis...</span>
        </template>
      </div>

      <!-- Controls row -->
      <div class="voice-controls">
        <!-- Sleep/wake -->
        <button
          v-if="isOn"
          class="ctrl-btn"
          :class="{ sleeping: session.isSleeping.value }"
          @click="session.toggleSleep"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
          <span>{{ session.isSleeping.value ? 'Wake' : 'Sleep' }}</span>
        </button>

        <!-- Interrupt -->
        <button v-if="canInterrupt" class="ctrl-btn ctrl-interrupt" @click="session.bargeIn()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="6" y="6" width="12" height="12" rx="2"/>
          </svg>
          <span>Interrupt</span>
        </button>

        <!-- Error -->
        <span v-if="session.error.value" class="voice-error">{{ session.error.value }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ═══ COMPACT MODE ═══ */
.voice-compact {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-1);
  min-height: 40px;
}
.voice-compact.on {
  background: linear-gradient(to bottom, rgba(99,102,241,0.06), var(--bg-1));
}

.mic-compact {
  width: 30px; height: 30px;
  display: flex; align-items: center; justify-content: center;
  background: var(--bg-3); border: 1px solid var(--border-strong);
  border-radius: 50%; color: var(--text-muted); cursor: pointer;
  transition: all 0.2s ease;
}
.mic-compact:hover { color: var(--text); border-color: var(--border-bright); }
.mic-compact.active {
  background: var(--primary); border-color: transparent; color: white;
  box-shadow: 0 0 12px var(--primary-glow);
}

.status-pill-compact {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 8px; border-radius: 999px;
  font-family: var(--font-mono); font-size: 10px;
  letter-spacing: 0.08em; text-transform: uppercase;
  background: var(--bg-2); color: var(--text-muted);
  border: 1px solid var(--border-strong);
}
.status-pill-compact.pill-listening { background: var(--success-bg); color: var(--success); border-color: rgba(16,185,129,0.25); }
.status-pill-compact.pill-thinking { background: var(--warning-bg); color: var(--warning); }
.status-pill-compact.pill-speaking { background: var(--primary-bg); color: var(--primary-hover); }

.dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
.dot.pulse { animation: dot-pulse 0.9s ease-in-out infinite; }
@keyframes dot-pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }

.interrupt-compact {
  padding: 4px 10px; background: transparent;
  border: 1px solid var(--danger); color: var(--danger);
  border-radius: var(--r-sm); font-size: 10px; font-weight: 600;
  cursor: pointer; text-transform: uppercase; letter-spacing: 0.06em;
}
.interrupt-compact:hover { background: var(--danger-bg); }

/* ═══ FULL MODE ═══ */
.voice-full {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: var(--bg-0);
  min-height: 0;
}

.voice-bg {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at center, rgba(99,102,241,0.04) 0%, transparent 70%);
  pointer-events: none;
  transition: opacity 0.5s ease;
}
.voice-full.active .voice-bg {
  background: radial-gradient(ellipse at center, rgba(99,102,241,0.08) 0%, transparent 70%);
}
.voice-full.speaking .voice-bg {
  background: radial-gradient(ellipse at center, rgba(16,185,129,0.08) 0%, transparent 70%);
}

.voice-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  z-index: 1;
}

/* Status */
.voice-status { text-align: center; }
.voice-status-text {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
  transition: color 0.3s ease;
}
.voice-status-text.st-listening { color: var(--success); }
.voice-status-text.st-thinking { color: var(--warning); }
.voice-status-text.st-speaking { color: var(--primary-hover); }
.voice-status-text.st-error { color: var(--danger); }
.voice-sleep-hint {
  display: block;
  font-size: 11px;
  color: var(--warning);
  margin-top: 4px;
}

/* Waveform */
.waveform {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 32px;
}
.wave-bar {
  width: 4px;
  border-radius: 2px;
  background: var(--text-muted);
  opacity: 0.3;
  transition: height 0.1s ease, background 0.3s ease, opacity 0.3s ease;
}
.wave-bar.active {
  opacity: 0.8;
}
.voice-full.listening .wave-bar { background: var(--success); }
.voice-full.speaking .wave-bar { background: var(--primary); }
.voice-full.thinking .wave-bar { background: var(--warning); }

/* Main mic button */
.mic-main {
  position: relative;
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: var(--bg-3);
  border: 2px solid var(--border-strong);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.mic-main:hover {
  transform: scale(1.05);
  border-color: var(--primary);
}
.mic-main.active {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
  box-shadow: 0 0 32px var(--primary-glow), 0 0 64px rgba(99,102,241,0.15);
}
.mic-main.pulse {
  animation: mic-pulse 2s ease-in-out infinite;
}

.mic-ring {
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}
.mic-main.active .mic-ring {
  border-color: rgba(99,102,241,0.2);
  animation: ring-expand 2s ease-in-out infinite;
}

@keyframes mic-pulse {
  0%, 100% { box-shadow: 0 0 32px var(--primary-glow); }
  50% { box-shadow: 0 0 48px var(--primary-glow), 0 0 80px rgba(99,102,241,0.1); }
}
@keyframes ring-expand {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.15); opacity: 0.2; }
}

.mic-inner {
  color: var(--text-muted);
  transition: color 0.3s ease;
}
.mic-main.active .mic-inner { color: white; }

/* Transcript */
.voice-transcript {
  text-align: center;
  max-width: 400px;
  min-height: 20px;
}
.transcript-partial {
  font-size: 15px;
  color: var(--text);
  font-style: italic;
  opacity: 0.7;
}
.transcript-final {
  font-size: 15px;
  color: var(--text);
  font-style: italic;
}
.transcript-hint {
  font-size: 13px;
  color: var(--warning);
}
.transcript-placeholder {
  font-size: 13px;
  color: var(--text-muted);
  font-style: italic;
}

/* Controls */
.voice-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}
.ctrl-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--bg-2);
  border: 1px solid var(--border-strong);
  border-radius: 999px;
  color: var(--text-dim);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}
.ctrl-btn:hover {
  background: var(--bg-3);
  color: var(--text);
}
.ctrl-btn.sleeping {
  background: rgba(245,158,11,0.1);
  border-color: rgba(245,158,11,0.3);
  color: var(--warning);
}
.ctrl-interrupt {
  border-color: var(--danger);
  color: var(--danger);
}
.ctrl-interrupt:hover {
  background: var(--danger-bg);
}

.voice-error {
  font-size: 12px;
  color: var(--danger);
}
</style>
