<template>
  <div class="jobs-viewer">
    <div class="jobs-header">
      <div class="title-section">
        <h1>Jobs</h1>
        <p class="subtitle">Monitor background tasks and processing jobs</p>
      </div>
      
      <div class="filter-controls">
        <div class="filter-group">
          <label for="book-filter">Book:</label>
          <select id="book-filter" v-model="selectedBookId">
            <option value="">All Books</option>
            <option v-for="book in books" :key="book.book_id" :value="book.book_id">
              {{ book.props.name || 'Untitled Book' }}
            </option>
          </select>
        </div>
        
        <div class="filter-group">
          <label for="state-filter">Status:</label>
          <select id="state-filter" v-model="selectedState">
            <option value="">All States</option>
            <option value="waiting">Waiting</option>
            <option value="running">Running</option>
            <option value="complete">Complete</option>
            <option value="error">Error</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        
        <button @click="loadJobs" :disabled="loading" class="refresh-btn">
          <span v-if="loading">⏳</span>
          <span v-else>🔄</span> Refresh
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && jobs.length === 0" class="loading-state">
      <div class="spinner"></div>
      <p>Loading jobs...</p>
    </div>
    
    <!-- Empty State -->
    <div v-else-if="jobs.length === 0" class="empty-state">
      <div class="empty-icon">📋</div>
      <h3>No Jobs Found</h3>
      <p>No jobs match your current filters or there are no jobs in the system yet.</p>
    </div>
    
    <template v-else>
      <!-- Stats Cards -->
      <div class="jobs-stats">
        <div class="stat-card">
          <div class="stat-number">{{ jobStats.total }}</div>
          <div class="stat-label">Total Jobs</div>
        </div>
        <div class="stat-card waiting">
          <div class="stat-number">{{ jobStats.waiting }}</div>
          <div class="stat-label">Waiting</div>
        </div>
        <div class="stat-card running">
          <div class="stat-number">{{ jobStats.running }}</div>
          <div class="stat-label">Running</div>
        </div>
        <div class="stat-card complete">
          <div class="stat-number">{{ jobStats.complete }}</div>
          <div class="stat-label">Complete</div>
        </div>
        <div class="stat-card error">
          <div class="stat-number">{{ jobStats.error }}</div>
          <div class="stat-label">Error</div>
        </div>
        <div class="stat-card cost">
          <div class="stat-number">{{ formatCurrency(grandTotalCost) }}</div>
          <div class="stat-label">Total Cost</div>
        </div>
      </div>
      
      <!-- Jobs Table -->
      <div class="jobs-table">
        <div class="table-header">
          <div>Status</div>
          <div>Type</div>
          <div>Book</div>
          <div>Created</div>
          <div>Duration</div>
          <div>Cost</div>
          <div>Actions</div>
        </div>
        
        <div v-for="job in sortedJobs" :key="job.job_id" class="job-row">
          <!-- Status -->
          <div>
            <span :class="['status-badge', job.state]">
              {{ getStatusIcon(job.state) }} {{ formatJobState(job.state) }}
            </span>
          </div>
          
          <!-- Type -->
          <div>
            <div class="job-type">{{ formatJobType(job.job_type) }}</div>
            <div class="job-props" v-if="job.props">{{ formatJobProps(job.props) }}</div>
          </div>
          
          <!-- Book -->
          <div class="book-info">
            <div class="book-name">{{ getBookName(job.book_id) }}</div>
            <div class="book-id">{{ job.book_id }}</div>
          </div>
          
          <!-- Created -->
          <div>
            <div class="created-time">{{ formatDateTime(job.created_at) }}</div>
            <div class="created-relative">{{ getRelativeTime(job.created_at) }}</div>
          </div>
          
          <!-- Duration -->
          <div>
            <div class="duration">{{ formatDuration(job) }}</div>
            <div v-if="job.state === 'running'" class="running-indicator">
              <span class="pulse-dot"></span> In progress
            </div>
          </div>
          
          <!-- Cost -->
          <div>
            {{ formatCurrency(job.total_cost) }}
          </div>
          
          <!-- Actions -->
          <div class="col-actions">
            <button @click="viewJobDetails(job.job_id)" class="action-btn details-btn" title="View Details">
              🔍
            </button>
            <button @click="viewJobLogs(job.job_id)" class="action-btn logs-btn" title="View Logs">
              📝
            </button>
            <button 
              v-if="job.state === 'waiting' || job.state === 'running'"
              @click="cancelJob(job.job_id)"
              class="action-btn cancel-btn"
              title="Cancel Job">
              ❌
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
// Imports
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useBookStore } from '../stores/book'
import { useJobStore } from '../stores/jobStore'
import type { Job } from '../stores/types'
import { apiService } from '../services/api'
import { 
  getStatusIcon, 
  formatJobState, 
  formatJobType, 
  formatDateTime, 
  formatDuration 
} from '../utils/jobFormatters'

