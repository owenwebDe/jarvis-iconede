<template>
  <div class="jarvis" :class="[status, { fullscreen }]">
    <div class="bg" />
    
    <!-- Jarvis hologram GIF -->
    <div class="hologram" :class="status">
      <img 
        src="https://i.gifer.com/yy3.gif" 
        alt="Jarvis Core" 
        class="holo-img"
      />
      <div class="holo-glow" />
    </div>
    
    <!-- Status -->
    <p class="status">{{ statusText }}</p>
    
    <!-- Transcript -->
    <p class="transcript" v-if="transcript">{{ transcript }}</p>
    
    <!-- Controls -->
    <div class="controls">
      <!-- Fullscreen toggle -->
      <button class="ctrl-btn" @click="toggleFullscreen" :title="fullscreen ? 'Exit fullscreen' : 'Fullscreen'">
        <svg v-if="!fullscreen" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
        </svg>
        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>
        </svg>
      </button>
      
      <!-- Mic -->
      <button class="mic" :class="{ on: isListening }" @click="toggle">
        <svg v-if="!isListening" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="2" width="6" height="12" rx="3"/>
          <path d="M5 10c0 4.4 3.6 8 8 8s8-3.6 8-8"/>
          <line x1="12" y1="18" x2="12" y2="22" stroke-linecap="round"/>
        </svg>
        <svg v-else width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="2" width="6" height="12" rx="3" fill="currentColor"/>
          <path d="M5 10c0 4.4 3.6 8 8 8s8-3.6 8-8"/>
          <line x1="12" y1="18" x2="12" y2="22" stroke-linecap="round"/>
        </svg>
      </button>
      
      <!-- Close (only when not fullscreen) -->
      <button v-if="!fullscreen" class="ctrl-btn" @click="$emit('close')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useVoiceSession } from '../../composables/useVoiceSession'

const emit = defineEmits(['close'])
const { status, start, stop, partialTranscript } = useVoiceSession()

const isListening = computed(() => status.value === 'listening')
const fullscreen = ref(false)
const transcript = ref('')

const statusText = computed(() => ({
  idle: 'STANDBY', connecting: 'CONNECTING', loading_stt: 'LOADING',
  listening: 'LISTENING', thinking: 'PROCESSING', speaking: 'SPEAKING', error: 'ERROR'
}[status.value] || ''))

function toggle() { isListening.value ? stop() : start() }

function toggleFullscreen() {
  fullscreen.value = !fullscreen.value
}

// ESC to exit fullscreen
function onKeydown(e) {
  if (e.key === 'Escape' && fullscreen.value) fullscreen.value = false
}

watch(partialTranscript, (t) => { if (t) transcript.value = t })

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.jarvis {
  position: relative; width: 100%; height: 100%; min-height: 500px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  overflow: hidden; color: #d7ecfa; font-family: system-ui, sans-serif;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Fullscreen mode */
.jarvis.fullscreen {
  position: fixed; inset: 0; z-index: 9999;
  min-height: 100vh; background: #020408;
}

.bg {
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at 50% 45%, #0a1628 0%, #060e1a 50%, #020408 100%);
}

/* Hologram container */
.hologram {
  position: relative;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Default / idle size */
.hologram { width: 300px; height: 300px; }

/* Listening = smaller */
.hologram.listening { width: 220px; height: 220px; }

/* Thinking = medium */
.hologram.thinking { width: 280px; height: 280px; }

/* Speaking = BIG */
.hologram.speaking { width: 480px; height: 480px; }

/* Fullscreen speaking = even bigger */
.fullscreen .hologram.speaking { width: 600px; height: 600px; }
.fullscreen .hologram.listening { width: 300px; height: 300px; }
.fullscreen .hologram.thinking { width: 380px; height: 380px; }
.fullscreen .hologram { width: 350px; height: 350px; }

.holo-img {
  width: 100%; height: 100%; object-fit: contain;
  filter: brightness(0.8) saturate(1.2);
  transition: filter 0.4s ease, transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0.7;
}

.listening .holo-img {
  filter: brightness(0.9) saturate(1.3) hue-rotate(-10deg) drop-shadow(0 0 20px rgba(0, 255, 150, 0.3));
  opacity: 0.85;
}
.thinking .holo-img {
  filter: brightness(1) saturate(1.3) hue-rotate(30deg) drop-shadow(0 0 30px rgba(255, 200, 0, 0.3));
  opacity: 0.9;
}
.speaking .holo-img {
  filter: brightness(1.1) saturate(1.4) drop-shadow(0 0 50px rgba(0, 200, 255, 0.5));
  opacity: 1;
}
.error .holo-img {
  filter: brightness(0.7) saturate(0.5) drop-shadow(0 0 20px rgba(255, 50, 50, 0.3));
}

.holo-glow {
  position: absolute; inset: -60px; border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 150, 255, 0.12) 0%, transparent 70%);
  pointer-events: none;
  transition: all 0.5s ease;
  animation: glow-pulse 4s ease-in-out infinite;
}

.speaking .holo-glow {
  inset: -80px;
  background: radial-gradient(circle, rgba(0, 200, 255, 0.2) 0%, transparent 70%);
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.05); }
}

/* Status */
.status {
  margin-top: 20px; font-size: 12px; letter-spacing: 0.35em;
  color: #00b4ff; font-weight: 600;
  text-shadow: 0 0 10px rgba(0, 180, 255, 0.5);
  transition: all 0.3s ease;
}

.listening .status { color: #00ff96; text-shadow: 0 0 10px rgba(0, 255, 150, 0.5); }
.thinking .status { color: #ffc800; text-shadow: 0 0 10px rgba(255, 200, 0, 0.5); }
.speaking .status { color: #00c8ff; text-shadow: 0 0 12px rgba(0, 200, 255, 0.6); }
.error .status { color: #ff5050; }

/* Transcript */
.transcript {
  margin-top: 8px; font-size: 14px; color: rgba(255,255,255,0.6);
  max-width: 400px; text-align: center; min-height: 20px;
}

/* Controls */
.controls {
  position: absolute; bottom: 28px;
  display: flex; align-items: center; gap: 16px;
}

/* Mic */
.mic {
  width: 64px; height: 64px; border-radius: 50%;
  border: 2px solid rgba(0, 180, 255, 0.3); background: rgba(0, 20, 40, 0.6);
  color: #54728a; display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.25s; backdrop-filter: blur(4px);
}
.mic:hover { border-color: #00b4ff; color: #00b4ff; }
.mic.on {
  border-color: #00b4ff; color: #00b4ff;
  background: rgba(0, 180, 255, 0.15);
  box-shadow: 0 0 30px rgba(0, 180, 255, 0.3), inset 0 0 20px rgba(0, 180, 255, 0.1);
  animation: mic-pulse 2s ease-in-out infinite;
}
@keyframes mic-pulse {
  0%, 100% { box-shadow: 0 0 30px rgba(0, 180, 255, 0.3); }
  50% { box-shadow: 0 0 50px rgba(0, 180, 255, 0.5); }
}

/* Control buttons */
.ctrl-btn {
  width: 40px; height: 40px; border-radius: 50%;
  border: 1px solid rgba(0, 180, 255, 0.2); background: rgba(0, 20, 40, 0.4);
  color: #54728a; display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: 0.2s; backdrop-filter: blur(4px);
}
.ctrl-btn:hover { border-color: #00b4ff; color: #00b4ff; }
</style>
