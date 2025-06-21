<template>
  <BookLockOverlay 
    v-if="isBookEffectivelyLocked"
    :title="overlayTitle"
    :message="overlayMessage"
    :jobStatus="overlayJobStatus"
  />
  <div class="book-viewer" :class="{ 'content-blurred': isBookEffectivelyLocked }">
    <!-- Book Header -->
    <div class="book-header">
      <div class="book-title-section">
        <button @click="$router.push('/dashboard')" class="back-button">
          ← Back to Books
        </button>
        <h1 class="book-title">{{ book?.props?.name || book?.props?.title || 'Untitled Book' }}</h1>
        <div class="book-meta">
          <span class="book-stats">{{ book?.chunk_count || 0 }} chunks</span>
          <span class="book-stats">{{ book?.word_count || 0 }} words</span>
        </div>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="tab-navigation">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="['tab-button', { active: activeTab === tab.id }]"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Index Tab -->
      <div v-if="activeTab === 'index'" class="index-tab">
        <BookIndex 
          :book="book" 
          :chunks="chunks"
          :loading="isLoading"
          @edit-chunk="editChunk"
          @reorder-chunks="reorderChunks"
        />
      </div>

      <!-- Read Tab -->
      <div v-else-if="activeTab === 'read'" class="read-tab">
        <BookReader 
          :chunks="chunks"
          :loading="isLoading"
        />
      </div>

      <!-- Bots Tab -->
      <div v-else-if="activeTab === 'bots'" class="bots-tab">
        <BotManager />
      </div>

      <!-- Export Tab -->
      <div v-else-if="activeTab === 'export'" class="export-tab">
        <BookExport 
          :chunks="chunks"
          :book="book"
        />
      </div>

      <!-- Settings Tab -->
      <div v-else-if="activeTab === 'settings'" class="settings-tab">
        <BookSettings 
          :book="book"
          :chunks="chunks"
          @book-updated="handleBookUpdated"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBookStore } from '../stores/book'
import BookIndex from '../components/BookIndex.vue'
import BookReader from '../components/BookReader.vue'
import BotManager from '../components/BotManager.vue'
import BookExport from '../components/BookExport.vue'
import BookSettings from '../components/BookSettings.vue'
import BookLockOverlay from '../components/BookLockOverlay.vue'
import type { Job } from '../stores/book'; // Assuming Job type from book.ts

const route = useRoute()
const router = useRouter()
const bookStore = useBookStore()

const activeTab = ref('index')
const isLoading = ref(false)

const tabs = [
  { id: 'index', label: 'Index' },
  { id: 'read', label: 'Read' },
  { id: 'bots', label: 'Bots' },
  { id: 'export', label: 'Export' },
  { id: 'settings', label: 'Settings' }
]

const book = computed(() => bookStore.currentBook)
const chunks = computed(() => bookStore.chunks)

const isBookEffectivelyLocked = computed(() => {
  const currentBookVal = book.value; // book is already bookStore.currentBook
  const job = bookStore.currentJob as Job | null; // Cast for state access
  
  // If there's no current book loaded yet, or if loading is in progress, consider it locked/unavailable.
  // isLoading.value handles the initial page load scenario.
  if (isLoading.value) return true; 
  if (!currentBookVal) return true; 

  // Check local is_locked flag or if the currentJob in bookStore is active for this book
  return currentBookVal.is_locked || 
         (job && job.book_id === currentBookVal.book_id && 
          (job.state === 'running' || job.state === 'waiting'));
});

const overlayTitle = computed(() => {
  // Could be more dynamic based on job type if other jobs lock the book
  const job = bookStore.currentJob;
  if (job && job.job_type === 'create_foundation'){
    return "Creating Book Foundation";
  }
  return "Processing Book"; 
});

const overlayMessage = computed(() => {
  const job = bookStore.currentJob as Job | null;
  if (job && book.value && job.book_id === book.value.book_id) {
    if (job.state === 'waiting') return "Job is queued and will start shortly...";
    if (job.state === 'running') return "Processing... please wait while we build your book's structure.";
    // Could add messages for other states if needed
  }
  return "Please wait while we prepare your book...";
});

const overlayJobStatus = computed(() => {
  const job = bookStore.currentJob as Job | null;
  if (job && book.value && job.book_id === book.value.book_id) {
    return `Status: ${job.state}`;
  }
  return "";
});

onMounted(async () => {
  const bookId = route.params.bookId as string
  if (bookId) {
    isLoading.value = true
    try {
      await bookStore.loadBook(bookId)
      await bookStore.loadChunks(bookId)
      await bookStore.loadJobs(bookId)
    } catch (error) {
      console.error('Failed to load book:', error)
      router.push('/dashboard')
    } finally {
      isLoading.value = false
    }
  }
})

function editChunk(chunkId: string) {
  router.push(`/books/${route.params.bookId}/chunks/${chunkId}/edit`)
}

function reorderChunks(fromIndex: number, toIndex: number) {
  // TODO: Implement drag-and-drop reordering
  console.log('Reorder chunks:', { fromIndex, toIndex })
}

function handleBookUpdated(updatedBook: any) {
  // Update the current book in the store
  if (bookStore.currentBook) {
    bookStore.currentBook = { ...bookStore.currentBook, ...updatedBook }
  }
}
</script>

<style scoped>
.book-viewer {
  min-height: 100vh;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

.book-header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 1.5rem 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.book-title-section {
  max-width: 1200px;
  margin: 0 auto;
}

.back-button {
  background: none;
  border: none;
  color: #6366f1;
  font-size: 0.875rem;
  cursor: pointer;
  margin-bottom: 0.5rem;
  padding: 0.25rem 0;
  transition: color 0.2s;
}

.back-button:hover {
  color: #4f46e5;
}

.book-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 0.5rem 0;
}

.book-meta {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.book-stats {
  color: #64748b;
  font-size: 0.875rem;
}

.book-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.book-status.locked {
  background: #fef3c7;
  color: #92400e;
}

.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid #fbbf24;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.tab-navigation {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 2rem;
}

.tab-navigation {
  display: flex;
  max-width: 1200px;
  margin: 0 auto;
}

.tab-button {
  background: none;
  border: none;
  padding: 1rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-button:hover {
  color: #6366f1;
}

.tab-button.active {
  color: #6366f1;
  border-bottom-color: #6366f1;
}

.tab-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.placeholder-content {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.placeholder-content h3 {
  font-size: 1.5rem;
  color: #1e293b;
  margin-bottom: 1rem;
}

.placeholder-content p {
  color: #64748b;
  margin-bottom: 0.5rem;
}

.placeholder-content em {
  color: #94a3b8;
}

.content-blurred {
  filter: blur(4px);
  pointer-events: none; /* Optional: prevent interaction with blurred content */
}
</style>
