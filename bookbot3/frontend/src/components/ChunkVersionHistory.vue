<template>
  <div class="version-history">
    <div v-if="isVersionsLoading && versions.length === 0" class="loading">
      <div class="spinner"></div>
      <p>Loading version history...</p>
    </div>
    
    <div v-else-if="versionsError" class="error">
      <p>{{ versionsError }}</p>
      <button @click="loadVersions" class="retry-button">Retry</button>
    </div>
    
    <div v-else>
      <div class="header">
        <h3>Version History</h3>
        <button @click="$emit('close')" class="close-button">&times;</button>
      </div>
      
      <div v-if="versions.length === 0" class="empty-state">
        <p>No version history available.</p>
      </div>
      
      <div v-else class="versions-list">
        <div v-for="version in versions" :key="version.version" class="version-item" :class="{ 'is-current': version.is_latest }">
          <div class="version-info">
            <div class="version-number">
              <span class="badge" :class="{ 'current-badge': version.is_latest }">
                {{ version.is_latest ? 'Current' : `v${version.version}` }}
              </span>
            </div>
            <div class="version-details">
              <div class="timestamp">{{ formatDate(version.created_at) }}</div>
              <div class="word-count">{{ version.word_count }} words</div>
            </div>
          </div>
          
          <div class="version-actions">
            <button 
              v-if="!version.is_latest" 
              @click="viewVersion(version.version)" 
              class="view-button"
              :class="{ 'active': selectedVersion === version.version }"
            >
              View
            </button>
            <button 
              v-if="!version.is_latest && !isRestoring" 
              @click="restoreVersion(version.version)" 
              class="restore-button"
            >
              Restore
            </button>
            <div v-if="isRestoring && selectedVersion === version.version" class="restoring-indicator">
              Restoring...
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="selectedVersion" class="version-preview">
        <h4>Preview of Version {{ selectedVersion }}</h4>
        <div v-if="isPreviewLoading" class="loading-preview">
          <div class="spinner"></div>
        </div>
        <div v-else class="preview-content">
          <MarkdownEditor 
            :modelValue="previewContent" 
            :readonly="true" 
            :showToolbar="false"
            :fontFamily="fontFamily"
            :fontSize="fontSize"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, defineProps } from 'vue'
import { useBookStore } from '@/stores/book'
import { storeToRefs } from 'pinia'
import { apiService } from '../services/api' // For preview
import MarkdownEditor from './MarkdownEditor.vue'

const props = defineProps<{
  chunkId: string
  fontFamily?: string
  fontSize?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'restored', chunkId: string): void
}>()

const bookStore = useBookStore()
const { versions, isVersionsLoading, versionsError } = storeToRefs(bookStore)

// Local state for UI
const selectedVersion = ref<number | null>(null)
const previewContent = ref('')
const isPreviewLoading = ref(false)
const isRestoring = ref(false)

const loadVersions = () => {
  bookStore.fetchVersions(props.chunkId)
}

const viewVersion = async (version: number) => {
  if (selectedVersion.value === version) {
    selectedVersion.value = null
    previewContent.value = ''
    return
  }
  
  selectedVersion.value = version
  isPreviewLoading.value = true
  
  try {
    const versionData = await apiService.getChunkVersion(props.chunkId, version)
    previewContent.value = versionData.text || ''
  } catch (err: any) {
    console.error('Failed to load version preview:', err)
    selectedVersion.value = null
  } finally {
    isPreviewLoading.value = false
  }
}

const restoreVersion = async (version: number) => {
  if (confirm(`Are you sure you want to restore to version ${version}? This will create a new version.`)) {
    isRestoring.value = true
    selectedVersion.value = version
    
    try {
      await bookStore.restoreChunkVersion(props.chunkId, version)
      emit('restored', props.chunkId)
    } catch (err: any) {
      // Error is handled in the store, but you might want to show a notification here
      console.error('Failed to restore version:', err)
    } finally {
      isRestoring.value = false
    }
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric', 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit', 
    minute: '2-digit'
  }).format(date)
}

watch(() => props.chunkId, (newChunkId) => {
  if (newChunkId) {
    loadVersions()
  }
}, { immediate: true })
</script>

<style scoped>
.version-history {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  padding: 1.5rem;
  position: relative;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 1rem;
}

.header h3 {
  margin: 0;
  color: #111827;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  color: #6b7280;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  transition: color 0.2s;
}

.close-button:hover {
  color: #111827;
}

.loading, .error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
}

.spinner {
  width: 2rem;
  height: 2rem;
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

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.versions-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.version-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  background-color: #f9fafb;
  transition: all 0.2s;
}

.version-item:hover {
  border-color: #d1d5db;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.version-item.is-current {
  border-color: #8b5cf6;
  background-color: #f5f3ff;
}

.version-info {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.version-number {
  flex-shrink: 0;
}

.badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  background-color: #e5e7eb;
  color: #4b5563;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.current-badge {
  background-color: #8b5cf6;
  color: white;
}

.version-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.timestamp {
  font-size: 0.875rem;
  color: #374151;
  font-weight: 500;
}

.word-count {
  font-size: 0.75rem;
  color: #6b7280;
}

.version-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.view-button, .restore-button {
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.view-button {
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.view-button:hover {
  background-color: #e5e7eb;
}

.view-button.active {
  background-color: #6366f1;
  color: white;
  border-color: #6366f1;
}

.restore-button {
  background-color: #4f46e5;
  color: white;
  border: none;
}

.restore-button:hover {
  background-color: #4338ca;
}

.restoring-indicator {
  color: #4f46e5;
  font-size: 0.875rem;
  font-weight: 500;
}

.version-preview {
  margin-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
  padding-top: 1.5rem;
}

.version-preview h4 {
  margin: 0 0 1rem 0;
  color: #111827;
  font-size: 1rem;
  font-weight: 600;
}

.preview-content {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
}

.loading-preview {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
}

.retry-button {
  background-color: #6366f1;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  margin-top: 1rem;
}
</style>
