<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAgentsStore } from '../stores/agents'
import { useChatStore } from '../stores/chat'
import { apiFetch } from '../api'
import { useToast } from '../composables/useToast'
import JarvisVoiceOrb from '../components/agent/JarvisVoiceOrb.vue'

const store = useAgentsStore()
const chatStore = useChatStore()
const router = useRouter()
const toast = useToast()

const searchQuery = ref('')
const activeCategory = ref('all')

onMounted(() => {
  store.fetchAgents()
})

const categories = [
  { id: 'all', label: 'All Agents' },
  { id: 'growth', label: 'Growth & Meta Ads' },
  { id: 'creative', label: 'Creative & Copy' },
  { id: 'research', label: 'Lead Research' },
  { id: 'operations', label: 'Operations & Market' },
]

// Professional SVG icon path definitions (Zero emojis)
const SVG_ICONS = {
  orchestrator: 'M13 2L3 14h9l-1 8 10-12h-9l1-8z', // lightning bolt
  target: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z', // shield / target
  pen: 'M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z', // pen / write
  chart: 'M18 20V10M12 20V4M6 20v-6', // bar chart
  mail: 'M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z M22 6l-10 7L2 6', // envelope
  calendar: 'M19 4H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zM16 2v4M8 2v4M3 10h18', // calendar
  trending: 'M23 6l-9.5 9.5-5-5L1 18M17 6h6v6', // trend line
  bot: 'M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83',
}

const agentMeta = {
  'Jarvis': {
    title: 'Autonomous Executive Orchestrator',
    category: 'growth',
    iconType: 'orchestrator',
    capabilities: ['Strategic Direction', 'Agent Coordination', 'Autonomous Execution'],
  },
  'LeadResearchAgent': {
    title: 'Prospect Discovery & Lead Scoring',
    category: 'research',
    iconType: 'target',
    capabilities: ['B2B Lead Discovery', 'Enrichment', 'Pain-point Extraction'],
  },
  'CreativeAgent': {
    title: 'Direct Response Copy & Ad Hooks',
    category: 'creative',
    iconType: 'pen',
    capabilities: ['Viral Hooks', 'Direct Response Copy', 'Midjourney Prompts'],
  },
  'AdsAgent': {
    title: 'Meta Ads Campaign Architecture',
    category: 'growth',
    iconType: 'chart',
    capabilities: ['Campaign Structure', 'Interest Targeting', 'ROAS Analytics'],
  },
  'OutreachAgent': {
    title: 'Personalized WhatsApp & Email Sequences',
    category: 'growth',
    iconType: 'mail',
    capabilities: ['Multi-touch Outbound', 'WhatsApp Delivery', 'Follow-up Logic'],
  },
  'PersonalAgent': {
    title: 'Calendar, Schedule & Operations',
    category: 'operations',
    iconType: 'calendar',
    capabilities: ['Task Scheduling', 'Email Triage', 'Meeting Alerts'],
  },
  'FinancialAnalyst': {
    title: 'Market Intelligence & Asset Tracking',
    category: 'operations',
    iconType: 'trending',
    capabilities: ['Market Analysis', 'Portfolio Insights', 'Macro Trends'],
  },
}

function getAgentMeta(name) {
  return agentMeta[name] || {
    title: 'Specialist AI Agent',
    category: 'growth',
    iconType: 'bot',
    capabilities: ['Specialized Automation', 'Fast Execution'],
  }
}

const filteredAgents = computed(() => {
  let list = store.agentsList || []
  const q = searchQuery.value.trim().toLowerCase()
  
  if (q) {
    list = list.filter(a =>
      (a.name || '').toLowerCase().includes(q) ||
      (a.model || '').toLowerCase().includes(q) ||
      (a.role || '').toLowerCase().includes(q)
    )
  }

  if (activeCategory.value !== 'all') {
    list = list.filter(a => {
      const meta = getAgentMeta(a.name)
      return meta.category === activeCategory.value
    })
  }

  return list
})

function openAgentDetail(agent) {
  router.push(`/agents/${encodeURIComponent(agent.name)}`)
}

function chatWithAgent(agent) {
  chatStore.setActiveAgent(agent.name)
  router.push('/chat')
}
</script>

