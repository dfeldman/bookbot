<template>
  <div class="book-viewer">
    <!-- Status Bar -->
    <StatusBar />
    
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
          <span v-if="book?.is_locked" class="book-status locked">
            <div class="spinner"></div>
            Job Running
          </span>
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
import StatusBar from '../components/StatusBar.vue'
import BookIndex from '../components/BookIndex.vue'
import BookReader from '../components/BookReader.vue'
import BotManager from '../components/BotManager.vue'
import BookExport from '../components/BookExport.vue'
import BookSettings from '../components/BookSettings.vue'

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
</style>
