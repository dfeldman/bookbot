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
          <select v-model="selectedBookId" id="book-filter" @change="loadJobs">
            <option value="">All Books</option>
            <option v-for="book in books" :key="book.book_id" :value="book.book_id">
              {{ book.props.name || 'Untitled Book' }}
            </option>
          </select>
        </div>
        
        <div class="filter-group">
          <label for="state-filter">Status:</label>
          <select v-model="selectedState" id="state-filter" @change="loadJobs">
            <option value="">All States</option>
            <option value="waiting">Waiting</option>
            <option value="running">Running</option>
            <option value="complete">Complete</option>
            <option value="error">Error</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        
        <button @click="loadJobs" class="refresh-btn" :disabled="loading">
          <span class="icon">🔄</span>
          Refresh
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      Loading jobs...
    </div>

    <div v-else-if="jobs.length === 0" class="empty-state">
      <div class="empty-icon">📋</div>
      <h3>No Jobs Found</h3>
      <p v-if="selectedState || selectedBookId">No jobs match your current filters.</p>
      <p v-else>There are no jobs in the system.</p>
    </div>

    <div v-else class="jobs-container">
      <div class="jobs-stats">
        <div class="stat-card">
          <div class="stat-number">{{ jobStats.total }}</div>
          <div class="stat-label">Total Jobs</div>
        </div>
        <div class="stat-card running">
          <div class="stat-number">{{ jobStats.running }}</div>
          <div class="stat-label">Running</div>
        </div>
        <div class="stat-card waiting">
          <div class="stat-number">{{ jobStats.waiting }}</div>
          <div class="stat-label">Waiting</div>
        </div>
        <div class="stat-card complete">
          <div class="stat-number">{{ jobStats.complete }}</div>
          <div class="stat-label">Complete</div>
        </div>
        <div class="stat-card error">
          <div class="stat-number">{{ jobStats.error }}</div>
          <div class="stat-label">Failed</div>
        </div>
        <div class="stat-card cost">
          <div class="stat-number">{{ formatCurrency(grandTotalCost) }}</div>
          <div class="stat-label">Total LLM Cost</div>
        </div>
      </div>

      <div class="jobs-table">
        <div class="table-header">
          <div class="col-status">Status</div>
          <div class="col-type">Type</div>
          <div class="col-book">Book</div>
          <div class="col-created">Created</div>
          <div class="col-duration">Duration</div>
          <div class="col-cost">Cost</div>
          <div class="col-actions">Actions</div>
        </div>
        
        <div 
          v-for="job in sortedJobs" 
          :key="job.job_id"
          :class="['job-row', `status-${job.state}`]"
          @click="viewJobDetails(job.job_id)"
        >
          <div class="col-status">
            <span :class="['status-badge', job.state]">
              <span class="status-icon">{{ getStatusIcon(job.state) }}</span>
              {{ formatJobState(job.state) }}
            </span>
          </div>
          
          <div class="col-type">
            <div class="job-type">{{ formatJobType(job.job_type) }}</div>
            <div v-if="job.props && Object.keys(job.props).length > 0" class="job-props">
              {{ formatJobProps(job.props) }}
            </div>
          </div>
          
          <div class="col-book">
            <div class="book-info">
              <div class="book-name">{{ getBookName(job.book_id) }}</div>
              <div class="book-id">{{ job.book_id.substring(0, 8) }}...</div>
            </div>
          </div>
          
          <div class="col-created">
            <div class="created-time">{{ formatDateTime(job.created_at) }}</div>
            <div class="created-relative">{{ getRelativeTime(job.created_at) }}</div>
          </div>
          
          <div class="col-duration">
            <div class="duration">{{ formatDuration(job) }}</div>
            <div v-if="job.state === 'running'" class="running-indicator">
              <span class="pulse-dot"></span>
              Running...
            </div>
          </div>
          
          <div class="col-cost">
            {{ formatCurrency(job.total_cost) }}
          </div>
          
          <div class="col-actions" @click.stop>
            <button 
              @click="viewJobLogs(job.job_id)"
              class="action-btn logs-btn"
              title="View Logs"
            >
              📄
            </button>
            <button 
              v-if="job.state === 'waiting' || job.state === 'running'"
              @click="cancelJob(job.job_id)"
              class="action-btn cancel-btn"
              title="Cancel Job"
            >
              ❌
            </button>
            <button 
              @click="viewJobDetails(job.job_id)"
              class="action-btn details-btn"
              title="View Details"
            >
              👁️
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useBookStore, type Job } from '../stores/book'
import { apiService } from '../services/api'

const router = useRouter()
const bookStore = useBookStore()

// State
const jobs = ref<Job[]>([])
const loading = ref(false)
const grandTotalCost = ref<number | null>(null)
const selectedBookId = ref('')
const selectedState = ref('')
const autoRefreshInterval = ref<number | null>(null)

// Computed
const books = computed(() => bookStore.books)

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
    if (job.state in stats) {
      stats[job.state as keyof typeof stats]++
    }
  })
  
  return stats
})