// Setup stores and router
const router = useRouter()
const bookStore = useBookStore()
const jobStore = useJobStore()

// Local state
const selectedBookId = ref('')
const selectedState = ref('')
const grandTotalCost = ref<number | null>(null)
const autoRefreshInterval = ref<number | null>(null)

// Basic computed properties
const jobs = computed(() => jobStore.allJobs)
const loading = computed(() => jobStore.isJobsViewerLoading)
const books = computed(() => bookStore.books)

// Job statistics - fixes job state counting mismatch
const jobStats = computed(() => {
  const stats = {
    total: jobs.value.length,
    waiting: 0,
    running: 0,
    complete: 0,
    error: 0,
    cancelled: 0
  }

  jobs.value.forEach(job => {
    let state = job.state
    if (state === 'completed') state = 'complete'
    if (state === 'failed') state = 'error'
    if (state === 'pending') state = 'waiting'

    if (stats.hasOwnProperty(state)) {
      stats[state as keyof typeof stats]++
    }
  })

  return stats
})

// Sort jobs with newest first
const sortedJobs = computed(() => {
  return [...jobs.value].sort((a, b) => {
    const dateA = new Date(a.created_at).getTime()
    const dateB = new Date(b.created_at).getTime()
    return dateB - dateA
  })
})

// Methods
async function loadJobs() {
  await jobStore.fetchAllJobs(selectedBookId.value, selectedState.value)
  await loadGrandTotalCost()
}

async function loadGrandTotalCost() {
  try {
    const data = await apiService.getTotalCostAllJobs()
    grandTotalCost.value = data.total_cost
  } catch (error) {
    console.error('Failed to load grand total cost:', error)
    grandTotalCost.value = null
  }
}

function viewJobDetails(jobId: string) {
  router.push(`/jobs/${jobId}`)
}

function viewJobLogs(jobId: string) {
  router.push(`/jobs/${jobId}/logs`)
}

async function cancelJob(jobId: string) {
  try {
    await apiService.cancelJob(jobId)
    // Refresh jobs list after cancellation
    loadJobs()
  } catch (error) {
    console.error('Failed to cancel job:', error)
  }
}

function getBookName(bookId: string) {
  const book = books.value.find(b => b.book_id === bookId)
  return book ? book.props.name || 'Untitled Book' : 'Unknown Book'
}

function formatJobProps(props: Record<string, any> | undefined) {
  if (!props) return ''
  
  // Filter out large or complex props that would make the display messy
  const filteredProps = Object.entries(props)
    .filter(([key, value]) => 
      typeof value !== 'object' && 
      key !== 'api_key' && 
      key !== 'token' && 
      !key.includes('password')
    )
  
  return filteredProps
    .map(([key, value]) => `${key}: ${value}`)
    .join(', ')
}

function getRelativeTime(dateStr: string) {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffMinutes < 1) return 'Just now'
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}

