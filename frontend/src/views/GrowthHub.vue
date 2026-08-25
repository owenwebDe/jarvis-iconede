<script setup>
import { ref, onMounted, computed } from 'vue'
import { apiFetch } from '../api'

const activeTab = ref('leads') // 'leads' | 'creatives' | 'campaigns' | 'meetings'
const loading = ref(false)

// ── State ──
const prospects = ref([])
const creatives = ref([])
const campaigns = ref([])
const activeMeeting = ref(null)
const meetingTranscript = ref([])

const searchQuery = ref('')
const selectedCountry = ref('all')

const newProspectModal = ref(false)
const newProspect = ref({
  company_name: '',
  contact_name: '',
  email: '',
  country: 'Global',
  industry: '',
  notes: '',
})

async function fetchProspects() {
  loading.value = true
  try {
    const q = searchQuery.value ? `&query=${encodeURIComponent(searchQuery.value)}` : ''
    const c = selectedCountry.value !== 'all' ? `&country=${encodeURIComponent(selectedCountry.value)}` : ''
    const res = await apiFetch(`/api/shared-memory/prospects?limit=50${q}${c}`)
    prospects.value = res.prospects || []
  } catch (err) {
    console.error('Failed to fetch prospects:', err)
  } finally {
    loading.value = false
  }
}

async function fetchCreatives() {
  loading.value = true
  try {
    const res = await apiFetch('/api/shared-memory/creatives?limit=50')
    creatives.value = res.creatives || []
  } catch (err) {
    console.error('Failed to fetch creatives:', err)
  } finally {
    loading.value = false
  }
}

async function fetchCampaigns() {
  loading.value = true
  try {
    const res = await apiFetch('/api/shared-memory/campaigns?limit=50')
    campaigns.value = res.campaigns || []
  } catch (err) {
    console.error('Failed to fetch campaigns:', err)
  } finally {
    loading.value = false
  }
}

async function saveManualProspect() {
  if (!newProspect.value.company_name) return
  try {
    await apiFetch('/api/shared-memory/prospects', {
      method: 'POST',
      body: JSON.stringify(newProspect.value),
    })
    newProspectModal.value = false
    newProspect.value = { company_name: '', contact_name: '', email: '', country: 'Global', industry: '', notes: '' }
    await fetchProspects()
  } catch (err) {
    alert('Error saving prospect: ' + err.message)
  }
}

onMounted(async () => {
  await fetchProspects()
  await fetchCreatives()
  await fetchCampaigns()
})
</script>

