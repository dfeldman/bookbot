<template>
  <div class="job-logs-viewer">
    <div class="logs-header">
      <div class="navigation">
        <button @click="goBack" class="back-btn">
          ← Back to Jobs
        </button>
        <div class="breadcrumb">
          <span>Jobs</span>
          <span class="separator">/</span>
          <span>{{ jobId }}</span>
          <span class="separator">/</span>
          <span>Logs</span>
        </div>
      </div>
      
      <div v-if="job" class="job-info">
        <div class="job-header">
          <h1>Job Logs</h1>
          <div class="job-details">
            <span :class="['status-badge', job.state]">
              {{ getStatusIcon(job.state) }} {{ formatJobState(job.state) }}
            </span>
            <span class="job-type">{{ formatJobType(job.job_type) }}</span>
            <span class="job-book">{{ getBookName(job.book_id) }}</span>
          </div>
        </div>
        
        <div class="job-meta">
          <div class="meta-item">
            <span class="label">Created:</span>
            <span class="value">{{ formatDateTime(job.created_at) }}</span>
          </div>
          <div v-if="job.started_at" class="meta-item">
            <span class="label">Started:</span>
            <span class="value">{{ formatDateTime(job.started_at) }}</span>
          </div>
          <div v-if="job.completed_at" class="meta-item">
            <span class="label">Completed:</span>
            <span class="value">{{ formatDateTime(job.completed_at) }}</span>
          </div>
          <div class="meta-item">
            <span class="label">Duration:</span>
            <span class="value">{{ formatDuration(job) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="logs-controls">
      <div class="filter-section">
        <div class="filter-group">
          <label for="log-level">Log Level:</label>
          <select v-model="selectedLogLevel" id="log-level" @change="filterLogs">
            <option value="">All Levels</option>
            <option value="DEBUG">Debug</option>
            <option value="INFO">Info</option>
            <option value="WARN">Warning</option>
            <option value="ERROR">Error</option>
          </select>
        </div>
        
        <div class="search-group">
          <label for="log-search">Search:</label>
          <input 
            v-model="searchQuery" 
            id="log-search"
            type="text" 
            placeholder="Search logs..."
            @input="filterLogs"
          />
        </div>
      </div>
      
      <div class="action-section">
        <button @click="refreshLogs" class="refresh-btn" :disabled="loading">
          <span class="icon">🔄</span>
          Refresh
        </button>
        <button @click="downloadLogs" class="download-btn">
          <span class="icon">💾</span>
          Download
        </button>
        <button @click="toggleAutoScroll" class="auto-scroll-btn" :class="{ active: autoScroll }">
          <span class="icon">📜</span>
          Auto-scroll
        </button>
      </div>
    </div>

    <div v-if="loading && logs.length === 0" class="loading-state">
      <div class="spinner"></div>
      Loading logs...
    </div>

    <div v-else-if="!job" class="error-state">
      <div class="error-icon">❌</div>
      <h3>Job Not Found</h3>
      <p>The job with ID {{ jobId }} could not be found.</p>
    </div>

    <div v-else-if="filteredLogs.length === 0" class="empty-state">
      <div class="empty-icon">📄</div>
      <h3>No Logs Found</h3>
      <p>{{ logs.length === 0 ? 'This job hasn\'t generated any logs yet.' : 'No logs match your current filters.' }}</p>
    </div>

    <div v-else class="logs-container" ref="logsContainer">
      <div class="logs-stats">
        <div class="stat-item">
          <span class="stat-number">{{ filteredLogs.length }}</span>
          <span class="stat-label">{{ filteredLogs.length === 1 ? 'Log Entry' : 'Log Entries' }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ logStats.errors }}</span>
          <span class="stat-label">Errors</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ logStats.warnings }}</span>
          <span class="stat-label">Warnings</span>
        </div>
      </div>

      <div class="logs-list">
        <div 
          v-for="log in filteredLogs" 
          :key="log.id"
          :class="['log-entry', `level-${log.log_level.toLowerCase()}`]"
        >
          <div class="log-meta">
            <span class="log-timestamp">{{ formatLogTime(log.created_at) }}</span>
            <span :class="['log-level', log.log_level.toLowerCase()]">{{ log.log_level }}</span>
          </div>
          <div class="log-content">
            <pre>{{ log.log_entry }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBookStore, type Job } from '../stores/book'
