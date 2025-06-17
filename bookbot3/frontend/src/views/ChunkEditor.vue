<template>
  <div class="chunk-editor">
    <!-- Status Bar -->
    <StatusBar />
    
    <!-- Editor Header -->
    <div class="editor-header">
      <div class="header-content">
        <div class="navigation">
          <button @click="goBack" class="back-button">
            ← Back to Book
          </button>
          <div class="breadcrumb">
            <span>{{ book?.props?.name || 'Untitled Book' }}</span>
            <span class="separator">›</span>
            <span>{{ getChunkDisplayName() }}</span>
          </div>
        </div>
        
        <div class="editor-actions">
          <button 
            @click="saveChunk" 
            :disabled="!hasChanges || isSaving"
            class="save-button"
            :class="{ saving: isSaving }"
          >
            {{ isSaving ? 'Saving...' : 'Save Changes' }}
          </button>
          <button @click="showDeleteConfirm = true" class="delete-button">
            Delete Chunk
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading chunk...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <h3>❌ Error Loading Chunk</h3>
      <p>{{ error }}</p>
      <button @click="loadChunk" class="retry-button">Retry</button>
    </div>

    <!-- Editor Content -->
    <div v-else-if="chunk" class="editor-content">
      <!-- Chunk Metadata -->
      <div class="chunk-metadata">
        <div class="metadata-grid">
          <div class="metadata-item">
            <label>Type:</label>
            <select v-model="chunkData.type" @change="markAsChanged">
              <option value="scene">Scene</option>
              <option value="chapter">Chapter</option>
              <option value="outline">Outline</option>
              <option value="character">Character</option>
              <option value="setting">Setting</option>
              <option value="notes">Notes</option>
              <option value="other">Other</option>
            </select>
          </div>
          
          <div class="metadata-item">
            <label>Chapter:</label>
            <input 
              type="number" 
              v-model.number="chunkData.chapter" 
              @input="markAsChanged"
              min="0"
              placeholder="Chapter number"
            />
          </div>
          
          <div class="metadata-item">
            <label>Order:</label>
            <input 
              type="number" 
              v-model.number="chunkData.order" 
              @input="markAsChanged"
              min="1"
              placeholder="Order in chapter"
            />
          </div>
          
          <div class="metadata-item">
            <label>Word Count:</label>
            <span class="word-count">{{ currentWordCount }}</span>
          </div>
        </div>
        
        <!-- Chunk Properties -->
        <div class="chunk-properties">
          <h4>Properties</h4>
          <div class="properties-grid">
            <div class="property-item">
              <label>Name:</label>
              <input 
                v-model="chunkData.props!.name" 
                @input="markAsChanged"
                placeholder="Chunk name"
              />
            </div>
            
            <div class="property-item">
              <label>Scene ID:</label>
              <input 
                v-model="chunkData.props!.scene_id" 
                @input="markAsChanged"
                placeholder="Scene identifier"
              />
            </div>
            
            <div class="property-item">
              <label>Scene Title:</label>
              <input 
                v-model="chunkData.props!.scene_title" 
                @input="markAsChanged"
                placeholder="Scene title"
              />
            </div>
            
            <div class="property-item">
              <label>Tags:</label>
              <input 
                v-model="tagsInput" 
                @input="updateTags"
                placeholder="Comma-separated tags"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Context Panel for Scene Chunks (Above Text Editor) -->
      <div v-if="isScene && hasSceneId" class="context-panel-container">
        <SceneContextPanel
          :context="contextData"
          :loading="contextLoading"
          :error="contextError"
          @refresh="loadContext"
        />
      </div>

      <!-- Generate Text Panel for Scene Chunks -->
      <div v-if="isScene" class="generate-panel-container">
        <GenerateChunkText
          :chunk-id="chunk.chunk_id"
          :book-id="bookId!"
          :chunk-type="chunk.type"
          @generation-started="handleGenerationStarted"
          @generation-completed="handleGenerationCompleted"
          @generation-cancelled="handleGenerationCancelled"
          @error="handleGenerationError"
        />
      </div>

      <!-- Bot Configuration Panel for Bot Chunks -->
      <div v-if="isBot" class="bot-config-container">
        <div class="bot-config-panel">
          <h4>Bot Configuration</h4>
          <div class="bot-config-form">
            <div class="form-row">
              <div class="form-group">
                <label for="bot-name">Bot Name</label>
                <input
                  id="bot-name"
                  v-model="chunkData.props!.name"
                  type="text"
                  placeholder="Enter bot name"
                  @input="markAsChanged"
                />
              </div>
              <div class="form-group">
                <label for="llm-alias">LLM Alias</label>
                <select
                  id="llm-alias"
                  v-model="chunkData.props!.llm_alias"
                  @change="markAsChanged"
                >
                  <option value="Writer">Writer</option>
                  <option value="Thinker">Thinker</option>
                  <option value="Explicit">Explicit</option>
                  <option value="Large-context">Large-context</option>
                </select>
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label for="temperature">Temperature</label>
                <input
                  id="temperature"
                  v-model.number="chunkData.props!.temperature"
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  @input="markAsChanged"
                />
              </div>
              <div class="form-group">
                <label for="bot-description">Description</label>
                <input
                  id="bot-description"
                  v-model="chunkData.props!.description"
                  type="text"
                  placeholder="Brief description of this bot"
                  @input="markAsChanged"
                />
              </div>
            </div>

            <div class="form-group">
              <label for="system-prompt">System Prompt</label>
              <textarea
                id="system-prompt"
                v-model="chunkData.props!.system_prompt"
                rows="4"
                placeholder="System prompt that defines the bot's personality and behavior"
                @input="markAsChanged"
              ></textarea>
            </div>
          </div>
        </div>
      </div>

      <!-- Text Editor -->
      <div class="text-editor-container">
        <h4>Content</h4>
        <TextEditor
          v-model="chunkData.text!"
          :show-toolbar="true"
          :show-word-count="false"
          :placeholder="getPlaceholder()"
          @update:model-value="markAsChanged"
        />
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="showDeleteConfirm = false">
      <div class="modal" @click.stop>
        <h3>Delete Chunk</h3>
        <p>Are you sure you want to delete this chunk? This action cannot be undone.</p>
        <div class="modal-actions">
          <button @click="showDeleteConfirm = false" class="cancel-button">Cancel</button>
          <button @click="deleteChunk" class="delete-button">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBookStore } from '../stores/book'