<template>
  <div class="growth-hub">
    <!-- Header -->
    <header class="growth-header">
      <div class="header-left">
        <div class="growth-badge">GROWTH ENGINE</div>
        <h1 class="growth-title">IconEdge Growth Hub</h1>
        <p class="growth-subtitle">Autonomous Client Acquisition, Ad Creatives & Multi-Agent Meeting Engine</p>
      </div>
      <div class="header-actions">
        <button class="clay-btn clay-btn-orange" @click="newProspectModal = true">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
          Add Prospect
        </button>
      </div>
    </header>

    <!-- Stats Overview -->
    <div class="stats-row">
      <div class="stat-card clay-card">
        <div class="stat-icon stat-icon--leads">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ prospects.length }}</span>
          <span class="stat-label">Global Prospects</span>
        </div>
      </div>
      <div class="stat-card clay-card">
        <div class="stat-icon stat-icon--creative">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z"/></svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ creatives.length }}</span>
          <span class="stat-label">Ad Creatives</span>
        </div>
      </div>
      <div class="stat-card clay-card">
        <div class="stat-icon stat-icon--campaigns">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ campaigns.length }}</span>
          <span class="stat-label">Campaigns</span>
        </div>
      </div>
      <div class="stat-card clay-card">
        <div class="stat-icon stat-icon--safety">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">PAUSED</span>
          <span class="stat-label">Safety Mode</span>
        </div>
      </div>
    </div>

    <!-- Nav Tabs -->
    <div class="growth-tabs">
      <button 
        class="growth-tab" 
        :class="{ 'growth-tab--active': activeTab === 'leads' }"
        @click="activeTab = 'leads'; fetchProspects()"
      >
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
        Prospects ({{ prospects.length }})
      </button>
      <button 
        class="growth-tab" 
        :class="{ 'growth-tab--active': activeTab === 'creatives' }"
        @click="activeTab = 'creatives'; fetchCreatives()"
      >
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z"/></svg>
        Creatives ({{ creatives.length }})
      </button>
      <button 
        class="growth-tab" 
        :class="{ 'growth-tab--active': activeTab === 'campaigns' }"
        @click="activeTab = 'campaigns'; fetchCampaigns()"
      >
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>
        Campaigns ({{ campaigns.length }})
      </button>
    </div>

    <!-- TAB 1: Prospects & Leads -->
    <section v-if="activeTab === 'leads'" class="tab-content">
      <div class="filter-bar">
        <input 
          v-model="searchQuery" 
          @input="fetchProspects" 
          placeholder="Search by company, contact, or notes..." 
          class="input-search"
        />
        <select v-model="selectedCountry" @change="fetchProspects" class="select-country">
          <option value="all">All Regions</option>
          <option value="United Kingdom">United Kingdom</option>
          <option value="Germany">Germany</option>
          <option value="United States">United States</option>
          <option value="Nigeria">Nigeria</option>
          <option value="Global">Global</option>
        </select>
      </div>

      <div class="grid-cards">
        <div v-for="lead in prospects" :key="lead.id" class="card lead-card">
          <div class="card-header">
            <h3 class="card-title">{{ lead.company_name }}</h3>
            <span class="badge" :class="`badge--${lead.status}`">{{ lead.status.toUpperCase() }}</span>
          </div>
          <p class="lead-contact"><strong>Contact:</strong> {{ lead.contact_name || 'N/A' }} ({{ lead.email || 'No email' }})</p>
          <p class="lead-location"><strong>Location:</strong> {{ lead.city ? lead.city + ', ' : '' }}{{ lead.country }}</p>
          <p class="lead-industry"><strong>Industry:</strong> {{ lead.industry || 'General SMB' }}</p>
          <div class="lead-score-bar">
            <span class="score-label">Lead Score: {{ lead.lead_score }}/100</span>
            <div class="score-track">
              <div class="score-fill" :style="{ width: `${lead.lead_score}%` }"></div>
            </div>
          </div>
          <div v-if="lead.notes" class="lead-notes">
            <p>{{ lead.notes }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 2: Creatives & Copy -->
    <section v-if="activeTab === 'creatives'" class="tab-content">
      <div class="grid-cards">
        <div v-for="c in creatives" :key="c.id" class="card creative-card">
          <div class="card-header">
            <h3 class="card-title">{{ c.title }}</h3>
            <span class="badge badge--creative">{{ c.hook_type.toUpperCase() }}</span>
          </div>
          <h4 class="creative-headline">"{{ c.headline }}"</h4>
          <p class="creative-body">{{ c.body_copy }}</p>
          <div class="creative-meta">
            <span class="cta-pill">CTA: {{ c.call_to_action }}</span>
            <span class="audience-pill" v-if="c.target_audience">Audience: {{ c.target_audience }}</span>
          </div>
          <div v-if="c.image_prompt" class="image-prompt-box">
            <strong>AI Image Prompt:</strong>
            <p>{{ c.image_prompt }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 3: Meta Ads Campaigns -->
    <section v-if="activeTab === 'campaigns'" class="tab-content">
      <div class="grid-cards">
        <div v-for="camp in campaigns" :key="camp.id" class="card campaign-card">
          <div class="card-header">
            <h3 class="card-title">{{ camp.name }}</h3>
            <span class="badge badge--safety" :class="{ 'badge--paused': camp.status === 'PAUSED' }">
              {{ camp.status }}
            </span>
          </div>
          <p><strong>Objective:</strong> {{ camp.objective }}</p>
          <p><strong>Daily Budget:</strong> ${{ camp.daily_budget }}/day</p>
          <div class="safety-banner">
            Safe Mode Active: All campaigns held in PAUSED state until authorized.
          </div>
        </div>
      </div>
    </section>

    <!-- Add Prospect Modal -->
    <div v-if="newProspectModal" class="modal-overlay" @click.self="newProspectModal = false">
      <div class="modal-card">
        <h2>Add Global Prospect</h2>
        <div class="form-group">
          <label>Company Name</label>
          <input v-model="newProspect.company_name" placeholder="e.g. Acme Global Logistics" />
        </div>
        <div class="form-group">
          <label>Contact Name</label>
          <input v-model="newProspect.contact_name" placeholder="e.g. John Doe" />
        </div>
        <div class="form-group">
          <label>Email</label>
          <input v-model="newProspect.email" placeholder="john@acme.com" />
        </div>
        <div class="form-group">
          <label>Country / City</label>
          <input v-model="newProspect.country" placeholder="e.g. United Kingdom" />
        </div>
        <div class="form-group">
          <label>Industry</label>
          <input v-model="newProspect.industry" placeholder="e.g. Supply Chain & Freight" />
        </div>
        <div class="form-group">
          <label>Pain Points / Notes</label>
          <textarea v-model="newProspect.notes" placeholder="e.g. Looking to reduce customs bottlenecks"></textarea>
        </div>
        <div class="modal-actions">
          <button class="clay-btn" @click="newProspectModal = false">Cancel</button>
          <button class="clay-btn clay-btn-orange" @click="saveManualProspect">Save Prospect</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.growth-hub {
  max-width: 1200px;
  margin: 0 auto;
  color: var(--text-heading);
}

/* ── Header ── */
.growth-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
}
.growth-badge {
  display: inline-block;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: var(--accent-orange);
  background: var(--accent-orange-light);
  border: 1px solid var(--border-orange);
  border-radius: 9999px;
  padding: 4px 12px;
  margin-bottom: 8px;
}
.growth-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--text-heading);
  margin: 0 0 4px 0;
  letter-spacing: -0.02em;
}
.growth-subtitle {
  font-size: 14px;
  color: var(--text-nav);
  margin: 0;
  max-width: 500px;
}

