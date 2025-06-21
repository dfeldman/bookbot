<template>
  <div class="generate-chunk-panel">
    <div class="panel-header">
      <h3 class="panel-title">
        <span class="generate-icon">✨</span>
        Generate Text
      </h3>
      <div class="panel-subtitle">
        Use AI to generate or edit chunk content
      </div>
    </div>

    <div class="panel-body">
      <!-- Generate Mode Selection -->
      <div class="form-group">
        <label class="form-label">Generate Mode</label>
        <select 
          v-model="selectedMode" 
          class="form-select"
          :disabled="isGenerating"
        >
          <option value="">Select a mode...</option>
          <option value="write">Write - Generate new content from outline</option>
          <option value="rewrite">Rewrite - Rewrite using different approach</option>
          <option value="edit">Edit - Review and improve existing text</option>
          <option value="copyedit">Copyedit - Light cleanup and polish</option>
          <option value="review">Review - Create review (separate chunk)</option>
        </select>
      </div>

      <!-- Bot Selection -->
      <div class="form-group">
        <label class="form-label">Bot</label>
        <select 
          v-model="selectedBot" 
          class="form-select"
          :disabled="isGenerating || !selectedMode"
        >
          <option value="">Select a bot...</option>
          <option 
            v-for="bot in bots" 
            :key="bot.chunk_id" 
            :value="bot.chunk_id"
          >
            {{ bot.props.name }} ({{ bot.props.llm_alias }})
          </option>
        </select>
        <div v-if="bots.length === 0" class="no-bots-message">
          No bots configured. <router-link to="/bots">Create bots</router-link> to get started.
        </div>
      </div>

      <!-- Generation Options -->
      <div v-if="selectedMode && selectedBot" class="form-group">
        <label class="form-label">Options</label>
        <div class="checkbox-group">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="options.preserveFormatting"
              :disabled="isGenerating"
            >
            Preserve formatting
          </label>
          <label class="checkbox-label" v-if="selectedMode === 'edit'">
            <input 
              type="checkbox" 
              v-model="options.trackChanges"
              :disabled="isGenerating"
            >
            Track changes
          </label>
        </div>
      </div>

      <!-- Generation Status -->
      <div v-if="isGenerating" class="generation-status">
        <div class="status-indicator">
          <div class="spinner"></div>
          <span>Generating {{ selectedMode }}...</span>
        </div>
        <div class="status-details">
          Chunk is locked during generation
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="panel-actions">
        <button 
          @click="generateText"
          :disabled="!canGenerate"
          class="btn btn-primary"
        >
          <span v-if="!isGenerating">Generate</span>
          <span v-else>
            <div class="btn-spinner"></div>
            Generating...
          </span>
        </button>
        
        <button 
          v-if="currentGeneratingJob"
          @click="cancelGeneration"
          class="btn btn-secondary"
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useBookStore } from '../stores/book'
import { storeToRefs } from 'pinia'
import { type Job } from '@/stores/types'

// Props
interface Props {
  chunkId: string
  bookId: string
  chunkType?: string
}

const props = defineProps<Props>()
const bookStore = useBookStore()
const { bots, isGenerating, jobs } = storeToRefs(bookStore)

// State
const selectedMode = ref('')
const selectedBot = ref('')
const options = ref({
  preserveFormatting: false,
  trackChanges: false
})

// Computed
const canGenerate = computed(() => {
  return selectedMode.value &&
         selectedBot.value &&
         !isGenerating.value &&
         (props.chunkType === 'scene' || !props.chunkType) // Only allow for scene chunks
})

const currentGeneratingJob = computed(() => {
  return jobs.value.find((job: Job) => 
    job.props?.input_chunk_id === props.chunkId &&
    (job.state === 'running' || job.state === 'waiting')
  )
})

// Methods
async function generateText() {
  if (!canGenerate.value) return
  
  bookStore.startSceneGeneration(
    props.chunkId,
    selectedBot.value,
    selectedMode.value,
    options.value
  )
}

async function cancelGeneration() {
  if (!currentGeneratingJob.value) return
  bookStore.cancelGeneration(currentGeneratingJob.value.job_id)
}

// Watchers
watch(() => props.bookId, (newBookId) => {
  if (newBookId) {
    bookStore.loadBots(newBookId)
  }
}, { immediate: true })

// Lifecycle
onMounted(() => {
  if (props.bookId) {
    bookStore.loadBots(props.bookId)
  }
})
</script>

<style scoped>
.generate-chunk-panel {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.panel-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.25rem 0;
  font-size: 1.125rem;
  font-weight: 600;
}

.generate-icon {
  font-size: 1.25rem;
}

.panel-subtitle {
  font-size: 0.875rem;
  opacity: 0.9;
  margin: 0;
}

.panel-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.form-select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  background: white;
  transition: border-color 0.2s;
}

.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-select:disabled {
  background: #f9fafb;
  color: #9ca3af;
  cursor: not-allowed;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #4b5563;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  margin: 0;
}

.no-bots-message {
  font-size: 0.875rem;
  color: #6b7280;
  margin-top: 0.5rem;
}

.no-bots-message a {
  color: #667eea;
  text-decoration: none;
}

.no-bots-message a:hover {
  text-decoration: underline;
}

.generation-status {
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: #92400e;
}

.status-details {
  font-size: 0.875rem;
  color: #b45309;
  margin-top: 0.25rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #f59e0b;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.panel-actions {
  display: flex;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5a67d8;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  background: #d1d5db;
}

.btn-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .panel-body {
    padding: 1rem;
  }
  
  .panel-actions {
    flex-direction: column;
  }
  
  .btn {
    justify-content: center;
  }
}
</style>
