<template>
  <div class="bot-manager">
    <div class="bot-header">
      <h3>Bot Management</h3>
      <button @click="createBot" class="create-bot-button">
        + Create New Bot
      </button>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      Loading bots...
    </div>

    <div v-else-if="botChunks.length === 0" class="no-bots">
      <div class="no-bots-content">
        <h4>No Bots Created Yet</h4>
        <p>Bots are AI assistants that can generate, edit, and review your text content.</p>
        <p>Create your first bot to start using AI text generation features.</p>
        <button @click="createBot" class="create-bot-button primary">
          Create Your First Bot
        </button>
      </div>
    </div>

    <div v-else class="bot-list">
      <div 
        v-for="bot in botChunks" 
        :key="bot.chunk_id"
        class="bot-card"
        @click="editBot(bot.chunk_id)"
      >
        <div class="bot-card-header">
          <h4 class="bot-name">{{ getBotName(bot) }}</h4>
          <span class="bot-llm">{{ getBotLLM(bot) }}</span>
        </div>
        <div class="bot-card-body">
          <p class="bot-description">{{ getBotDescription(bot) }}</p>
          <div class="bot-meta">
            <span class="bot-version">v{{ bot.version }}</span>
            <span class="bot-updated">Updated {{ formatDate(bot.updated_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useBookStore } from '../stores/book'
import { apiService } from '../services/api'

const router = useRouter()
const route = useRoute()
const bookStore = useBookStore()

const loading = ref(false)

const botChunks = computed(() => {
  return bookStore.chunks.filter(chunk => chunk.type === 'bot')
})

onMounted(async () => {
  // Bots should already be loaded with chunks, but we can refresh if needed
  if (bookStore.chunks.length === 0) {
    loading.value = true
    try {
      await bookStore.loadChunks(route.params.bookId as string)
    } finally {
      loading.value = false
    }
  }
})

async function createBot() {
  try {
    const bookId = route.params.bookId as string
    
    // Create a new bot chunk with default properties
    const newBot = await apiService.createChunk(bookId, {
      type: 'bot',
      title: 'New Bot',
      text: '',
      props: {
        name: 'New Bot',
        llm_alias: 'Writer',
        description: 'A new AI bot for text generation',
        system_prompt: 'You are a helpful AI writing assistant.',
        temperature: 0.7
      },
      parent_id: null,
      order_index: botChunks.value.length
    })
    
    // Add to store
    bookStore.chunks.push(newBot)
    
    // Navigate to edit the new bot
    editBot(newBot.chunk_id)
  } catch (error) {
    console.error('Failed to create bot:', error)
    alert('Failed to create bot. Please try again.')
  }
}

function editBot(chunkId: string) {
  router.push(`/books/${route.params.bookId}/chunks/${chunkId}/edit`)
}

function getBotName(bot: any): string {
  return bot.props?.name || bot.title || 'Unnamed Bot'
}

function getBotLLM(bot: any): string {
  return bot.props?.llm_alias || 'Unknown LLM'
}

function getBotDescription(bot: any): string {
  return bot.props?.description || 'No description provided'
}

function formatDate(dateString: string): string {
  if (!dateString) return 'Unknown'
  
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  
  return date.toLocaleDateString()
}
</script>

<style scoped>
.bot-manager {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.bot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.bot-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.create-bot-button {
  background: #6366f1;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.create-bot-button:hover {
  background: #4f46e5;
}

.create-bot-button.primary {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
}

.loading {
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

.no-bots {
  padding: 3rem 2rem;
}

.no-bots-content {
  text-align: center;
  max-width: 400px;
  margin: 0 auto;
}

.no-bots-content h4 {
  font-size: 1.25rem;
  color: #1e293b;
  margin-bottom: 1rem;
}

.no-bots-content p {
  color: #64748b;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.bot-list {
  padding: 1.5rem;
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.bot-card {
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.bot-card:hover {
  border-color: #6366f1;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.bot-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.bot-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.bot-llm {
  background: #e0e7ff;
  color: #3730a3;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.bot-card-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.bot-description {
  color: #64748b;
  font-size: 0.875rem;
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.bot-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: #94a3b8;
}

.bot-version {
  background: #f1f5f9;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
}
</style>