import { apiService } from '../services/api'

interface JobLog {
  id: number
  job_id: string
  log_entry: string
  log_level: string
  created_at: string
}

const route = useRoute()
const router = useRouter()
const bookStore = useBookStore()

// State
const jobId = route.params.jobId as string
const job = ref<Job | null>(null)
const logs = ref<JobLog[]>([])
const loading = ref(false)
const selectedLogLevel = ref('')
const searchQuery = ref('')
const autoScroll = ref(true)
const logsContainer = ref<HTMLElement | null>(null)
const refreshInterval = ref<number | null>(null)

// Computed
const books = computed(() => bookStore.books)

const filteredLogs = computed(() => {
  let filtered = logs.value

  // Filter by log level
  if (selectedLogLevel.value) {
    filtered = filtered.filter(log => log.log_level === selectedLogLevel.value)
  }

  // Filter by search query
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim()
    filtered = filtered.filter(log => 
      log.log_entry.toLowerCase().includes(query) ||
      log.log_level.toLowerCase().includes(query)
    )
  }

  return filtered
})

const logStats = computed(() => {
  const stats = {
    errors: 0,
    warnings: 0
  }
  
  logs.value.forEach(log => {
    if (log.log_level === 'ERROR') stats.errors++
    if (log.log_level === 'WARN') stats.warnings++
  })
  
  return stats
})

// Methods
async function loadJob() {
  try {
    const response = await apiService.get(`/api/jobs/${jobId}`)
    job.value = response
  } catch (error) {
    console.error('Failed to load job:', error)
    job.value = null
  }
}

