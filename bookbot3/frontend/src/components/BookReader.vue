<template>
  <div class="book-reader">
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      Loading book content...
    </div>
    
    <div v-else-if="!chunks.length" class="empty-state">
      <h3>📖 No Content to Read</h3>
      <p>This book doesn't have any readable content yet.</p>
    </div>

    <div v-else class="reader-content">
      <!-- Reader Controls -->
      <div class="reader-controls">
        <div class="view-options">
          <button 
            @click="viewMode = 'chapters'"
            :class="['view-btn', { active: viewMode === 'chapters' }]"
          >
            By Chapter
          </button>
          <button 
            @click="viewMode = 'continuous'"
            :class="['view-btn', { active: viewMode === 'continuous' }]"
          >
            Continuous
          </button>
        </div>
        
        <div class="text-controls">
          <label class="font-size-control">
            Font Size:
            <select v-model="fontSize">
              <option value="small">Small</option>
              <option value="medium">Medium</option>
              <option value="large">Large</option>
              <option value="extra-large">Extra Large</option>
            </select>
          </label>
          
          <label class="font-family-control">
            Font:
            <select v-model="fontFamily">
              <option value="serif">Serif</option>
              <option value="sans-serif">Sans Serif</option>
              <option value="monospace">Monospace</option>
            </select>
          </label>
        </div>
      </div>

      <!-- Chapter Navigation (when in chapter view) -->
      <div v-if="viewMode === 'chapters'" class="chapter-navigation">
        <div class="chapter-selector">
          <button 
            v-for="chapterNum in availableChapters" 
            :key="chapterNum"
            @click="selectedChapter = chapterNum"
            :class="['chapter-btn', { active: selectedChapter === chapterNum }]"
          >
            {{ chapterNum === 0 ? 'Intro' : `Chapter ${chapterNum}` }}
          </button>
        </div>
      </div>

      <!-- Reading Area -->
      <div 
        class="reading-area" 
        :class="[`font-${fontSize}`, `font-${fontFamily}`]"
      >
        <!-- Chapter View -->
        <div v-if="viewMode === 'chapters'" class="chapter-view">
          <div v-for="chunk in currentChapterChunks" :key="chunk.chunk_id" class="chunk-section">
            <!-- Chunk Header (optional, can be hidden for cleaner reading) -->
            <div v-if="showChunkHeaders" class="chunk-header">
              <span class="chunk-type">{{ formatChunkType(chunk.type) }}</span>
              <span v-if="chunk.props?.scene_title" class="scene-title">
                {{ chunk.props.scene_title }}
              </span>
            </div>
            
            <!-- Chunk Content -->
            <div 
              class="chunk-content" 
              v-html="formatChunkText(chunk.text || '')"
            ></div>
          </div>
          
          <!-- Chapter Navigation -->
          <div class="chapter-nav-controls">
            <button 
              @click="previousChapter" 
              :disabled="!canGoPreviousChapter"
              class="nav-btn prev-btn"
            >
              ← Previous Chapter
            </button>
            <button 
              @click="nextChapter" 
              :disabled="!canGoNextChapter"
              class="nav-btn next-btn"
            >
              Next Chapter →
            </button>
          </div>
        </div>

        <!-- Continuous View -->
        <div v-else class="continuous-view">
          <div v-for="chapter in organizedChunks" :key="chapter.chapterNumber" class="chapter-section">
            <!-- Chapter Heading -->
            <h2 v-if="chapter.chapterNumber > 0" class="chapter-heading">
              Chapter {{ chapter.chapterNumber }}
            </h2>
            <h2 v-else class="chapter-heading">Introduction</h2>
            
            <!-- Chapter Chunks -->
            <div v-for="chunk in chapter.chunks" :key="chunk.chunk_id" class="chunk-section">
              <div v-if="showChunkHeaders" class="chunk-header">
                <span class="chunk-type">{{ formatChunkType(chunk.type) }}</span>
                <span v-if="chunk.props?.scene_title" class="scene-title">
                  {{ chunk.props.scene_title }}
                </span>
              </div>
              
              <div 
                class="chunk-content" 
                v-html="formatChunkText(chunk.text || '')"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Reading Progress -->
      <div class="reading-progress">
        <div class="progress-info">
          <span>{{ readingProgressText }}</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${readingProgress}%` }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { Chunk } from '../stores/book'

interface Props {
  chunks: Chunk[]
  loading: boolean
}

const props = defineProps<Props>()

// Reading settings
const viewMode = ref<'chapters' | 'continuous'>('continuous')
const fontSize = ref<'small' | 'medium' | 'large' | 'extra-large'>('medium')
const fontFamily = ref<'serif' | 'sans-serif' | 'monospace'>('serif')
const showChunkHeaders = ref(false)
const selectedChapter = ref(0)

// Computed properties
const readableChunks = computed(() => {
  return props.chunks.filter(chunk => 
    chunk.text && 
    chunk.text.trim().length > 0 && 
    !chunk.is_deleted &&
    (chunk.type === 'scene' || chunk.type === 'chapter' || chunk.type === 'outline')
  ).sort((a, b) => {
    // Sort by chapter first, then by order
    if (a.chapter !== b.chapter) {
      return (a.chapter || 0) - (b.chapter || 0)
    }
    return (a.order || 0) - (b.order || 0)
  })
})

const organizedChunks = computed(() => {
  const chapters = new Map<number, { chapterNumber: number; chunks: Chunk[] }>()
  
  readableChunks.value.forEach(chunk => {
    const chapterNum = chunk.chapter || 0
    if (!chapters.has(chapterNum)) {
      chapters.set(chapterNum, { chapterNumber: chapterNum, chunks: [] })
    }
    chapters.get(chapterNum)!.chunks.push(chunk)
  })
  
  return Array.from(chapters.values()).sort((a, b) => a.chapterNumber - b.chapterNumber)
})

const availableChapters = computed(() => {
  return organizedChunks.value.map(chapter => chapter.chapterNumber)
})

const currentChapterChunks = computed(() => {
  const chapter = organizedChunks.value.find(ch => ch.chapterNumber === selectedChapter.value)
  return chapter ? chapter.chunks : []
})

const canGoPreviousChapter = computed(() => {
  const currentIndex = availableChapters.value.indexOf(selectedChapter.value)
  return currentIndex > 0
})

const canGoNextChapter = computed(() => {
  const currentIndex = availableChapters.value.indexOf(selectedChapter.value)
  return currentIndex < availableChapters.value.length - 1
})

const totalWords = computed(() => {
  return readableChunks.value.reduce((total, chunk) => total + (chunk.word_count || 0), 0)
})

const currentWords = computed(() => {
  if (viewMode.value === 'continuous') {
    return totalWords.value
  } else {
    return currentChapterChunks.value.reduce((total, chunk) => total + (chunk.word_count || 0), 0)
  }
})

const readingProgress = computed(() => {
  if (viewMode.value === 'continuous') {
    return 100 // Always 100% in continuous mode
  } else {
    const currentIndex = availableChapters.value.indexOf(selectedChapter.value)
    return availableChapters.value.length > 0 ? ((currentIndex + 1) / availableChapters.value.length) * 100 : 0
  }
})

const readingProgressText = computed(() => {
  if (viewMode.value === 'continuous') {
    return `${readableChunks.value.length} chunks • ${totalWords.value.toLocaleString()} words`
  } else {
    const currentIndex = availableChapters.value.indexOf(selectedChapter.value)
    return `Chapter ${currentIndex + 1} of ${availableChapters.value.length} • ${currentWords.value.toLocaleString()} words`
  }
})

// Methods
function formatChunkType(type: string): string {
  return type.charAt(0).toUpperCase() + type.slice(1)
}

function formatChunkText(text: string): string {
  if (!text) return ''
  
  // Convert markdown-like formatting to HTML
  let formatted = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
    .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
    .replace(/\n\n/g, '</p><p>') // Paragraphs
    .replace(/\n/g, '<br>') // Line breaks
  
  // Wrap in paragraph tags if not already wrapped
  if (!formatted.startsWith('<p>')) {
    formatted = '<p>' + formatted + '</p>'
  }
  
  return formatted
}

function previousChapter() {
  const currentIndex = availableChapters.value.indexOf(selectedChapter.value)
  if (currentIndex > 0) {
    selectedChapter.value = availableChapters.value[currentIndex - 1]
  }
}

function nextChapter() {
  const currentIndex = availableChapters.value.indexOf(selectedChapter.value)
  if (currentIndex < availableChapters.value.length - 1) {
    selectedChapter.value = availableChapters.value[currentIndex + 1]
  }
}

// Lifecycle
onMounted(() => {
  // Set initial chapter to the first available chapter
  if (availableChapters.value.length > 0) {
    selectedChapter.value = availableChapters.value[0]
  }
})

// Watch for chunks changes and update selected chapter if needed
watch(() => props.chunks, () => {
  if (availableChapters.value.length > 0 && !availableChapters.value.includes(selectedChapter.value)) {
    selectedChapter.value = availableChapters.value[0]
  }
})

// Keyboard navigation
onMounted(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (viewMode.value === 'chapters') {
      if (e.key === 'ArrowLeft' && canGoPreviousChapter.value) {
        previousChapter()
      } else if (e.key === 'ArrowRight' && canGoNextChapter.value) {
        nextChapter()
      }
    }
  }
  
  document.addEventListener('keydown', handleKeyDown)
  
  // Cleanup on unmount
  return () => {
    document.removeEventListener('keydown', handleKeyDown)
  }
})
</script>

<style scoped>
.book-reader {
  min-height: 400px;
}

.loading-state, .empty-state {
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

.reader-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.reader-controls {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.view-options {
  display: flex;
  gap: 0.5rem;
}

.view-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.view-btn:hover {
  background: #f9fafb;
}

.view-btn.active {
  background: #6366f1;
  color: white;
  border-color: #6366f1;
}

.text-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.font-size-control, .font-family-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #374151;
}

.font-size-control select, .font-family-control select {
  padding: 0.25rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
}

.chapter-navigation {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chapter-selector {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.chapter-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
}

.chapter-btn:hover {
  background: #f9fafb;
}

.chapter-btn.active {
  background: #6366f1;
  color: white;
  border-color: #6366f1;
}

.reading-area {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  line-height: 1.6;
  max-width: none;
}

/* Font sizes */
.font-small {
  font-size: 14px;
}

.font-medium {
  font-size: 16px;
}

.font-large {
  font-size: 18px;
}

.font-extra-large {
  font-size: 20px;
}

/* Font families */
.font-serif {
  font-family: Georgia, 'Times New Roman', serif;
}

.font-sans-serif {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.font-monospace {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.chapter-section {
  margin-bottom: 3rem;
}

.chapter-heading {
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 2rem 0;
  color: #1f2937;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 0.5rem;
}

.chunk-section {
  margin-bottom: 2rem;
}

.chunk-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.875rem;
  color: #6b7280;
}

.chunk-type {
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.scene-title {
  font-style: italic;
}

.chunk-content {
  color: #374151;
  line-height: inherit;
}

.chunk-content :deep(p) {
  margin: 0 0 1rem 0;
}

.chunk-content :deep(p:last-child) {
  margin-bottom: 0;
}

.chunk-content :deep(strong) {
  font-weight: 600;
}

.chunk-content :deep(em) {
  font-style: italic;
}

.chapter-nav-controls {
  display: flex;
  justify-content: space-between;
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid #e5e7eb;
}

.nav-btn {
  padding: 0.75rem 1.5rem;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.nav-btn:hover:not(:disabled) {
  background: #4f46e5;
  transform: translateY(-1px);
}

.nav-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
}

.reading-progress {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.progress-info {
  display: flex;
  justify-content: center;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.progress-bar {
  height: 4px;
  background: #f3f4f6;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #6366f1;
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* Responsive Design */
@media (max-width: 768px) {
  .reader-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .text-controls {
    justify-content: center;
  }
  
  .chapter-selector {
    justify-content: center;
  }
  
  .reading-area {
    padding: 1.5rem;
  }
  
  .chapter-nav-controls {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>