import { apiService } from '../services/api'
import StatusBar from '../components/StatusBar.vue'
import TextEditor from '../components/TextEditor.vue'
import SceneContextPanel from '../components/SceneContextPanel.vue'
import GenerateChunkText from '../components/GenerateChunkText.vue'

// Types
interface Chunk {
  chunk_id: string
  type: string
  chapter: number | null
  order: number
  text: string
  word_count: number
  version: number
  is_locked: boolean
  props: {
    name?: string
    scene_id?: string
    scene_title?: string
    chapter_title?: string
    tags?: string[]
    [key: string]: any
  }
  created_at: string
  updated_at: string
}

const route = useRoute()
const router = useRouter()
const bookStore = useBookStore()

// Reactive state
const chunk = ref<Chunk | null>(null)
const chunkData = ref<Partial<Chunk>>({
  type: 'scene',
  chapter: null,
  order: 1,
  text: '',
  props: {
    name: '',
    scene_id: '',
    scene_title: '',
    tags: [] as string[],
    // Bot-specific properties
    llm_alias: 'Writer',
    temperature: 0.7,
    description: '',
    system_prompt: ''
  }
})
const originalChunkData = ref<any>(null)
const hasChanges = ref(false)
const isLoading = ref(false)
const isSaving = ref(false)
const error = ref('')
const showDeleteConfirm = ref(false)
const tagsInput = ref('')

// Context panel state
const contextData = ref({
  outline_section: '',
  characters_sections: [],
  settings_sections: [],
  tags: [],
  available: false
})
const contextLoading = ref(false)
const contextError = ref<string | null>(null)

// Computed
const book = computed(() => bookStore.currentBook)
const bookId = computed(() => route.params.bookId as string)
const chunkId = computed(() => route.params.chunkId as string)

const currentWordCount = computed(() => {
  if (!chunkData.value.text) return 0
  return chunkData.value.text.trim().split(/\s+/).filter((word: string) => word.length > 0).length
})

// Context panel computed properties
const isScene = computed(() => chunkData.value.type === 'scene')
const isBot = computed(() => chunkData.value.type === 'bot')
const hasSceneId = computed(() => Boolean(chunkData.value.props?.scene_id))

// Functions
function markAsChanged() {
  hasChanges.value = true
}

function updateTags() {
  const tags = tagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0)
  if (chunkData.value.props) {
    chunkData.value.props.tags = tags
    markAsChanged()
  }
}

function getChunkDisplayName() {
  if (chunk.value?.props?.name) {
    return chunk.value.props.name
  }
  if (chunk.value?.props?.scene_title) {
    return chunk.value.props.scene_title
  }
  if (chunk.value?.type) {
    const type = chunk.value.type.charAt(0).toUpperCase() + chunk.value.type.slice(1)
    if (chunk.value.chapter) {
      return `${type} - Chapter ${chunk.value.chapter}`
    }
    return type
  }
  return 'Untitled Chunk'
}

