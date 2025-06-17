<template>
  <div class="status-bar">
    <div class="status-content">
      <!-- Left: App Title -->
      <div class="app-section">
        <router-link to="/dashboard" class="app-title">
          📚 BookBot
        </router-link>
      </div>

      <!-- Center: Current Jobs -->
      <div class="jobs-section">
        <router-link to="/jobs" class="jobs-link">
          <div v-if="activeJobs.length > 0" class="active-jobs">
            <div class="job-indicator">
              <div class="spinner-small"></div>
              <div class="job-details">
                <div v-if="activeJobs.length === 1" class="single-job">
                  <span class="job-name">{{ formatJobType(activeJobs[0].job_type) }}</span>
                  <span class="job-time">{{ getElapsedTime(activeJobs[0]) }}</span>
                </div>
                <div v-else class="multiple-jobs">
                  {{ activeJobs.length }} running jobs
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-jobs">
            📋 Jobs
          </div>
        </router-link>
      </div>

      <!-- Right: Account & Settings -->
      <div class="account-section">
        <div v-if="hasApiToken" class="balance-display">
          Balance: ${{ accountBalance }}
        </div>
        <div v-else class="no-token">
          No API token
        </div>
        <button @click="showSettings" class="settings-button">
          ⚙️
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'
import { useBookStore } from '../stores/book'

const router = useRouter()
const appStore = useAppStore()
const bookStore = useBookStore()

// Reactive timestamp for elapsed time calculation
const now = ref(Date.now())
let timeUpdateInterval: ReturnType<typeof setInterval> | null = null

const hasApiToken = computed(() => appStore.hasApiToken)
const accountBalance = computed(() => {
  // This would come from periodic API calls or token validation
  return '25.50' // Placeholder
})

const activeJobs = computed(() => {
  // Only show jobs for the current book, not all jobs globally
  const currentBookId = bookStore.currentBook?.book_id
  
  if (!currentBookId) {
    return []
  }
  
  const filtered = bookStore.jobs.filter(job => 
    job.book_id === currentBookId &&
    (job.state === 'waiting' || job.state === 'running')
  )
  
  return filtered
})

function formatJobType(jobType: string): string {
  // Convert job_type to readable format
  return jobType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function getElapsedTime(job: any): string {
  const startTime = job.started_at || job.created_at
  if (!startTime) return '0s'
  
  const start = new Date(startTime).getTime()
  const elapsed = Math.floor((now.value - start) / 1000)
  
  if (elapsed < 60) {
    return `${elapsed}s`
  } else if (elapsed < 3600) {
    const minutes = Math.floor(elapsed / 60)
    const seconds = elapsed % 60
    return `${minutes}m ${seconds}s`
  } else {
    const hours = Math.floor(elapsed / 3600)
    const minutes = Math.floor((elapsed % 3600) / 60)
    return `${hours}h ${minutes}m`
  }
}

function showSettings() {
  router.push('/settings')
}

// Update elapsed time every second when there are active jobs
onMounted(() => {
  timeUpdateInterval = setInterval(() => {
    now.value = Date.now()
  }, 1000)
})

onUnmounted(() => {
  if (timeUpdateInterval) {
    clearInterval(timeUpdateInterval)
  }
})
</script>

<style scoped>
.status-bar {
  background: #1e293b;
  color: white;
  padding: 0.75rem 0;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.status-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-section {
  flex: 1;
}

.app-title {
  color: white;
  text-decoration: none;
  font-weight: 600;
  font-size: 1.125rem;
  transition: color 0.2s;
}

.app-title:hover {
  color: #e2e8f0;
}

.jobs-section {
  flex: 1;
  text-align: center;
}

.jobs-link {
  color: inherit;
  text-decoration: none;
  transition: opacity 0.2s;
}

.jobs-link:hover {
  opacity: 0.8;
}

.active-jobs {
  display: flex;
  align-items: center;
  justify-content: center;
}

.job-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(59, 130, 246, 0.1);
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.875rem;
  color: #93c5fd;
}

.job-details {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.125rem;
}

.single-job {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.2;
}

.job-name {
  font-weight: 500;
  color: #93c5fd;
}

.job-time {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 400;
}

.multiple-jobs {
  font-weight: 500;
}

.spinner-small {
  width: 12px;
  height: 12px;
  border: 2px solid #3b82f6;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.no-jobs {
  font-size: 0.875rem;
  color: #94a3b8;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.05);
  transition: background-color 0.2s;
}

.no-jobs:hover {
  background: rgba(255, 255, 255, 0.1);
}

.account-section {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 1rem;
}

.balance-display {
  font-size: 0.875rem;
  color: #e2e8f0;
}

.no-token {
  font-size: 0.875rem;
  color: #f87171;
}

.settings-button {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  padding: 0.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 1rem;
}

.settings-button:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
