<template>
  <div class="job-details-viewer" v-if="job">
    <div class="navigation-header">
      <button @click="goBackToJobsList" class="back-btn">← Back to Jobs</button>
      <div class="breadcrumb">
        <span>Jobs</span>
        <span class="separator">/</span>
        <span>{{ jobId }}</span>
      </div>
    </div>

    <h1>Job Details</h1>
    <div class="details-grid">
      <div class="detail-item">
        <span class="label">Job ID:</span>
        <span class="value">{{ job.id }}</span>
      </div>
      <div class="detail-item">
        <span class="label">Job Type:</span>
        <span class="value">{{ formatJobType(job.job_type) }}</span>
      </div>
      <div class="detail-item">
        <span class="label">Book:</span>
        <span class="value">{{ getBookName(job.book_id) }}</span>
      </div>
      <div class="detail-item">
        <span class="label">Status:</span>
        <span :class="['status-badge', job.state]">
          {{ getStatusIcon(job.state) }} {{ formatJobState(job.state) }}
        </span>
      </div>
      <div class="detail-item">
        <span class="label">Created At:</span>
        <span class="value">{{ formatDateTime(job.created_at) }}</span>
      </div>
      <div class="detail-item" v-if="job.started_at">
        <span class="label">Started At:</span>
        <span class="value">{{ formatDateTime(job.started_at) }}</span>
      </div>
      <div class="detail-item" v-if="job.completed_at">
        <span class="label">Completed At:</span>
        <span class="value">{{ formatDateTime(job.completed_at) }}</span>
      </div>
      <div class="detail-item">
        <span class="label">Duration:</span>
        <span class="value">{{ formatDuration(job) }}</span>
      </div>
      <div class="detail-item">
        <span class="label">LLM Cost:</span>
        <span class="value">{{ formatCurrency(job.total_cost) }}</span>
      </div>
      <div class="detail-item full-width" v-if="job.error_message">
        <span class="label">Error:</span>
        <pre class="error-message">{{ job.error_message }}</pre>
      </div>
      <div class="detail-item full-width" v-if="job.result_summary">
        <span class="label">Result Summary:</span>
        <pre class="result-summary">{{ job.result_summary }}</pre>
      </div>
    </div>

    <div class="actions">
      <router-link :to="`/jobs/${jobId}/logs`" class="action-btn logs-btn">View Logs</router-link>
      <!-- Add other actions like cancel/retry if applicable -->
    </div>

  </div>
  <div v-else-if="loading" class="loading-state">
    <div class="spinner"></div>
    Loading job details...
  </div>
  <div v-else class="error-state">
    <div class="error-icon">❌</div>
    <h3>Job Not Found</h3>
    <p>The job with ID {{ jobId }} could not be found, or an error occurred.</p>
    <button @click="goBackToJobsList" class="action-btn">Go to Jobs List</button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useBookStore } from '../stores/book';
import { useJobStore } from '../stores/jobStore';
import type { Job } from '../stores/types';
import { 
  formatJobState, 
  formatJobType, 
  getStatusIcon, 
  formatDateTime, 
  formatDuration
} from '../utils/jobFormatters';

const formatCurrency = (value: number | null | undefined): string => {
  if (value === null || typeof value === 'undefined' || Number.isNaN(value)) {
    return 'N/A';
  }
  // Ensure value is treated as a number for toLocaleString
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) {
    return 'N/A'; // Handle cases where conversion to number fails
  }
  return `$${numericValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`;
};

const route = useRoute();
const router = useRouter();
const bookStore = useBookStore();
const jobStore = useJobStore();

const jobId = route.params.jobId as string;
const job = computed(() => jobStore.currentJobDetails);
const loading = computed(() => jobStore.isJobDetailsLoading);

async function loadJobDetails() {
  try {
    // Get job details from job store
    await jobStore.fetchJobDetails(jobId);
    
    // Also make sure we have book info loaded
    if (job.value && job.value.book_id) {
      await bookStore.loadBooks();
    }
  } catch (error) {
    console.error('Failed to load job details:', error);
  }
}

function getBookName(bookId: string): string {
  const book = bookStore.books.find(b => b.book_id === bookId);
  return book ? book.props.name || 'Untitled Book' : 'Unknown Book';
}

function goBackToJobsList() {
  router.push('/jobs');
}

onMounted(() => {
  loadJobDetails();
  // Consider if auto-refresh is needed for job details, 
  // similar to logs, if job status can change while viewing.
  // For now, it loads once.
});

</script>

<style scoped>
.job-details-viewer {
  padding: 2rem;
  max-width: 900px;
  margin: 0 auto;
  background-color: #f9f9f9;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.navigation-header {
  display: flex;
  align-items: center;
  margin-bottom: 1.5rem;
  gap: 1rem;
}

.back-btn {
  background: none;
  border: 1px solid #ccc;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  color: #333;
}
.back-btn:hover {
  background-color: #eee;
}

.breadcrumb {
  font-size: 0.9rem;
  color: #666;
}

.breadcrumb .separator {
  margin: 0 0.5rem;
}

h1 {
  font-size: 1.8rem;
  margin-bottom: 1.5rem;
  color: #2c3e50;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.5rem;
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.detail-item {
  background-color: #fff;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #e1e8ed;
}

.detail-item.full-width {
  grid-column: 1 / -1; /* Span full width */
}

.detail-item .label {
  font-weight: 600;
  color: #555;
  display: block;
  margin-bottom: 0.3rem;
  font-size: 0.85rem;
}

.detail-item .value {
  color: #2c3e50;
  font-size: 0.95rem;
}

.status-badge {
  padding: 0.2em 0.6em;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 0.3em;
}

.status-badge.waiting { background-color: #e0e0e0; color: #333; }
.status-badge.running { background-color: #e3f2fd; color: #1565c0; }
.status-badge.complete { background-color: #e8f5e9; color: #2e7d32; }
.status-badge.error { background-color: #ffebee; color: #c62828; }
.status-badge.cancelled { background-color: #f5f5f5; color: #757575; }

pre {
  background-color: #f0f0f0;
  padding: 0.8rem;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.85rem;
  max-height: 200px;
  overflow-y: auto;
}

.actions {
  margin-top: 2rem;
  display: flex;
  gap: 1rem;
}

.action-btn {
  padding: 0.7rem 1.2rem;
  border: none;
  border-radius: 5px;
  text-decoration: none;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.logs-btn {
  background-color: #3498db;
  color: white;
}
.logs-btn:hover {
  background-color: #2980b9;
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
  color: #666;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}
</style>
