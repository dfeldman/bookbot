<template>
  <div class="dashboard-container">

    <div class="dashboard-content">
      <!-- Header -->
      <div class="dashboard-header">
        <h1>Your Books</h1>
        <p>Manage your AI-powered writing projects</p>
      </div>

      <!-- Loading State -->
      <div v-if="bookStore.isLoading" class="loading-section">
        <div class="loading-spinner"></div>
        <p>Loading your books...</p>
      </div>

      <!-- Current Job Progress -->
      <div v-if="bookStore.currentJob" class="job-progress-section">
        <div class="card job-progress-card">
          <h3>🚀 Creating Book Foundation</h3>
          <p>Building your book's structure, characters, and world...</p>
          
          <div class="progress-details">
            <span>{{ jobStatusText }}</span>
          </div>
        </div>
      </div>

      <!-- Books Grid -->
      <div v-if="!bookStore.isLoading" class="books-section">
        <!-- No Books State -->
        <div v-if="!bookStore.hasBooks" class="empty-state">
          <div class="empty-icon">📚</div>
          <h2>No books yet</h2>
          <p>Create your first book to get started with AI-powered writing!</p>
          <button class="btn btn-primary" @click="createNewBook">
            Create Your First Book
          </button>
        </div>

        <!-- Books Grid -->
        <div v-else class="books-grid">
          <div 
            v-for="book in bookStore.books" 
            :key="book.book_id"
            class="book-card card"
            @click="handleBookClick(book)"
          >
            <div class="book-header">
              <h3>{{ book.props.name || 'Untitled Book' }}</h3>
              <div class="book-status">
                <span v-if="book.is_locked" class="status-badge locked">🔒 Locked</span>
                <span v-else-if="book.job" class="status-badge processing">⚡ Processing</span>
                <span v-else class="status-badge ready">✅ Ready</span>
              </div>
            </div>
            
            <div class="book-description">
              {{ book.props.description || 'No description available' }}
            </div>
            
            <div class="book-stats">
              <div class="stat">
                <span class="stat-label">Chunks:</span>
                <span class="stat-value">{{ book.chunk_count || 0 }}</span>
              </div>
              <div class="stat">
                <span class="stat-label">Words:</span>
                <span class="stat-value">{{ formatNumber(book.word_count || 0) }}</span>
              </div>
              <div class="stat">
                <span class="stat-label">Style:</span>
                <span class="stat-value">{{ book.props.style || 'General' }}</span>
              </div>
            </div>
            
            <div class="book-footer">
              <span class="book-date">
                Created {{ formatDate(book.created_at) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Bar -->
      <div v-if="bookStore.hasBooks" class="action-bar">
        <button class="btn btn-primary" @click="createNewBook">
          Create Another Book
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useBookStore } from '../stores/book'
import StatusBar from '../components/StatusBar.vue'
import type { Book } from '../stores/book'

const router = useRouter()
const bookStore = useBookStore()

let jobPollingInterval: NodeJS.Timeout | null = null

const jobStatusText = computed(() => {
  if (!bookStore.currentJob) return ''
  
  switch (bookStore.currentJob.state) {
    case 'waiting':
      return 'Waiting to start...'
    case 'running':
      return 'Working on it...'
    case 'complete':
      return 'Complete!'
    case 'error':
      return 'Something went wrong'
    case 'cancelled':
      return 'Cancelled'
    default:
      return 'Processing...'
  }
})

onMounted(async () => {
  await bookStore.loadBooks()
  
  // Start polling if there's a current job
  if (bookStore.currentJob && bookStore.currentJob.state === 'running') {
    startJobPolling()
  }
})

onUnmounted(() => {
  stopJobPolling()
})

function startJobPolling() {
  if (jobPollingInterval) return
  
  jobPollingInterval = setInterval(async () => {
    if (bookStore.currentJob) {
      try {
        await bookStore.pollJobStatus(bookStore.currentJob.job_id)
        
        // Stop polling if job is complete
        if (bookStore.currentJob.state !== 'running' && bookStore.currentJob.state !== 'waiting') {
          stopJobPolling()
          // Reload books to get updated data
          await bookStore.loadBooks()
        }
      } catch (error) {
        console.error('Failed to poll job status:', error)
      }
    }
  }, 2000) // Poll every 2 seconds
}

function stopJobPolling() {
  if (jobPollingInterval) {
    clearInterval(jobPollingInterval)
    jobPollingInterval = null
  }
}

function createNewBook() {
  router.push('/wizard')
}

function handleBookClick(book: Book) {
  const job = bookStore.currentJob;
  // Check if the book is locked or if the currentJob in bookStore pertains to this book and is active
  if (book.is_locked || 
      (job && job.book_id === book.book_id && 
       (job.state === 'running' || job.state === 'waiting'))) { 
    // TODO: Implement a user-friendly notification (e.g., toast)
    console.warn(`Book '${book.props.name}' is currently being created or is locked. Please wait.`);
    return;
  }

  console.log('Opening book:', book);
  const path = `/books/${book.book_id}`;
  console.log('Navigating to:', path);
  
  // Ensure currentBook is set before navigating to BookViewer
  // This helps BookViewer load the correct book context immediately
  bookStore.currentBook = book;
  
  router.push(path).catch((error) => {
    console.error('Navigation failed:', error);
  });
}

function formatNumber(num: number): string {
  return num.toLocaleString()
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: #f8fafc;
  padding: 2rem 1rem;
}

.dashboard-content {
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 3rem;
}

.dashboard-header h1 {
  font-size: 2.5rem;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.dashboard-header p {
  font-size: 1.1rem;
  color: #64748b;
  margin: 0;
}

.loading-section {
  text-align: center;
  padding: 4rem 0;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.job-progress-section {
  margin-bottom: 3rem;
}

.job-progress-card {
  padding: 2rem;
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
}

.job-progress-card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.3rem;
}

.job-progress-card p {
  margin: 0 0 2rem 0;
  opacity: 0.9;
}

.progress-bar {
  background: rgba(255, 255, 255, 0.2);
  margin-bottom: 1rem;
}

.job-progress-card .progress-fill {
  background: white;
}

.progress-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  opacity: 0.9;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h2 {
  color: #1e293b;
  margin-bottom: 1rem;
}

.empty-state p {
  color: #64748b;
  margin-bottom: 2rem;
  font-size: 1.1rem;
}

.books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
}

.book-card {
  padding: 2rem;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid #e2e8f0;
}

.book-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px -6px rgb(0 0 0 / 0.1), 0 8px 16px -8px rgb(0 0 0 / 0.1);
  border-color: #cbd5e1;
}

.book-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.book-header h3 {
  margin: 0;
  color: #1e293b;
  font-size: 1.25rem;
  line-height: 1.3;
}

.status-badge {
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.status-badge.ready {
  background: #dcfce7;
  color: #166534;
}

.status-badge.processing {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.locked {
  background: #fecaca;
  color: #991b1b;
}

.book-description {
  color: #64748b;
  margin-bottom: 1.5rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  line-clamp: 3;
  overflow: hidden;
}

.book-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.8rem;
  color: #9ca3af;
  margin-bottom: 0.25rem;
}

.stat-value {
  display: block;
  font-weight: 600;
  color: #374151;
}

.book-footer {
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.book-date {
  font-size: 0.9rem;
  color: #9ca3af;
}

.action-bar {
  text-align: center;
  padding-top: 2rem;
  border-top: 1px solid #e2e8f0;
}

/* Responsive */
@media (max-width: 768px) {
  .books-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .book-card {
    padding: 1.5rem;
  }
  
  .book-header {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .book-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .progress-details {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>