function getPlaceholder() {
  switch (chunkData.value.type) {
    case 'scene':
      return 'Write your scene content here...'
    case 'chapter':
      return 'Write your chapter content here...'
    case 'outline':
      return 'Write your outline here...'
    case 'character':
      return 'Describe your character here...'
    case 'setting':
      return 'Describe your setting here...'
    case 'notes':
      return 'Write your notes here...'
    default:
      return 'Write your content here...'
  }
}

async function loadChunk() {
  if (!chunkId.value) return
  
  isLoading.value = true
  error.value = ''
  
  try {
    const response = await apiService.getChunk(chunkId.value)
    chunk.value = response
    
    // Initialize editable data
    chunkData.value = {
      type: response.type || 'scene',
      chapter: response.chapter,
      order: response.order || 1,
      text: response.text || '',
      props: {
        name: response.props?.name || '',
        scene_id: response.props?.scene_id || '',
        scene_title: response.props?.scene_title || '',
        tags: response.props?.tags || [],
        // Bot-specific properties
        llm_alias: response.props?.llm_alias || 'Writer',
        temperature: response.props?.temperature || 0.7,
        description: response.props?.description || '',
        system_prompt: response.props?.system_prompt || '',
        // Ensure other properties are preserved
        ...response.props
      }
    }
    
    // Store original data for comparison
    originalChunkData.value = JSON.parse(JSON.stringify(chunkData.value)) as any
    
    // Update tags input
    if (chunkData.value.props && chunkData.value.props.tags) {
      tagsInput.value = chunkData.value.props.tags.join(', ')
    }
    
    hasChanges.value = false
  } catch (err) {
    console.error('Failed to load chunk:', err)
    error.value = 'Failed to load chunk. Please try again.'
  } finally {
    isLoading.value = false
  }
}

async function saveChunk() {
  if (!hasChanges.value || isSaving.value) return
  
  isSaving.value = true
  
  try {
    const updateData = {
      type: chunkData.value.type,
      chapter: chunkData.value.chapter,
      order: chunkData.value.order,
      text: chunkData.value.text,
      props: {
        ...chunkData.value.props,
        word_count: currentWordCount.value
      }
    }
    
    await apiService.updateChunk(chunkId.value, updateData)
    
    // Update local chunk data
    chunk.value = { ...chunk.value, ...updateData } as any
    originalChunkData.value = JSON.parse(JSON.stringify(chunkData.value)) as any
    hasChanges.value = false
    
    // Show success feedback (you could add a toast notification here)
    console.log('Chunk saved successfully')
    
  } catch (err) {
    console.error('Failed to save chunk:', err)
    // Show error feedback (you could add a toast notification here)
    alert('Failed to save chunk. Please try again.')
  } finally {
    isSaving.value = false
  }
}

async function deleteChunk() {
  try {
    await apiService.deleteChunk(chunkId.value)
    showDeleteConfirm.value = false
    // Navigate back to book viewer
    router.push(`/books/${bookId.value}`)
  } catch (err) {
    console.error('Failed to delete chunk:', err)
    alert('Failed to delete chunk. Please try again.')
  }
}

function goBack() {
  if (hasChanges.value) {
    const confirmed = confirm('You have unsaved changes. Are you sure you want to leave?')
    if (!confirmed) return
  }
  router.push(`/books/${bookId.value}`)
}

// Context functions
async function loadContext() {
  if (!isScene.value || !hasSceneId.value || !chunkId.value) {
    return
  }

  contextLoading.value = true
  contextError.value = null

  try {
    const context = await apiService.getChunkContext(bookId.value, chunkId.value)
    contextData.value = context
  } catch (err: any) {
    console.error('Failed to load context:', err)
    contextError.value = err.response?.data?.error || 'Failed to load context'
  } finally {
    contextLoading.value = false
  }
}

// Auto-save functionality (optional)
let autoSaveTimer: NodeJS.Timeout | null = null

function startAutoSave() {
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer)
  }
  
  autoSaveTimer = setTimeout(() => {
    if (hasChanges.value && !isSaving.value) {
      saveChunk()
    }
  }, 30000) // Auto-save after 30 seconds of inactivity
}

watch(() => chunkData.value.text, () => {
  markAsChanged()
  startAutoSave()
})

// Watch for scene ID changes to load context
watch([isScene, hasSceneId], () => {
  if (isScene.value && hasSceneId.value) {
    loadContext()
  }
}, { immediate: false })

