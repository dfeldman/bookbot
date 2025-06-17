<template>
  <div class="book-index">
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      Loading book contents...
    </div>
    
    <div v-else-if="!chunks || chunks.length === 0" class="empty-state">
      <h3>📄 No Content Yet</h3>
      <p>This book doesn't have any chunks yet. Start by creating a foundation or adding content.</p>
    </div>

    <div v-else class="book-content">
      <!-- Foundation Section -->
      <div v-if="foundationChunks.length > 0" class="foundation-section">
        <div class="section-header">
          <h2 class="section-title">📋 Foundation</h2>
          <div class="section-stats">
            {{ foundationChunks.length }} foundation chunk{{ foundationChunks.length !== 1 ? 's' : '' }}
          </div>
        </div>

        <div class="foundation-grid">
          <div 
            v-for="chunk in foundationChunks" 
            :key="chunk.chunk_id"
            :class="['foundation-chunk', { locked: chunk.is_locked }]"
            @click="!chunk.is_locked && $emit('edit-chunk', chunk.chunk_id)"
          >
            <div class="chunk-icon">{{ getFoundationIcon(chunk.type) }}</div>
            <div class="chunk-info">
              <div class="chunk-name">{{ formatChunkType(chunk.type) }}</div>
              <div class="chunk-meta">
                {{ chunk.word_count || 0 }} words
                <span v-if="chunk.props?.name"> · {{ chunk.props.name }}</span>
              </div>
            </div>
            <div class="chunk-actions">
              <div v-if="chunk.is_locked" class="chunk-spinner"></div>
              <button 
                v-else
                @click.stop="$emit('edit-chunk', chunk.chunk_id)"
                class="edit-button"
                title="Edit chunk"
              >
                ✏️
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Chapters Section -->
      <div v-if="chapterScenes.length > 0" class="chapters-section">
        <div 
          v-for="chapter in chapterScenes" 
          :key="chapter.chapterNumber"
          class="chapter-group"
        >
          <div class="chapter-header">
            <h2 class="chapter-title">
              📖 Chapter {{ chapter.chapterNumber }}
            </h2>
            <div class="chapter-stats">
              {{ chapter.scenes.length }} scene{{ chapter.scenes.length !== 1 ? 's' : '' }} · 
              {{ chapter.totalWords }} words
            </div>
          </div>

          <div class="scenes-list">
            <div 
              v-for="(scene, index) in chapter.scenes" 
              :key="scene.chunk_id"
              :class="['scene-row', { locked: scene.is_locked }]"
              @click="!scene.is_locked && $emit('edit-chunk', scene.chunk_id)"
            >
              <!-- Drag Handle -->
              <div class="drag-handle" title="Drag to reorder">
                ⋮⋮
              </div>
              
              <!-- Scene Content -->
              <div class="scene-content">
                <div class="scene-name">
                  {{ getSceneName(scene, index) }}
                </div>
                <div class="scene-properties">
                  <span class="scene-order">Order: {{ scene.order }}</span>
                  <span class="scene-words">{{ scene.word_count || 0 }} words</span>
                  <span v-if="scene.props?.scene_title" class="scene-title">
                    {{ scene.props.scene_title }}
                  </span>
                  <span v-if="scene.props?.tags?.length" class="scene-tags">
                    Tags: {{ scene.props.tags.join(', ') }}
                  </span>
                </div>
              </div>

              <!-- Status & Actions -->
              <div class="scene-actions">
                <div v-if="scene.is_locked" class="scene-spinner" title="Processing..."></div>
                <button 
                  v-else
                  @click.stop="$emit('edit-chunk', scene.chunk_id)"
                  class="edit-button"
                  title="Edit scene"
                >
                  ✏️
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty Scenes State -->
      <div v-if="foundationChunks.length > 0 && chapterScenes.length === 0" class="empty-scenes">
        <h3>📝 Ready for Scenes</h3>
        <p>Foundation is set up. Start adding scenes to build your story!</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Chunk {
  chunk_id: string
  type: string
  chapter: number | null
  order: number
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

interface ChapterScenes {
  chapterNumber: number
  scenes: Chunk[]
  totalWords: number
}

interface Props {
  book: any
  chunks: Chunk[]
  loading: boolean
}

const props = defineProps<Props>()

defineEmits<{
  'edit-chunk': [chunkId: string]
  'reorder-chunks': [fromIndex: number, toIndex: number]
}>()

// Foundation chunk types (usually chapter 0 or null)
const FOUNDATION_TYPES = ['brief', 'outline', 'style', 'settings', 'characters']

const foundationChunks = computed((): Chunk[] => {
  if (!props.chunks) return []
  
  return props.chunks
    .filter(chunk => FOUNDATION_TYPES.includes(chunk.type))
    .sort((a, b) => {
      // Sort by predefined order, then by created_at
      const typeOrder = FOUNDATION_TYPES.indexOf(a.type) - FOUNDATION_TYPES.indexOf(b.type)
      if (typeOrder !== 0) return typeOrder
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    })
})

const chapterScenes = computed((): ChapterScenes[] => {
  if (!props.chunks) return []
  
  // Get only scene chunks with valid chapters (1 or higher)
  const sceneChunks = props.chunks
    .filter(chunk => chunk.type === 'scene' && chunk.chapter && chunk.chapter >= 1)
  
  if (sceneChunks.length === 0) return []
  
  // Group scenes by chapter
  const chapterMap = new Map<number, Chunk[]>()
  
  sceneChunks.forEach(scene => {
    const chapterNum = scene.chapter!
    if (!chapterMap.has(chapterNum)) {
      chapterMap.set(chapterNum, [])
    }
    chapterMap.get(chapterNum)!.push(scene)
  })

  // Convert to sorted array
  const chapters: ChapterScenes[] = []
  const sortedChapterNumbers = Array.from(chapterMap.keys()).sort((a, b) => a - b)

  sortedChapterNumbers.forEach(chapterNum => {
    const scenes = chapterMap.get(chapterNum)!
    // Sort scenes within chapter by order, then by created_at
    scenes.sort((a, b) => {
      if (a.order !== b.order) return a.order - b.order
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    })

    chapters.push({
      chapterNumber: chapterNum,
      scenes,
      totalWords: scenes.reduce((sum, scene) => sum + (scene.word_count || 0), 0)
    })
  })

  return chapters
})

function getFoundationIcon(type: string): string {
  const icons = {
    brief: '📝',
    outline: '📋',
    style: '🎨',
    settings: '⚙️',
    characters: '👥'
  }
  return icons[type as keyof typeof icons] || '📄'
}

function getSceneName(scene: Chunk, index: number): string {
  if (scene.props?.name) {
    return scene.props.name
  }
  if (scene.props?.scene_title) {
    return scene.props.scene_title
  }
  return `Scene ${index + 1}`
}

function formatChunkType(type: string): string {
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
</script>

<style scoped>
.book-index {
  min-height: 500px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: #64748b;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #f3f4f6;
  border-top: 2px solid #6366f1;
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
  padding: 4rem 2rem;
  background: white;
  border-radius: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.empty-state h3 {
  font-size: 1.5rem;
  color: #1e293b;
  margin-bottom: 1rem;
}

.empty-state p {
  color: #64748b;
}

.empty-scenes {
  text-align: center;
  padding: 3rem 2rem;
  background: #f8fafc;
  border-radius: 1rem;
  margin-top: 2rem;
}

.empty-scenes h3 {
  font-size: 1.25rem;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.empty-scenes p {
  color: #64748b;
  margin: 0;
}

.book-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Foundation Section */
.foundation-section {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.section-header {
  background: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.section-stats {
  color: #64748b;
  font-size: 0.875rem;
}

.foundation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  padding: 1.5rem 2rem;
}

.foundation-chunk {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.foundation-chunk:hover:not(.locked) {
  border-color: #6366f1;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
  transform: translateY(-2px);
}

.foundation-chunk.locked {
  opacity: 0.6;
  cursor: not-allowed;
  background: #f8fafc;
}

.chunk-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.chunk-info {
  flex: 1;
  min-width: 0;
}

.chunk-name {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.chunk-meta {
  font-size: 0.875rem;
  color: #64748b;
}

.chunk-actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.chunk-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #f3f4f6;
  border-top: 2px solid #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.edit-button {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  border-radius: 0.375rem;
  transition: background-color 0.2s;
  font-size: 1rem;
}

.edit-button:hover {
  background: #f1f5f9;
}

/* Chapters Section */
.chapters-section {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.chapter-group {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chapter-header {
  background: #fafafa;
  border-bottom: 1px solid #e2e8f0;
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chapter-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.chapter-stats {
  color: #64748b;
  font-size: 0.875rem;
}

.scenes-list {
  padding: 1rem 2rem 1.5rem;
}

.scene-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  margin-bottom: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.scene-row:last-child {
  margin-bottom: 0;
}

.scene-row:hover:not(.locked) {
  border-color: #6366f1;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
  transform: translateY(-2px);
}

.scene-row.locked {
  opacity: 0.6;
  cursor: not-allowed;
  background: #f8fafc;
}

.drag-handle {
  color: #94a3b8;
  cursor: grab;
  font-size: 1rem;
  line-height: 1;
  flex-shrink: 0;
  user-select: none;
  padding: 0.25rem;
}

.drag-handle:hover {
  color: #64748b;
}

.drag-handle:active {
  cursor: grabbing;
}

.scene-content {
  flex: 1;
  min-width: 0;
}

.scene-name {
  font-weight: 600;
  color: #1e293b;
  font-size: 1rem;
  margin-bottom: 0.5rem;
}

.scene-properties {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  font-size: 0.875rem;
  color: #64748b;
}

.scene-properties > span {
  position: relative;
}

.scene-properties > span:not(:last-child)::after {
  content: '•';
  margin-left: 1rem;
  color: #cbd5e1;
}

.scene-order {
  font-family: monospace;
}

.scene-words {
  color: #059669;
  font-weight: 500;
}

.scene-title {
  color: #7c3aed;
  font-style: italic;
}

.scene-tags {
  color: #dc2626;
}

.scene-actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.scene-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f4f6;
  border-top: 2px solid #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Responsive Design */
@media (max-width: 768px) {
  .section-header,
  .chapter-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .foundation-grid {
    grid-template-columns: 1fr;
  }
  
  .scene-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .drag-handle {
    align-self: flex-end;
  }
  
  .scene-properties {
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .scene-properties > span:not(:last-child)::after {
    display: none;
  }
}
</style>