const sortedJobs = computed(() => {
  return [...jobs.value].sort((a, b) => {
    // Sort by state priority (running > waiting > error > complete > cancelled)
    // const statePriority = { running: 5, waiting: 4, error: 3, complete: 2, cancelled: 1 }
    // const aPriority = statePriority[a.state as keyof typeof statePriority] || 0
    // const bPriority = statePriority[b.state as keyof typeof statePriority] || 0
    
    // if (aPriority !== bPriority) {
    //   return bPriority - aPriority
    // }
    
    // Then by created_at (newest first)
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
})

// Methods
async function loadJobs() {
  loading.value = true
  try {
    const params: any = {}
    if (selectedState.value) {
      params.state = selectedState.value
    }

    let response;
    if (!selectedBookId.value) {
      // Fetch all jobs if no specific book is selected
      response = await apiService.getAllJobs(params)
    } else {
      // Fetch jobs for the selected book
      response = await apiService.getJobs(selectedBookId.value, params)
    }

    jobs.value = response.jobs.map((job: any) => ({
      ...job,
      created_at: new Date(job.created_at),
      updated_at: new Date(job.updated_at)
    }))
  } catch (error) {
    console.error('Failed to load jobs:', error)
    jobs.value = []
  } finally {
    loading.value = false
  }
}

async function cancelJob(jobId: string) {
  if (!confirm('Are you sure you want to cancel this job?')) {
    return
  }
  
  try {
    await apiService.delete(`/api/jobs/${jobId}`)
    await loadJobs() // Refresh the list
  } catch (error) {
    console.error('Failed to cancel job:', error)
    alert('Failed to cancel job. Please try again.')
  }
}

function viewJobDetails(jobId: string) {
  router.push(`/jobs/${jobId}`)
}

function viewJobLogs(jobId: string) {
  router.push(`/jobs/${jobId}/logs`)
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

function formatJobProps(props: any): string {
  if (!props || typeof props !== 'object') return ''
  
  const entries = Object.entries(props)
  if (entries.length === 0) return ''
  
  // Show first few key properties
  const displayEntries = entries.slice(0, 2)
  let result = displayEntries.map(([key, value]) => `${key}: ${value}`).join(', ')
  
  if (entries.length > 2) {
    result += ` +${entries.length - 2} more`
  }
  
  return result
}

function getBookName(bookId: string): string {
  const book = books.value.find(b => b.book_id === bookId)
  return book?.props?.name || 'Unknown Book'
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString()
}

function getRelativeTime(dateString: string): string {
  const date = new Date(dateString)
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

function formatCurrency(value: number | null | undefined): string {
  if (value === null || typeof value === 'undefined' || Number.isNaN(value)) {
    return 'N/A';
  }
  return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`;
}

async function loadGrandTotalCost() {
  try {
    const data = await apiService.getTotalCostAllJobs();
    grandTotalCost.value = data.total_cost;
  } catch (error) {
    console.error('Failed to load grand total cost:', error);
    grandTotalCost.value = null;
  }
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

// Lifecycle
onMounted(async () => {
  await bookStore.loadBooks()
  // If no book is selected and there are books available, select the first one.
  if (!selectedBookId.value && books.value.length > 0) {
    selectedBookId.value = books.value[0].book_id
  }
  await loadJobs() // loadJobs now calls loadGrandTotalCost internally
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.jobs-viewer {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.jobs-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  gap: 2rem;
}

.title-section h1 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
  font-size: 2rem;
}

.subtitle {
  margin: 0;
  color: #666;
  font-size: 1rem;
}

.filter-controls {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #555;
}

.filter-group select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  min-width: 150px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.refresh-btn:hover {
  background: #2980b9;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 4rem;
  color: #666;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 4rem;
  color: #666;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.jobs-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
}

.stat-card.running {
  border-color: #f39c12;
  background: #fef9e7;
}

.stat-card.waiting {
  border-color: #3498db;
  background: #e8f4fd;
}

.stat-card.complete {
  border-color: #27ae60;
  background: #e8f5e8;
}

.stat-card.error {
  border-color: #e74c3c;
  background: #fdf2f2;
}

.stat-card.cost {
  border-color: #7f8c8d; /* A neutral grey */
  background: #ecf0f1; /* Light grey background */
}

.stat-number {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #666;
}

.jobs-table {
  background: white;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 120px 200px 150px 150px 100px 100px 120px; /* Status, Type, Book, Created, Duration, Cost, Actions */
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e1e8ed;
  font-weight: 600;
  font-size: 0.875rem;
  color: #555;
}

.job-row {
  display: grid;
  grid-template-columns: 120px 200px 150px 150px 100px 100px 120px; /* Status, Type, Book, Created, Duration, Cost, Actions */
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.2s;
}

.job-row:hover {
  background: #f8f9fa;
}

.job-row:last-child {
  border-bottom: none;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
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
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.job-props {
  font-size: 0.75rem;
  color: #666;
}

.book-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.book-name {
  font-weight: 500;
}

.book-id {
  font-size: 0.75rem;
  color: #666;
  font-family: monospace;
}

.created-time {
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.created-relative {
  font-size: 0.75rem;
  color: #666;
}

.duration {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.running-indicator {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #f39c12;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  background: #f39c12;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.col-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  transition: transform 0.2s;
}

.action-btn:hover {
  transform: scale(1.1);
}

.logs-btn {
  background: #3498db;
  color: white;
}

.cancel-btn {
  background: #e74c3c;
  color: white;
}

.details-btn {
  background: #95a5a6;
  color: white;
}

@media (max-width: 768px) {
  .jobs-viewer {
    padding: 1rem;
  }
  
  .jobs-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .filter-controls {
    width: 100%;
  }
  
  .table-header,
  .job-row {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  
  .table-header {
    display: none;
  }
  
  .job-row {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .jobs-stats {
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  }
}
</style>