async function loadLogs() {
  loading.value = true
  
  try {
    const response = await apiService.get(`/api/jobs/${jobId}/logs`)
    logs.value = response.logs || []
    
    if (autoScroll.value) {
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('Failed to load logs:', error)
    logs.value = []
  } finally {
    loading.value = false
  }
}

async function refreshLogs() {
  await Promise.all([loadJob(), loadLogs()])
}

function filterLogs() {
  // Filtering is handled by computed property
}

function downloadLogs() {
  const content = filteredLogs.value
    .map(log => `[${log.created_at}] ${log.log_level}: ${log.log_entry}`)
    .join('\n')
  
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `job-${jobId}-logs.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function toggleAutoScroll() {
  autoScroll.value = !autoScroll.value
  if (autoScroll.value) {
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (logsContainer.value) {
    logsContainer.value.scrollTop = logsContainer.value.scrollHeight
  }
}

function goBack() {
  router.push('/jobs')
}

function getStatusIcon(state: string): string {
  const icons = {
    waiting: '⏳',
    running: '⚡',
    complete: '✅',
    error: '❌',
    cancelled: '🚫'
  }
  return icons[state as keyof typeof icons] || '❓'
}

function formatJobState(state: string): string {
  return state.charAt(0).toUpperCase() + state.slice(1)
}

function formatJobType(jobType: string): string {
  return jobType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function getBookName(bookId: string): string {
  const book = books.value.find(b => b.book_id === bookId)
  return book?.props?.name || 'Unknown Book'
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString()
}

function formatLogTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleTimeString()
}

function formatDuration(job: Job): string {
  if (!job.started_at) {
    return job.state === 'waiting' ? 'Not started' : '-'
  }
  
  const startTime = new Date(job.started_at).getTime()
  const endTime = job.completed_at ? new Date(job.completed_at).getTime() : Date.now()
  const durationMs = endTime - startTime
  
  const seconds = Math.floor(durationMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

function startAutoRefresh() {
  // Only auto-refresh if job is still active
  refreshInterval.value = window.setInterval(async () => {
    if (job.value && (job.value.state === 'running' || job.value.state === 'waiting')) {
      await loadLogs()
    }
  }, 3000) // Refresh every 3 seconds for active jobs
}

function stopAutoRefresh() {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

// Lifecycle
onMounted(async () => {
  await bookStore.loadBooks()
  await refreshLogs()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.job-logs-viewer {
  padding: 1rem 2rem 2rem;
  max-width: 1200px;
  margin: 0 auto;
  height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
}

.logs-header {
  margin-bottom: 1.5rem;
}

.navigation {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #f8f9fa;
  border: 1px solid #e1e8ed;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  color: #555;
  font-size: 0.875rem;
}

.back-btn:hover {
  background: #e9ecef;
}

.breadcrumb {
  font-size: 0.875rem;
  color: #666;
}

.separator {
  margin: 0 0.5rem;
  color: #ccc;
}

.job-info {
  background: white;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  padding: 1.5rem;
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.job-header h1 {
  margin: 0;
  color: #2c3e50;
}

.job-details {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-badge.waiting {
  background: #e8f4fd;
  color: #3498db;
}

.status-badge.running {
  background: #fef9e7;
  color: #f39c12;
}

.status-badge.complete {
  background: #e8f5e8;
  color: #27ae60;
}

.status-badge.error {
  background: #fdf2f2;
  color: #e74c3c;
}

.status-badge.cancelled {
  background: #f5f5f5;
  color: #666;
}

.job-type {
  padding: 0.25rem 0.75rem;
  background: #f8f9fa;
  border-radius: 12px;
  font-size: 0.875rem;
  color: #666;
}

.job-book {
  padding: 0.25rem 0.75rem;
  background: #e8f4fd;
  border-radius: 12px;
  font-size: 0.875rem;
  color: #3498db;
}

.job-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.meta-item {
  display: flex;
  gap: 0.5rem;
}

.meta-item .label {
  font-weight: 500;
  color: #666;
  min-width: 80px;
}

.meta-item .value {
  color: #2c3e50;
}

.logs-controls {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 1rem;
  gap: 2rem;
  flex-wrap: wrap;
}

.filter-section {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
}

.filter-group,
.search-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-group label,
.search-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #555;
}

.filter-group select,
.search-group input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  min-width: 120px;
}

.action-section {
  display: flex;
  gap: 0.5rem;
}

.refresh-btn,
.download-btn,
.auto-scroll-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  background: white;
}

.refresh-btn:hover,
.download-btn:hover,
.auto-scroll-btn:hover {
  background: #f8f9fa;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auto-scroll-btn.active {
  background: #3498db;
  color: white;
  border-color: #3498db;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: #666;
  text-align: center;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon,
.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.logs-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.logs-stats {
  display: flex;
  gap: 2rem;
  margin-bottom: 1rem;
  padding: 1rem;
  background: white;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.stat-number {
  font-size: 1.5rem;
  font-weight: bold;
  color: #2c3e50;
}

.stat-label {
  font-size: 0.75rem;
  color: #666;
}

.logs-list {
  flex: 1;
  background: #1e1e1e;
  border-radius: 8px;
  overflow-y: auto;
  padding: 1rem;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.log-entry {
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  border-radius: 4px;
  border-left: 3px solid transparent;
}

.log-entry.level-debug {
  border-left-color: #95a5a6;
  background: rgba(149, 165, 166, 0.1);
}

.log-entry.level-info {
  border-left-color: #3498db;
  background: rgba(52, 152, 219, 0.1);
}

.log-entry.level-warn {
  border-left-color: #f39c12;
  background: rgba(243, 156, 18, 0.1);
}

.log-entry.level-error {
  border-left-color: #e74c3c;
  background: rgba(231, 76, 60, 0.1);
}

.log-meta {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.25rem;
  font-size: 0.75rem;
}

.log-timestamp {
  color: #95a5a6;
}

.log-level {
  font-weight: bold;
  text-transform: uppercase;
}

.log-level.debug { color: #95a5a6; }
.log-level.info { color: #3498db; }
.log-level.warn { color: #f39c12; }
.log-level.error { color: #e74c3c; }

.log-content {
  color: #ecf0f1;
  line-height: 1.4;
}

.log-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
}

@media (max-width: 768px) {
  .job-logs-viewer {
    padding: 1rem;
  }
  
  .logs-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
  
  .filter-section {
    flex-wrap: wrap;
  }
  
  .job-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .job-details {
    justify-content: flex-start;
  }
  
  .job-meta {
    grid-template-columns: 1fr;
  }
  
  .logs-stats {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