/* ── Stats Row ── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--clay-shadow-inner);
}
.stat-icon--leads { background: #eef2ff; color: #6366f1; }
.stat-icon--creative { background: #fdf2f8; color: #ec4899; }
.stat-icon--campaigns { background: #f0f9ff; color: #0ea5e9; }
.stat-icon--safety { background: #f0fdf4; color: #22c55e; }
.stat-content { display: flex; flex-direction: column; }
.stat-value {
  font-size: 22px;
  font-weight: 800;
  color: var(--text-heading);
  line-height: 1.2;
}
.stat-label {
  font-size: 12px;
  color: var(--text-nav);
  font-weight: 500;
  margin-top: 2px;
}

/* ── Tabs ── */
.growth-tabs {
  display: flex;
  gap: 6px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 24px;
}
.growth-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: none;
  color: var(--text-nav);
  padding: 10px 18px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
  border-radius: 10px 10px 0 0;
}
.growth-tab:hover {
  color: var(--text-heading);
  background: rgba(255,107,0,0.04);
}
.growth-tab--active {
  color: var(--accent-orange);
  border-bottom-color: var(--accent-orange);
  background: var(--accent-orange-light);
}

/* ── Filter Bar ── */
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.input-search, .select-country {
  background: var(--bg-base);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 10px 18px;
  color: var(--text-heading);
  font-size: 13px;
  box-shadow: var(--clay-shadow-inner);
  outline: none;
  transition: border-color 0.2s;
}
.input-search { flex: 1; }
.input-search:focus, .select-country:focus {
  border-color: var(--accent-orange);
}
.select-country { min-width: 160px; }

