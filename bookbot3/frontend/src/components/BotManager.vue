<template>
  <div class="bot-manager-layout">
    <!-- Left Panel: List of Bots and Tasks -->
    <div class="list-panel">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span>Loading...</span>
      </div>
      
      <div v-else>
        <!-- Bots Section -->
        <div class="list-section">
          <div class="list-header">
            <h4>Bots</h4>
            <button @click="createBot" class="create-button">+ New Bot</button>
          </div>
          <ul class="item-list">
            <li v-if="botChunks.length === 0" class="empty-list-item">No bots yet.</li>
            <li 
              v-for="chunk in botChunks" 
              :key="chunk.chunk_id"
              @click="selectChunk(chunk)"
              :class="{ 'active': selectedChunk?.chunk_id === chunk.chunk_id }"
            >
              {{ chunk.props.name || 'Untitled Bot' }}
            </li>
          </ul>
        </div>

        <!-- Bot Tasks Section -->
        <div class="list-section">
          <div class="list-header">
            <h4>Bot Tasks</h4>
            <button @click="createBotTask" class="create-button">+ New Task</button>
          </div>
          <ul class="item-list">
            <li v-if="botTaskChunks.length === 0" class="empty-list-item">No tasks yet.</li>
            <li 
              v-for="chunk in botTaskChunks" 
              :key="chunk.chunk_id"
              @click="selectChunk(chunk)"
              :class="{ 'active': selectedChunk?.chunk_id === chunk.chunk_id }"
            >
              {{ chunk.props.name || 'Untitled Task' }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Right Panel: Editor -->
    <div class="editor-panel">
      <div v-if="!selectedChunk" class="editor-placeholder">
        <p>Select a bot or task to begin editing.</p>
      </div>
      <div v-else class="editor-container">
        <BotEditor v-if="selectedChunk.type === 'bot'" v-model="selectedChunk" @update:modelValue="handleChunkUpdate" />
        <BotTaskEditor v-else-if="selectedChunk.type === 'bot_task'" v-model="selectedChunk" @update:modelValue="handleChunkUpdate" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useBookStore } from '../stores/book'
import { apiService } from '../services/api'
import type { Chunk } from '../stores/book'
import BotEditor from './BotEditor.vue'
import BotTaskEditor from './BotTaskEditor.vue'

const route = useRoute()
const bookStore = useBookStore()

const loading = ref(false)
const selectedChunk = ref<Chunk | null>(null)
let autoSaveTimer: number | null = null

const botChunks = computed(() => bookStore.chunks.filter(c => c.type === 'bot'))
const botTaskChunks = computed(() => bookStore.chunks.filter(c => c.type === 'bot_task'))

onMounted(async () => {
  if (bookStore.chunks.length === 0) {
    loading.value = true
    try {
      await bookStore.loadChunks(route.params.bookId as string)
    } finally {
      loading.value = false
    }
  }
})

onBeforeUnmount(() => {
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer)
  }
})

function selectChunk(chunk: Chunk) {
  // Deep copy to prevent direct mutation before save
  selectedChunk.value = JSON.parse(JSON.stringify(chunk))
}

async function createChunk(type: 'bot' | 'bot_task') {
  try {
    const bookId = route.params.bookId as string
    const isBot = type === 'bot'
    
    const defaultData = {
      type,
      text: isBot ? 'You are a helpful AI assistant.' : '',
      props: {
        name: isBot ? 'New Bot' : 'New Task',
        llm_group: 'Writer',
        ...(isBot ? { temperature: 0.7 } : { jobs: 'GenerateChunk' })
      },
    }

    const newChunk = await apiService.createChunk(bookId, defaultData)
    await bookStore.loadChunks(bookId) // Reload to get the new chunk
    selectChunk(newChunk)

  } catch (error) {
    console.error(`Failed to create ${type}:`, error)
    alert(`Failed to create ${type}. Please try again.`)
  }
}

const createBot = () => createChunk('bot')
const createBotTask = () => createChunk('bot_task')

function handleChunkUpdate(updatedChunk: Chunk) {
  selectedChunk.value = updatedChunk
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer)
  }
  autoSaveTimer = window.setTimeout(() => {
    saveSelectedChunk()
  }, 1000) // 1 second delay
}

async function saveSelectedChunk() {
  if (!selectedChunk.value) return

  try {
    const chunkToSave = selectedChunk.value
    const updated = await apiService.updateChunk(chunkToSave.chunk_id, {
      text: chunkToSave.text,
      props: chunkToSave.props,
      type: chunkToSave.type, // Ensure type is preserved
    })
    
    // Update the chunk in the store without a full reload
    bookStore.updateChunkInStore(updated)

  } catch (error) {
    console.error('Failed to save chunk:', error)
    // Optionally show a save error to the user
  }
}

</script>

<style scoped>
.bot-manager-layout {
  display: flex;
  height: calc(100vh - 200px); /* Adjust based on header/footer height */
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  overflow: hidden;
}

.list-panel {
  width: 300px;
  flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  overflow-y: auto;
  padding: 1rem;
}

.list-section {
  margin-bottom: 1.5rem;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding: 0 0.5rem;
}

.list-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
}

.create-button {
  background: none;
  border: 1px solid #cbd5e1;
  color: #475569;
  padding: 0.25rem 0.6rem;
  font-size: 0.8rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
}

.create-button:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
}

.item-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.item-list li {
  padding: 0.6rem 0.75rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
  font-size: 0.875rem;
  color: #334155;
}

.item-list li:hover {
  background-color: #f1f5f9;
}

.item-list li.active {
  background-color: #6366f1;
  color: white;
  font-weight: 500;
}

.empty-list-item {
  color: #94a3b8;
  font-style: italic;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
}

.editor-panel {
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.editor-placeholder {
  text-align: center;
  color: #94a3b8;
}

.editor-container {
  width: 100%;
  height: 100%;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3rem;
  color: #64748b;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e2e8f0;
  border-top: 2px solid #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
