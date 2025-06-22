<template>
  <div class="book-export">
    <div class="export-header">
      <h3>📤 Export Your Book</h3>
      <p>Choose from various export formats to share or publish your book.</p>
    </div>

    <div class="export-options">
      <!-- Format Selection -->
      <div class="export-section">
        <h4>Export Format</h4>
        <div class="format-grid">
          <div 
            v-for="format in exportFormats" 
            :key="format.id"
            @click="selectedFormat = format.id"
            :class="['format-card', { selected: selectedFormat === format.id }]"
          >
            <div class="format-icon">{{ format.icon }}</div>
            <div class="format-info">
              <h5>{{ format.name }}</h5>
              <p>{{ format.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Content Options -->
      <div class="export-section">
        <h4>Content Options</h4>
        <div class="content-options">
          <label class="option-item">
            <input 
              type="checkbox" 
              v-model="includeMetadata"
            />
            <span>Include book metadata (title, description, etc.)</span>
          </label>
          
          <label class="option-item">
            <input 
              type="checkbox" 
              v-model="includeChapterHeadings"
            />
            <span>Include chapter headings</span>
          </label>
          
          <label class="option-item">
            <input 
              type="checkbox" 
              v-model="includeSceneTitles"
            />
            <span>Include scene titles</span>
          </label>
          
          <label class="option-item">
            <input 
              type="checkbox" 
              v-model="includeEmptyChunks"
            />
            <span>Include empty or incomplete chunks</span>
          </label>
        </div>
      </div>

      <!-- Chapter Selection -->
      <div class="export-section">
        <h4>Chapter Selection</h4>
        <div class="chapter-options">
          <label class="option-item">
            <input 
              type="radio" 
              name="chapterSelection"
              value="all"
              v-model="chapterSelection"
            />
            <span>Export all chapters</span>
          </label>
          
          <label class="option-item">
            <input 
              type="radio" 
              name="chapterSelection"
              value="range"
              v-model="chapterSelection"
            />
            <span>Export chapter range</span>
          </label>
          
          <div v-if="chapterSelection === 'range'" class="chapter-range">
            <div class="range-inputs">
              <label>
                From Chapter:
                <select v-model="chapterRangeStart">
                  <option v-for="chapterNum in availableChapters" :key="chapterNum" :value="chapterNum">
                    {{ chapterNum === 0 ? 'Introduction' : `Chapter ${chapterNum}` }}
                  </option>
                </select>
              </label>
              
              <label>
                To Chapter:
                <select v-model="chapterRangeEnd">
                  <option v-for="chapterNum in availableChapters" :key="chapterNum" :value="chapterNum">
                    {{ chapterNum === 0 ? 'Introduction' : `Chapter ${chapterNum}` }}
                  </option>
                </select>
              </label>
            </div>
          </div>
          
          <label class="option-item">
            <input 
              type="radio" 
              name="chapterSelection"
              value="specific"
              v-model="chapterSelection"
            />
            <span>Export specific chapters</span>
          </label>
          
          <div v-if="chapterSelection === 'specific'" class="specific-chapters">
            <div class="chapter-checkboxes">
              <label v-for="chapterNum in availableChapters" :key="chapterNum" class="chapter-checkbox">
                <input 
                  type="checkbox" 
                  :value="chapterNum"
                  v-model="selectedChapters"
                />
                <span>{{ chapterNum === 0 ? 'Introduction' : `Chapter ${chapterNum}` }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Preview Section -->
      <div class="export-section">
        <h4>Export Preview</h4>
        <div class="preview-info">
          <div class="preview-stats">
            <div class="stat">
              <span class="stat-label">Chunks to export:</span>
              <span class="stat-value">{{ exportStats.chunkCount }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Total words:</span>
              <span class="stat-value">{{ exportStats.wordCount.toLocaleString() }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Estimated pages:</span>
              <span class="stat-value">{{ exportStats.estimatedPages }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">File size:</span>
              <span class="stat-value">{{ exportStats.estimatedSize }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Export Actions -->
      <div class="export-actions">
        <button 
          @click="previewExport"
          :disabled="!canExport"
          class="preview-btn"
        >
          Preview Export
        </button>
        
        <button 
          @click="exportBook"
          :disabled="!canExport || isExporting"
          :class="['export-btn', { exporting: isExporting }]"
        >
          {{ isExporting ? 'Exporting...' : `Export as ${selectedFormatName}` }}
        </button>
      </div>
    </div>

    <!-- Export Preview Modal -->
    <div v-if="showPreview" class="modal-overlay" @click="showPreview = false">
      <div class="preview-modal" @click.stop>
        <div class="modal-header">
          <h3>Export Preview</h3>
          <button @click="showPreview = false" class="close-btn">×</button>
        </div>
        
        <div class="modal-content">
          <div class="preview-content" v-html="exportPreviewContent"></div>
        </div>
        
        <div class="modal-actions">
          <button @click="showPreview = false" class="cancel-btn">Close</button>
          <button @click="exportFromPreview" :disabled="isExporting" class="export-btn">
            {{ isExporting ? 'Exporting...' : 'Export' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Chunk } from '../stores/types'

interface Props {
  chunks: Chunk[]
  book?: any
}

const props = defineProps<Props>()

// Export settings
const selectedFormat = ref('html')
const includeMetadata = ref(true)
const includeChapterHeadings = ref(true)
const includeSceneTitles = ref(false)
const includeEmptyChunks = ref(false)
const chapterSelection = ref<'all' | 'range' | 'specific'>('all')
const chapterRangeStart = ref(0)
const chapterRangeEnd = ref(0)
const selectedChapters = ref<number[]>([])
const isExporting = ref(false)
const showPreview = ref(false)
const exportPreviewContent = ref('')

// Export formats
const exportFormats = [
  {
    id: 'html',
    name: 'HTML',
    icon: '🌐',
    description: 'Web-friendly format, great for sharing online'
  },
  {
    id: 'scene',
    name: 'Markdown',
    icon: '📝',
    description: 'Plain text with formatting, perfect for editing'
  },
  {
    id: 'txt',
    name: 'Plain Text',
    icon: '📄',
    description: 'Simple text format, universally compatible'
  },
  {
    id: 'pdf',
    name: 'PDF',
    icon: '📕',
    description: 'Print-ready format (coming soon)'
  },
  {
    id: 'epub',
    name: 'EPUB',
    icon: '📚',
    description: 'E-book format for reading devices (coming soon)'
  }
]

// Computed properties
const availableChapters = computed(() => {
  const chapters = new Set<number>()
  props.chunks.forEach(chunk => {
    if (!chunk.is_deleted) {
      chapters.add(chunk.props?.chapter || 0)
    }
  })
  return Array.from(chapters).sort((a, b) => a - b)
})

const selectedFormatName = computed(() => {
  const format = exportFormats.find(f => f.id === selectedFormat.value)
  return format?.name || 'Unknown'
})

const chunksToExport = computed(() => {
  let chunks = props.chunks.filter(chunk => 
    !chunk.is_deleted && 
    (includeEmptyChunks.value || (chunk.text && chunk.text.trim().length > 0))
  )
  
  // Filter by chapter selection
  if (chapterSelection.value === 'range') {
    const start = Math.min(chapterRangeStart.value, chapterRangeEnd.value)
    const end = Math.max(chapterRangeStart.value, chapterRangeEnd.value)
    chunks = chunks.filter(chunk => {
      const chapterNum = chunk.props?.chapter || 0
      return chapterNum >= start && chapterNum <= end
    })
  } else if (chapterSelection.value === 'specific') {
    chunks = chunks.filter(chunk => 
      selectedChapters.value.includes(chunk.props?.chapter || 0)
    )
  }
  
  return chunks.sort((a, b) => {
    if (a.props?.chapter !== b.props?.chapter) {
      return (a.props?.chapter || 0) - (b.props?.chapter || 0)
    }
    return (a.props?.order || 0) - (b.props?.order || 0)
  })
})

const exportStats = computed(() => {
  const chunks = chunksToExport.value
  const wordCount = chunks.reduce((total, chunk) => total + (chunk.word_count || 0), 0)
  const estimatedPages = Math.ceil(wordCount / 250) // Assuming 250 words per page
  const estimatedSizeKB = Math.ceil(wordCount * 6 / 1024) // Rough estimate
  
  return {
    chunkCount: chunks.length,
    wordCount,
    estimatedPages,
    estimatedSize: estimatedSizeKB < 1024 ? `${estimatedSizeKB} KB` : `${(estimatedSizeKB / 1024).toFixed(1)} MB`
  }
})

const canExport = computed(() => {
  return chunksToExport.value.length > 0 && 
         (selectedFormat.value === 'html' || selectedFormat.value === 'scene' || selectedFormat.value === 'txt')
})

// Methods
function previewExport() {
  exportPreviewContent.value = generateExportContent()
  showPreview.value = true
}

function generateExportContent(): string {
  const chunks = chunksToExport.value
  let content = ''
  
  // Add metadata if requested
  if (includeMetadata.value && props.book) {
    if (selectedFormat.value === 'html') {
      content += `<div class="book-metadata">
        <h1>${props.book.props?.name || 'Untitled Book'}</h1>
        ${props.book.props?.description ? `<p class="description">${props.book.props.description}</p>` : ''}
      </div>\n\n`
    } else if (selectedFormat.value === 'scene') {
      content += `# ${props.book.props?.name || 'Untitled Book'}\n\n`
      if (props.book.props?.description) {
        content += `${props.book.props.description}\n\n`
      }
    } else {
      content += `${props.book.props?.name || 'Untitled Book'}\n`
      if (props.book.props?.description) {
        content += `${props.book.props.description}\n\n`
      }
    }
  }
  
  // Group chunks by chapter
  const chapterGroups = new Map<number, Chunk[]>()
  chunks.forEach(chunk => {
    const chapterNum = chunk.props?.chapter || 0
    if (!chapterGroups.has(chapterNum)) {
      chapterGroups.set(chapterNum, [])
    }
    chapterGroups.get(chapterNum)!.push(chunk)
  })
  
  // Generate content for each chapter
  Array.from(chapterGroups.entries()).sort(([a], [b]) => a - b).forEach(([chapterNum, chapterChunks]) => {
    // Add chapter heading if requested
    if (includeChapterHeadings.value && chapterNum > 0) {
      if (selectedFormat.value === 'html') {
        content += `<h2>Chapter ${chapterNum}</h2>\n\n`
      } else if (selectedFormat.value === 'scene') {
        content += `## Chapter ${chapterNum}\n\n`
      } else {
        content += `Chapter ${chapterNum}\n${'='.repeat(20)}\n\n`
      }
    }
    
    // Add chunk content
    chapterChunks.forEach(chunk => {
      // Add scene title if requested
      if (includeSceneTitles.value && chunk.props?.scene_title) {
        if (selectedFormat.value === 'html') {
          content += `<h3>${chunk.props.scene_title}</h3>\n`
        } else if (selectedFormat.value === 'scene') {
          content += `### ${chunk.props.scene_title}\n\n`
        } else {
          content += `${chunk.props.scene_title}\n${'-'.repeat(chunk.props.scene_title.length)}\n\n`
        }
      }
      
      // Add chunk text
      if (chunk.text && chunk.text.trim()) {
        if (selectedFormat.value === 'html') {
          const formattedText = chunk.text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
          content += `<p>${formattedText}</p>\n\n`
        } else {
          content += `${chunk.text}\n\n`
        }
      }
    })
  })
  
  return content
}

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function exportBook() {
  if (!canExport.value) return
  
  isExporting.value = true
  
  try {
    const content = generateExportContent()
    const bookName = props.book?.props?.name || 'Untitled Book'
    const sanitizedName = bookName.replace(/[^a-zA-Z0-9\s-]/g, '').replace(/\s+/g, '_')
    
    let filename: string
    let mimeType: string
    
    switch (selectedFormat.value) {
      case 'html':
        filename = `${sanitizedName}.html`
        mimeType = 'text/html'
        break
      case 'scene':
        filename = `${sanitizedName}.md`
        mimeType = 'text/markdown'
        break
      case 'txt':
        filename = `${sanitizedName}.txt`
        mimeType = 'text/plain'
        break
      default:
        throw new Error('Unsupported format')
    }
    
    downloadFile(content, filename, mimeType)
    
  } catch (error) {
    console.error('Export failed:', error)
    alert('Export failed. Please try again.')
  } finally {
    isExporting.value = false
  }
}

function exportFromPreview() {
  showPreview.value = false
  exportBook()
}

// Initialize chapter range
if (availableChapters.value.length > 0) {
  chapterRangeStart.value = availableChapters.value[0]
  chapterRangeEnd.value = availableChapters.value[availableChapters.value.length - 1]
}
</script>

<style scoped>
.book-export {
  padding: 1.5rem;
}

.export-header {
  text-align: center;
  margin-bottom: 2rem;
}

.export-header h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  color: #1f2937;
}

.export-header p {
  margin: 0;
  color: #6b7280;
}

.export-options {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.export-section {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.export-section h4 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.format-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.format-card {
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.format-card:hover {
  border-color: #6366f1;
  background: #f8fafc;
}

.format-card.selected {
  border-color: #6366f1;
  background: #eff6ff;
}

.format-icon {
  font-size: 2rem;
  text-align: center;
  margin-bottom: 0.5rem;
}

.format-info h5 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  font-weight: 600;
  text-align: center;
}

.format-info p {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
  text-align: center;
}

.content-options,
.chapter-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.option-item input {
  margin: 0;
}

.chapter-range,
.specific-chapters {
  margin-left: 1.5rem;
  margin-top: 0.5rem;
}

.range-inputs {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.range-inputs label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
}

.range-inputs select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
}

.chapter-checkboxes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.5rem;
}

.chapter-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  cursor: pointer;
}

.preview-info {
  background: #f9fafb;
  border-radius: 6px;
  padding: 1rem;
}

.preview-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat {
  display: flex;
  flex-direction: column;
  text-align: center;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.export-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.preview-btn,
.export-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.preview-btn {
  background: #f3f4f6;
  color: #374151;
}

.preview-btn:hover:not(:disabled) {
  background: #e5e7eb;
}

.export-btn {
  background: #6366f1;
  color: white;
}

.export-btn:hover:not(:disabled) {
  background: #4f46e5;
  transform: translateY(-1px);
}

.export-btn:disabled,
.preview-btn:disabled {
  background: #9ca3af;
  color: #6b7280;
  cursor: not-allowed;
  transform: none;
}

.export-btn.exporting {
  background: #6b7280;
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
  padding: 2rem;
}

.preview-modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.preview-content {
  font-family: Georgia, serif;
  line-height: 1.6;
  color: #374151;
}

.preview-content :deep(h1) {
  font-size: 2rem;
  margin: 0 0 1rem 0;
}

.preview-content :deep(h2) {
  font-size: 1.5rem;
  margin: 2rem 0 1rem 0;
}

.preview-content :deep(h3) {
  font-size: 1.25rem;
  margin: 1.5rem 0 0.5rem 0;
}

.preview-content :deep(p) {
  margin: 0 0 1rem 0;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.cancel-btn {
  background: #f3f4f6;
  color: #374151;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
}

/* Responsive Design */
@media (max-width: 768px) {
  .book-export {
    padding: 1rem;
  }
  
  .format-grid {
    grid-template-columns: 1fr;
  }
  
  .range-inputs {
    flex-direction: column;
    align-items: stretch;
  }
  
  .preview-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .export-actions {
    flex-direction: column;
  }
  
  .modal-overlay {
    padding: 1rem;
  }
}
</style>
