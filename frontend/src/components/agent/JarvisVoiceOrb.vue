<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { apiFetch } from '../../api'
import { useToast } from '../../composables/useToast'
import { useAudioPlayerStore } from '../../stores/audioPlayer'

const toast = useToast()
const audioStore = useAudioPlayerStore()

// Voice states: 'idle' | 'listening' | 'thinking' | 'speaking'
const voiceState = ref('idle')
const isMicActive = ref(false)
const transcript = ref('')
const responseText = ref('')
const lastSpokenText = ref('')

const canvasRef = ref(null)
let animId = null
let recognition = null

// ─── 100% Alpha Transparent Holographic Orb Engine ───
// Generates fluid, electric glowing energy filaments with ZERO black background
function startHologramEngine() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  let t = 0
  const dpr = window.devicePixelRatio || 1
  const size = 480
  canvas.width = size * dpr
  canvas.height = size * dpr
  ctx.scale(dpr, dpr)

  const cx = size / 2
  const cy = size / 2

  function render() {
    ctx.clearRect(0, 0, size, size)

    const isSpeaking = voiceState.value === 'speaking'
    const isListening = voiceState.value === 'listening'
    const isThinking = voiceState.value === 'thinking'

    const speed = isSpeaking ? 0.045 : (isListening ? 0.03 : 0.015)
    t += speed

    const baseRadius = isSpeaking ? 140 : (isListening ? 130 : 120)
    const ringCount = isSpeaking ? 16 : 10

    // Draw multidimensional glowing ribbons
    for (let r = 0; r < ringCount; r++) {
      const angleOffset = (r * Math.PI) / (ringCount / 2) + t * (r % 2 === 0 ? 1 : -1)
      const currentRadius = baseRadius + Math.sin(t * 2 + r) * (isSpeaking ? 18 : 8)

      ctx.beginPath()

      for (let a = 0; a <= Math.PI * 2; a += 0.08) {
        // Complex fluid turbulence
        const distortion = 
          Math.sin(a * 4 + t * 3 + r) * (isSpeaking ? 22 : (isListening ? 14 : 7)) +
          Math.cos(a * 6 - t * 2 + r) * (isSpeaking ? 12 : 5) +
          Math.sin(a * 2 + angleOffset) * 8

        const rad = currentRadius + distortion
        const x = cx + Math.cos(a + angleOffset * 0.2) * rad
        const y = cy + Math.sin(a + angleOffset * 0.2) * (rad * 0.9)

        if (a === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      }

      ctx.closePath()

      // Gradient color theme: Vibrant Electric Orange & Amber Glow
      let strokeColor
      if (isSpeaking) {
        strokeColor = `rgba(${255}, ${107 + (r * 8) % 80}, ${10}, ${0.45 + (r % 3) * 0.15})`
      } else if (isListening) {
        strokeColor = `rgba(${16}, ${185}, ${129}, ${0.45 + (r % 3) * 0.15})` // emerald listening
      } else if (isThinking) {
        strokeColor = `rgba(${245}, ${158}, ${11}, ${0.45 + (r % 3) * 0.15})` // amber thinking
      } else {
        strokeColor = `rgba(${255}, ${122}, ${24}, ${0.35 + (r % 2) * 0.15})` // calm orange standby
      }

      ctx.strokeStyle = strokeColor
      ctx.lineWidth = isSpeaking ? (2.5 + (r % 3)) : 1.8
      ctx.shadowColor = isSpeaking ? '#ff5100' : '#ff7a18'
      ctx.shadowBlur = isSpeaking ? 25 : 12
      ctx.stroke()
    }

    // Core energetic center glow
    const coreGrad = ctx.createRadialGradient(cx, cy, 10, cx, cy, baseRadius * 0.8)
    if (isSpeaking) {
      coreGrad.addColorStop(0, 'rgba(255, 107, 0, 0.4)')
      coreGrad.addColorStop(0.5, 'rgba(255, 122, 24, 0.15)')
      coreGrad.addColorStop(1, 'rgba(255, 255, 255, 0)')
    } else if (isListening) {
      coreGrad.addColorStop(0, 'rgba(16, 185, 129, 0.35)')
      coreGrad.addColorStop(0.5, 'rgba(16, 185, 129, 0.1)')
      coreGrad.addColorStop(1, 'rgba(255, 255, 255, 0)')
    } else {
      coreGrad.addColorStop(0, 'rgba(255, 122, 24, 0.25)')
      coreGrad.addColorStop(0.5, 'rgba(255, 122, 24, 0.08)')
      coreGrad.addColorStop(1, 'rgba(255, 255, 255, 0)')
    }

    ctx.fillStyle = coreGrad
    ctx.beginPath()
    ctx.arc(cx, cy, baseRadius * 0.8, 0, Math.PI * 2)
    ctx.fill()

    animId = requestAnimationFrame(render)
  }

  render()
}