function formatCurrency(value: number | null | undefined): string {
  if (value === null || typeof value === 'undefined' || Number.isNaN(value)) {
    return 'N/A'
  }
  return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`
}

function startAutoRefresh() {
  // Refresh every 5 seconds if there are active jobs
  autoRefreshInterval.value = window.setInterval(() => {
    const hasActiveJobs = jobs.value.some(job => job.state === 'running' || job.state === 'waiting')
    if (hasActiveJobs) {
      loadJobs()
    }
  }, 5000)
}

function stopAutoRefresh() {
  if (autoRefreshInterval.value) {
    clearInterval(autoRefreshInterval.value)
    autoRefreshInterval.value = null
  }
}

// Watch for filter changes
watch([selectedBookId, selectedState], () => {
  loadJobs()
})

// Lifecycle hooks
onMounted(async () => {
  await bookStore.loadBooks()
  // If no book is selected and there are books available, select the first one
  if (!selectedBookId.value && books.value.length > 0) {
    selectedBookId.value = books.value[0].book_id
  }
  await loadJobs()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.jobs-viewer {
  padding: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.jobs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.title-section h1 {
  font-size: 1.8rem;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  font-size: 1rem;
}

.filter-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

select {
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #ddd;
  min-width: 150px;
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.refresh-btn:hover {
  background-color: #e0e0e0;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 0;
  text-align: center;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #ccc;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Stats Cards */
.jobs-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.stat-card.waiting { background-color: #fff8e1; }
.stat-card.running { background-color: #e3f2fd; }
.stat-card.complete { background-color: #e8f5e9; }
.stat-card.error { background-color: #ffebee; }
.stat-card.cost { background-color: #f3e5f5; }

.stat-number {
  font-size: 1.8rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

/* Jobs Table */
.jobs-table {
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: white;
}

.table-header {
  display: grid;
  grid-template-columns: 1fr 1.5fr 1fr 1fr 1fr 0.7fr 0.8fr;
  background-color: #f5f5f5;
  padding: 0.75rem 1rem;
  font-weight: bold;
  border-bottom: 1px solid #eee;
}

.job-row {
  display: grid;
  grid-template-columns: 1fr 1.5fr 1fr 1fr 1fr 0.7fr 0.8fr;
  padding: 1rem;
  border-bottom: 1px solid #eee;
  align-items: center;
}

.job-row:hover {
  background-color: #f9f9f9;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  gap: 0.25rem;
}

.status-badge.waiting {
  background-color: #fff8e1;
  color: #ffa000;
}

.status-badge.running {
  background-color: #e3f2fd;
  color: #1976d2;
}

.status-badge.complete {
  background-color: #e8f5e9;
  color: #388e3c;
}

.status-badge.error {
  background-color: #ffebee;
  color: #d32f2f;
}

.status-badge.cancelled {
  background-color: #f5f5f5;
  color: #757575;
}

.job-type {
  font-weight: bold;
  margin-bottom: 0.25rem;
}

.job-props {
  font-size: 0.8rem;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

.book-name {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.book-id {
  font-size: 0.75rem;
  color: #999;
  font-family: monospace;
}

.created-time {
  margin-bottom: 0.25rem;
}

.created-relative {
  font-size: 0.8rem;
  color: #666;
}

.duration {
  font-weight: 500;
}

.running-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #1976d2;
  margin-top: 0.25rem;
}

.pulse-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  background-color: #1976d2;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(0.8);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.2);
    opacity: 1;
  }
  100% {
    transform: scale(0.8);
    opacity: 0.8;
  }
}

.col-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 4px;
  border: none;
  background-color: #f5f5f5;
  cursor: pointer;
  transition: background-color 0.2s;
}

.action-btn:hover {
  background-color: #e0e0e0;
}

.details-btn:hover {
  background-color: #e3f2fd;
}

.logs-btn:hover {
  background-color: #e8f5e9;
}

.cancel-btn:hover {
  background-color: #ffebee;
}

@media (max-width: 1024px) {
  .job-row,
  .table-header {
    grid-template-columns: 1fr 1.5fr 1fr 1fr 1fr 0.7fr 0.8fr;
    font-size: 0.9rem;
  }
}

@media (max-width: 768px) {
  .jobs-table {
    display: block;
    overflow-x: auto;
  }
  
  .job-row,
  .table-header {
    width: 900px;
  }
  
  .jobs-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .filter-controls {
    width: 100%;
    justify-content: space-between;
  }
}
</style>

<style scoped>
.jobs-viewer {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

/* Add more styling as needed */
</style>