<template>
  <div class="agents-page-wrapper max-w-7xl mx-auto px-4 py-4 space-y-12">
    <!-- Hero Stage: Jarvis Fullscreen Voice AI -->
    <JarvisVoiceOrb />

    <!-- Specialist Agents Section (Reveals smoothly on scroll) -->
    <section id="agents-roster" class="agents-roster-section pt-6">
      <!-- Section Header & Filter Controls -->
      <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8">
        <div>
          <div class="flex items-center gap-2 mb-1.5">
            <span class="clay-badge clay-badge-orange text-xs">Autonomous Team</span>
            <span class="text-xs text-slate-400 font-semibold uppercase tracking-wider">IconEdge Technologies</span>
          </div>
          <h2 class="text-2xl md:text-3xl font-black text-slate-900 tracking-tight">
            Specialist Agents Division
          </h2>
          <p class="text-xs text-slate-500 font-medium mt-1">
            Dedicated autonomous workers coordinating with Jarvis on strategy and execution.
          </p>
        </div>

        <!-- Search Bar -->
        <div class="w-full md:w-80">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search agents or capabilities..."
            class="clay-input w-full text-xs font-medium"
          />
        </div>
      </div>

      <!-- Category Filter Pills -->
      <div class="flex items-center gap-2.5 mb-8 overflow-x-auto pb-2">
        <button
          v-for="cat in categories"
          :key="cat.id"
          @click="activeCategory = cat.id"
          class="clay-btn text-xs py-2 px-4 whitespace-nowrap transition-all"
          :class="{
            'clay-btn-orange font-bold': activeCategory === cat.id,
            'text-slate-600 font-semibold': activeCategory !== cat.id
          }"
        >
          {{ cat.label }}
        </button>
      </div>

      <!-- Agent Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="agent in filteredAgents"
          :key="agent.name"
          @click="openAgentDetail(agent)"
          class="clay-card clay-card-interactive p-6 flex flex-col justify-between group"
        >
          <div>
            <!-- Top Header: SVG Icon + Name + Active Status Badge -->
            <div class="flex items-start justify-between gap-3 mb-4">
              <div class="flex items-center gap-3.5">
                <div class="w-12 h-12 rounded-2xl flex items-center justify-center bg-orange-50 border border-orange-200/60 shadow-sm text-[#ff6b00]">
                  <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path :d="SVG_ICONS[getAgentMeta(agent.name).iconType] || SVG_ICONS.bot" />
                  </svg>
                </div>
                <div>
                  <h3 class="text-base font-bold text-slate-900 group-hover:text-[#ff6b00] transition-colors">
                    {{ agent.name }}
                  </h3>
                  <span class="text-[11px] text-slate-500 font-medium block">
                    {{ getAgentMeta(agent.name).title }}
                  </span>
                </div>
              </div>

              <!-- Status -->
              <span class="clay-badge text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 inline-block animate-pulse"></span>
                Active
              </span>
            </div>

            <!-- Model Badge & Attached Tools -->
            <div class="flex flex-wrap items-center gap-1.5 mb-4">
              <span class="clay-badge text-[10px] text-slate-700 bg-slate-50">
                {{ agent.model || 'gemini-3.6-flash' }}
              </span>
              <span 
                v-if="agent.servers && agent.servers.length"
                class="clay-badge text-[10px] text-orange-800 bg-orange-50"
              >
                {{ agent.servers.length }} Connected Tools
              </span>
            </div>

            <!-- Capabilities -->
            <div class="space-y-1.5 my-3">
              <div 
                v-for="(cap, idx) in getAgentMeta(agent.name).capabilities" 
                :key="idx"
                class="flex items-center gap-2 text-xs text-slate-600 font-medium"
              >
                <svg class="w-3.5 h-3.5 text-[#ff6b00] flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>{{ cap }}</span>
              </div>
            </div>
          </div>

          <!-- Card Footer Action -->
          <div class="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
            <span class="text-xs text-slate-400 group-hover:text-[#ff6b00] font-bold transition-colors flex items-center gap-1">
              Configure Agent
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </span>
            
            <button 
              @click.stop="chatWithAgent(agent)"
              class="clay-btn clay-btn-orange text-xs py-1.5 px-3.5 font-semibold"
            >
              Open Direct Chat
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.agents-page-wrapper {
  min-height: 100vh;
}
</style>