// Setup Speech Recognition
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) {
    console.warn('Speech Recognition not supported natively in this browser.')
    return
  }

  recognition = new SpeechRecognition()
  recognition.continuous = true
  recognition.interimResults = true
  recognition.lang = 'en-US'

  recognition.onstart = () => {
    isMicActive.value = true
    if (voiceState.value === 'idle') voiceState.value = 'listening'
  }

  recognition.onresult = (event) => {
    let interim = ''
    let final = ''

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      const trans = event.results[i][0].transcript
      if (event.results[i].isFinal) {
        final += trans
      } else {
        interim += trans
      }
    }

    const currentText = final || interim
    transcript.value = currentText

    if (final && final.trim()) {
      handleUserVoiceInput(final.trim())
    }
  }

  recognition.onerror = (event) => {
    console.warn('Speech recognition error:', event.error)
    if (event.error === 'not-allowed') {
      isMicActive.value = false
      voiceState.value = 'idle'
      toast.warning('Microphone permission denied. Click to retry.')
    }
  }

  recognition.onend = () => {
    if (isMicActive.value && voiceState.value !== 'speaking' && voiceState.value !== 'thinking') {
      try {
        recognition.start()
      } catch (e) {}
    }
  }
}

function toggleMic() {
  if (!recognition) initSpeechRecognition()
  if (!recognition) {
    toast.error('Voice input is not supported in this browser. Please use Chrome/Edge.')
    return
  }

  if (isMicActive.value) {
    isMicActive.value = false
    voiceState.value = 'idle'
    try { recognition.stop() } catch (e) {}
  } else {
    isMicActive.value = true
    voiceState.value = 'listening'
    try { recognition.start() } catch (e) {}
  }
}

async function handleUserVoiceInput(message) {
  if (!message || !message.trim()) return

  const cleanMsg = message.replace(/^(hey\s+)?jarvis[,:]?\s*/i, '').trim() || message

  voiceState.value = 'thinking'
  lastSpokenText.value = message

  let text = ''
  let audioUrl = null

  try {
    const data = await apiFetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message: cleanMsg }),
    })

    text = (data && data.response) ? data.response : (typeof data === 'string' ? data : '')
    audioUrl = data?.audio || data?.audio_url || data?.playback_url || null
  } catch (err) {
    console.warn('Backend chat response error or rate limit, switching to executive standby:', err)
    text = `Greetings Owen. I am standing by and ready to coordinate your specialist agents, research leads, or audit your ad campaigns.`
  }

  if (!text) {
    text = 'At your service, Owen.'
  }

  responseText.value = text
  await playJarvisVoice(text, audioUrl)
}

async function playJarvisVoice(text, audioUrl) {
  if (recognition && isMicActive.value) {
    try { recognition.stop() } catch (e) {}
  }

  if (audioUrl) {
    voiceState.value = 'speaking'
    audioStore.playChatTts(audioUrl)
    
    // Return orb to idle when playback completes
    const pollId = setInterval(() => {
      if (!audioStore.isPlaying && audioStore.playbackType !== 'chatTts') {
        clearInterval(pollId)
        voiceState.value = 'idle'
        if (isMicActive.value && recognition) {
          try { recognition.start() } catch (e) {}
        }
      }
    }, 250)
  } else {
    voiceState.value = 'idle'
  }
}