// Generation handlers
function handleGenerationStarted(jobId: string) {
  console.log('Generation started:', jobId)
  // Mark chunk as locked locally
  if (chunk.value) {
    chunk.value.is_locked = true
  }
  // Reload jobs to show the new generation job
  if (bookId.value) {
    bookStore.loadJobs(bookId.value)
  }
}

function handleGenerationCompleted(chunkId: string) {
  console.log('Generation completed:', chunkId)
  // Reload the chunk to get the new content
  loadChunk()
  // Reload jobs to update status
  if (bookId.value) {
    bookStore.loadJobs(bookId.value)
  }
}

function handleGenerationCancelled(chunkId: string) {
  console.log('Generation cancelled:', chunkId)
  // Mark chunk as unlocked locally
  if (chunk.value) {
    chunk.value.is_locked = false
  }
  // Reload jobs to update status
  if (bookId.value) {
    bookStore.loadJobs(bookId.value)
  }
}

function handleGenerationError(message: string) {
  console.error('Generation error:', message)
  error.value = message
  // Mark chunk as unlocked locally
  if (chunk.value) {
    chunk.value.is_locked = false
  }
}

// Lifecycle
onMounted(async () => {
  // Load book if not already loaded
  if (!book.value && bookId.value) {
    try {
      await bookStore.loadBook(bookId.value)
      await bookStore.loadJobs(bookId.value)
    } catch (err) {
      console.error('Failed to load book:', err)
    }
  }
  
  await loadChunk()
  
  // Load context after chunk is loaded
  if (isScene.value && hasSceneId.value) {
    await loadContext()
  }
})

onBeforeUnmount(() => {
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer)
  }
})

// Prevent navigation if there are unsaved changes
window.addEventListener('beforeunload', (e) => {
  if (hasChanges.value) {
    e.preventDefault()
    e.returnValue = ''
  }
})
</script>

<style scoped>
.chunk-editor {
  min-height: 100vh;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

.editor-header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 1rem 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navigation {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.back-button {
  background: none;
  border: none;
  color: #6366f1;
  font-size: 0.875rem;
  cursor: pointer;
  padding: 0.5rem 0;
  transition: color 0.2s ease;
}

.back-button:hover {
  color: #4f46e5;
}

.breadcrumb {
  font-size: 0.875rem;
  color: #64748b;
}

.separator {
  margin: 0 0.5rem;
  color: #cbd5e1;
}

.editor-actions {
  display: flex;
  gap: 0.75rem;
}

.save-button {
  background: #10b981;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.save-button:hover:not(:disabled) {
  background: #059669;
  transform: translateY(-1px);
}

.save-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.save-button.saving {
  background: #6b7280;
}

.delete-button {
  background: #ef4444;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.delete-button:hover {
  background: #dc2626;
  transform: translateY(-1px);
}

.loading-container, .error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f4f6;
  border-top: 4px solid #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.retry-button {
  background: #6366f1;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  margin-top: 1rem;
}

.editor-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Layout for editor with context panel */
.editor-layout {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.editor-layout.with-context {
  flex-direction: row;
  gap: 2rem;
  align-items: flex-start;
}

.main-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.context-sidebar {
  flex: 0 0 400px;
  max-width: 400px;
}

.chunk-metadata {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.metadata-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metadata-item label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.metadata-item input, .metadata-item select {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.word-count {
  font-size: 0.875rem;
  color: #6b7280;
  padding: 0.75rem 0;
}

.chunk-properties h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
}

.properties-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.property-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.property-item label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.property-item input {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.text-editor-container {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  flex: 1;
}

.text-editor-container h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 400px;
  width: 90%;
  text-align: center;
}

.modal h3 {
  margin: 0 0 1rem 0;
  color: #374151;
}

.modal p {
  margin: 0 0 2rem 0;
  color: #6b7280;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.cancel-button {
  background: #f3f4f6;
  color: #374151;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
}

/* Responsive Design */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .editor-actions {
    justify-content: center;
  }

  .metadata-grid, .properties-grid {
    grid-template-columns: 1fr;
  }

  .editor-content {
    padding: 1rem;
  }

  /* Stack layout on mobile */
  .editor-layout.with-context {
    flex-direction: column;
  }

  .context-sidebar {
    flex: none;
    max-width: none;
  }
}

/* Context Panel Container */
.context-panel-container {
  margin: 0 0 1.5rem 0;
}

/* Generate Panel Container */
.generate-panel-container {
  margin: 0 0 1.5rem 0;
}

/* Bot Configuration Panel */
.bot-config-container {
  margin: 0 0 1.5rem 0;
}

.bot-config-panel {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.bot-config-panel h4 {
  margin: 0 0 1.5rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
}

.bot-config-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-group textarea {
  resize: vertical;
  min-height: 100px;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