/* ── Card Grid ── */
.grid-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 18px;
}
.card {
  background: var(--bg-card);
  border-radius: 20px;
  padding: 22px;
  box-shadow: 8px 8px 20px rgba(166,175,195,0.3), -8px -8px 20px rgba(255,255,255,0.95);
  border: 1px solid rgba(255,255,255,0.8);
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}
.card:hover {
  transform: translateY(-4px);
  box-shadow: 12px 12px 28px rgba(166,175,195,0.4), -12px -12px 28px rgba(255,255,255,1);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-heading);
  margin: 0;
}

/* ── Badges ── */
.badge {
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  box-shadow: 2px 2px 6px rgba(166,175,195,0.2), -2px -2px 6px rgba(255,255,255,0.8);
}
.badge--new { background: #f1f5f9; color: #64748b; }
.badge--qualified { background: #ecfdf5; color: #059669; }
.badge--contacted { background: #eff6ff; color: #2563eb; }
.badge--creative { background: #fdf4ff; color: #9333ea; }
.badge--paused { background: #fffbeb; color: #d97706; }
.badge--safety { background: #f0fdf4; color: #16a34a; }

/* ── Lead Score ── */
.lead-score-bar { margin: 12px 0; }
.score-label { font-size: 12px; color: var(--text-nav); font-weight: 500; }
.score-track {
  height: 6px;
  background: #f1f5f9;
  border-radius: 3px;
  overflow: hidden;
  margin-top: 6px;
  box-shadow: inset 1px 1px 3px rgba(166,175,195,0.3);
}
.score-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-orange), #22c55e);
  border-radius: 3px;
  transition: width 0.5s ease;
}
.lead-contact, .lead-location, .lead-industry {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 4px 0;
}
.lead-contact strong, .lead-location strong, .lead-industry strong {
  color: var(--text-heading);
}
.lead-notes {
  background: var(--bg-base);
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 12px;
  line-height: 1.5;
  box-shadow: var(--clay-shadow-inner);
}

/* ── Creatives ── */
.creative-headline {
  font-size: 15px;
  font-weight: 600;
  color: var(--accent-orange);
  margin: 8px 0;
}
.creative-body {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}
.creative-meta {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}
.cta-pill, .audience-pill {
  font-size: 11px;
  font-weight: 600;
  background: var(--bg-base);
  padding: 4px 10px;
  border-radius: 8px;
  color: var(--text-nav);
  box-shadow: 2px 2px 5px rgba(166,175,195,0.2), -2px -2px 5px rgba(255,255,255,0.8);
}
.image-prompt-box {
  background: var(--bg-base);
  padding: 12px;
  border-radius: 10px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 12px;
  line-height: 1.5;
  box-shadow: var(--clay-shadow-inner);
}

/* ── Safety Banner ── */
.safety-banner {
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border: 1px solid #bbf7d0;
  color: #166534;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  margin-top: 14px;
  box-shadow: 3px 3px 8px rgba(166,175,195,0.15), -3px -3px 8px rgba(255,255,255,0.8);
}

/* ── Modal ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15,23,42,0.4);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.modal-card {
  background: var(--bg-card);
  border-radius: 24px;
  padding: 32px;
  width: 480px;
  max-width: 90vw;
  box-shadow: 16px 16px 40px rgba(166,175,195,0.4), -16px -16px 40px rgba(255,255,255,0.95);
  border: 1px solid rgba(255,255,255,0.8);
  animation: slideUp 0.25s cubic-bezier(0.4,0,0.2,1);
}
@keyframes slideUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
.modal-card h2 {
  font-size: 20px;
  font-weight: 800;
  color: var(--text-heading);
  margin: 0 0 20px 0;
}
.form-group { margin-bottom: 14px; }
.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-nav);
  margin-bottom: 6px;
}
.form-group input, .form-group textarea {
  width: 100%;
  background: var(--bg-base);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 10px 14px;
  color: var(--text-heading);
  font-size: 13px;
  box-sizing: border-box;
  box-shadow: var(--clay-shadow-inner);
  outline: none;
  transition: border-color 0.2s;
}
.form-group input:focus, .form-group textarea:focus {
  border-color: var(--accent-orange);
}
.form-group textarea { min-height: 80px; resize: vertical; }
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
}
</style>