function sendPreset(prompt) {
  transcript.value = prompt
  handleUserVoiceInput(prompt)
}

function scrollToAgents() {
  const el = document.getElementById('agents-roster')
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  }
}

onMounted(() => {
  startHologramEngine()
  initSpeechRecognition()
})

onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId)
  if (recognition) {
    try { recognition.stop() } catch (e) {}
  }
  if (currentAudio) {
    currentAudio.pause()
  }
  if (synth) {
    synth.cancel()
  }
})
</script>

<template>
  <section class="jarvis-fullscreen-hero relative flex flex-col items-center justify-center w-full min-h-[calc(100vh-140px)] p-4 md:p-8 overflow-hidden">
    <!-- Ambient Radiant Glow -->
    <div class="aura-glow-outer absolute pointer-events-none" :class="{ 'aura-active': voiceState !== 'idle' }"></div>
    <div class="aura-glow-inner absolute pointer-events-none" :class="{ 'aura-active': voiceState === 'speaking' || voiceState === 'listening' }"></div>

    <!-- Center Stage: Big Centered Holographic AI Orb (100% Dead Center, 0% Black Background) -->
    <div class="relative flex flex-col items-center justify-center my-auto z-10 w-full">
      
      <!-- Expanding Soundwave Waves when speaking or listening -->
      <div 
        v-if="voiceState === 'listening' || voiceState === 'speaking'"
        class="absolute w-[380px] h-[380px] sm:w-[480px] sm:h-[480px] md:w-[600px] md:h-[600px] rounded-full border-2 border-[#ff6b00]/40 animate-ping pointer-events-none"
      ></div>
      <div 
        v-if="voiceState === 'speaking'"
        class="absolute w-[440px] h-[440px] sm:w-[540px] sm:h-[540px] md:w-[660px] md:h-[660px] rounded-full border border-[#ff7a18]/40 animate-pulse-ring pointer-events-none"
      ></div>

      <!-- Main Big Centered Floating Hologram Container -->
      <div 
        @click="toggleMic"
        class="hologram-stage relative flex items-center justify-center cursor-pointer transition-transform duration-300 transform hover:scale-105"
      >
        <!-- 100% Alpha-Transparent Dynamic Canvas Hologram Orb -->
        <canvas 
          ref="canvasRef"
          class="w-72 h-72 sm:w-96 sm:h-96 md:w-[480px] md:h-[480px] lg:w-[520px] lg:h-[520px] pointer-events-none"
          :class="{
            'orb-speaking-glow': voiceState === 'speaking',
            'orb-listening-glow': voiceState === 'listening',
            'orb-thinking-glow': voiceState === 'thinking',
          }"
        ></canvas>

        <!-- Floating Orange Mic Trigger Button -->
        <div 
          class="absolute bottom-4 right-4 md:bottom-8 md:right-8 w-14 h-14 rounded-full flex items-center justify-center clay-btn-orange shadow-2xl transition-transform duration-200 z-20"
        >
          <svg v-if="voiceState === 'listening'" class="w-6 h-6 text-white animate-pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" x2="12" y1="19" y2="22" />
          </svg>
          <svg v-else-if="voiceState === 'thinking'" class="w-6 h-6 text-white animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-linecap="round"/>
          </svg>
          <svg v-else-if="voiceState === 'speaking'" class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
          </svg>
          <svg v-else class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" x2="12" y1="19" y2="22" />
          </svg>
        </div>
      </div>

      <!-- Dialogue Bubbles (User Speech & Jarvis Response) -->
      <div v-if="lastSpokenText || responseText" class="w-full max-w-2xl mt-6 space-y-3">
        <!-- User Voice Query -->
        <div v-if="lastSpokenText" class="flex items-start justify-end gap-3">
          <div class="bg-gradient-to-r from-orange-50 to-amber-50 border border-orange-200/90 rounded-2xl rounded-tr-sm px-5 py-3 shadow-sm text-right">
            <span class="text-[11px] font-bold text-[#ea580c] uppercase tracking-wider block mb-0.5">You</span>
            <p class="text-sm text-slate-900 font-semibold leading-relaxed">"{{ lastSpokenText }}"</p>
          </div>
        </div>

        <!-- Jarvis Voice Response -->
        <div v-if="responseText" class="flex items-start justify-start gap-3">
          <div class="bg-white border border-slate-200/90 rounded-2xl rounded-tl-sm p-5 shadow-lg text-left w-full">
            <div class="flex items-center justify-between mb-1.5 pb-1 border-b border-slate-100">
              <span class="text-xs font-black text-[#ff6b00] uppercase tracking-wider">Jarvis Response</span>
              <span class="text-[10px] text-slate-400 font-semibold">Spoken Audio Response</span>
            </div>
            <p class="text-sm text-slate-800 whitespace-pre-wrap leading-relaxed font-normal">{{ responseText }}</p>
          </div>
        </div>
      </div>

      <!-- Quick Action Voice Preset Buttons (Zero Emojis, Pure Professional) -->
      <div class="flex flex-wrap items-center justify-center gap-3 mt-8">
        <button 
          @click="sendPreset('Give me a full executive briefing on IconEdge growth and current agent readiness.')"
          class="clay-btn text-xs py-2.5 px-4 font-semibold hover:text-[#ff6b00]"
        >
          Executive Briefing
        </button>

        <button 
          @click="sendPreset('Lead Research Agent: Find 5 high-converting prospective clients in technology and marketing.')"
          class="clay-btn text-xs py-2.5 px-4 font-semibold hover:text-[#ff6b00]"
        >
          Research Tech Leads
        </button>

        <button 
          @click="sendPreset('Creative Agent: Write 3 direct-response viral ad hooks for our growth service.')"
          class="clay-btn text-xs py-2.5 px-4 font-semibold hover:text-[#ff6b00]"
        >
          Generate Ad Hooks
        </button>

        <button 
          @click="sendPreset('Ads Agent: Show me the status and metrics of our Meta Ad campaigns.')"
          class="clay-btn text-xs py-2.5 px-4 font-semibold hover:text-[#ff6b00]"
        >
          Audit Meta Ads
        </button>

        <button 
          @click="sendPreset('Convene an executive board meeting with Lead Research, Creative, and Ads agents.')"
          class="clay-btn text-xs py-2.5 px-4 font-semibold hover:text-[#ff6b00]"
        >
          Board Meeting
        </button>
      </div>

      <!-- Scroll to Agents Roster Indicator -->
      <button 
        @click="scrollToAgents"
        class="text-xs font-bold text-slate-500 hover:text-[#ff6b00] transition-colors flex items-center gap-1.5 mt-6 group"
      >
        <span>View Specialist Agents Division</span>
        <svg class="w-4 h-4 transform group-hover:translate-y-1 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M6 9l6 6 6-6"/>
        </svg>
      </button>
    </div>
  </section>
</template>

<style scoped>
.jarvis-fullscreen-hero {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.hologram-stage {
  background: transparent !important;
  padding: 0 !important;
  border: none !important;
  box-shadow: none !important;
}

.orb-speaking-glow {
  filter: drop-shadow(0 0 45px rgba(255, 107, 0, 0.95)) drop-shadow(0 0 20px rgba(255, 122, 24, 0.8));
  transform: scale(1.06);
}

.orb-listening-glow {
  filter: drop-shadow(0 0 30px rgba(16, 185, 129, 0.75));
}

.orb-thinking-glow {
  filter: drop-shadow(0 0 30px rgba(245, 158, 11, 0.75));
}

.aura-glow-outer {
  width: 620px;
  height: 620px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 107, 0, 0.16) 0%, rgba(255, 107, 0, 0) 70%);
  filter: blur(40px);
  transition: all 0.5s ease;
  opacity: 0.5;
}

.aura-glow-inner {
  width: 480px;
  height: 480px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 122, 24, 0.25) 0%, rgba(255, 107, 0, 0) 70%);
  filter: blur(25px);
  transition: all 0.5s ease;
  opacity: 0.4;
}

.aura-active {
  opacity: 1 !important;
  transform: scale(1.25);
}
</style>
