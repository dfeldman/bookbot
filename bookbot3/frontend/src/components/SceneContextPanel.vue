<template>
  <div class="scene-context-panel">
    <!-- Panel Header -->
    <div class="panel-header">
      <div class="header-left">
        <h4>📋 Scene Context</h4>
        <div v-if="context.tags?.length" class="tags-list">
          <span 
            v-for="tag in context.tags" 
            :key="tag"
            class="tag"
          >
            #{{ tag }}
          </span>
        </div>
      </div>
      <div class="header-actions">
        <button 
          v-if="hasContextSections"
          @click="toggleCollapsed"
          class="collapse-button"
          :title="isCollapsed ? 'Expand context' : 'Collapse context'"
        >
          {{ isCollapsed ? '▼' : '▲' }}
        </button>
        <button 
          @click="$emit('refresh')"
          :disabled="loading"
          class="refresh-button"
          title="Refresh context"
        >
          🔄
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Loading context...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <span>❌ {{ error }}</span>
      <button @click="$emit('refresh')" class="retry-button">Retry</button>
    </div>

    <!-- Unavailable State -->
    <div v-else-if="!context.available" class="unavailable-state">
      <span>💡 Context is available for scenes with a Scene ID that matches an outline section.</span>
    </div>

    <!-- Context Content Grid -->
    <div v-else-if="hasContextSections && !isCollapsed" class="context-grid">
      <!-- Outline Section -->
      <div v-if="context.outline_section" class="context-section outline-section">
        <h5>📋 Outline</h5>
        <div class="content-box" v-html="renderMarkdown(context.outline_section)"></div>
      </div>

      <!-- Characters Section -->
      <div v-if="context.characters_sections?.length" class="context-section characters-section">
        <h5>👥 Characters ({{ context.characters_sections.length }})</h5>
        <div class="content-list">
          <div 
            v-for="(section, index) in context.characters_sections" 
            :key="index"
            class="content-box"
            v-html="renderMarkdown(section)"
          ></div>
        </div>
      </div>

      <!-- Settings Section -->
      <div v-if="context.settings_sections?.length" class="context-section settings-section">
        <h5>⚙️ Settings ({{ context.settings_sections.length }})</h5>
        <div class="content-list">
          <div 
            v-for="(section, index) in context.settings_sections" 
            :key="index"
            class="content-box"
            v-html="renderMarkdown(section)"
          ></div>
        </div>
      </div>
    </div>

    <!-- Empty Context -->
    <div v-else-if="!hasContextSections" class="empty-context">
      <span>📝 No matching context found for this scene.</span>
      <span class="hint">Make sure the Scene ID matches an outline section with tags.</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'

// Configure marked for inline rendering
marked.setOptions({
  breaks: true,
  gfm: true
})

interface ContextData {
  outline_section: string
  characters_sections: string[]
  settings_sections: string[]
  tags: string[]
  available: boolean
}

interface Props {
  context: ContextData
  loading: boolean
  error: string | null
}

// Define props and get reference to use in computed properties
const props = defineProps<Props>()

defineEmits<{
  refresh: []
}>()

// Local state for collapsing
const isCollapsed = ref(false)

// Computed properties
const hasContextSections = computed(() => {
  return !!(props.context.outline_section || 
           props.context.characters_sections?.length || 
           props.context.settings_sections?.length)
})

// Methods
const toggleCollapsed = () => {
  isCollapsed.value = !isCollapsed.value
}

const renderMarkdown = (text: string): string => {
  if (!text) return ''
  try {
    const result = marked(text)
    // Handle both sync and async returns from marked
    return typeof result === 'string' ? result : text
  } catch (e) {
    console.warn('Failed to render markdown:', e)
    return text
  }
}
</script>

<style scoped>
.scene-context-panel {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  margin-bottom: 1.5rem;
  overflow: hidden;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

/* Panel Header */
.panel-header {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
  padding: 0.75rem 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 3rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.header-left h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.collapse-button,
.refresh-button {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  border-radius: 0.375rem;
  transition: all 0.2s;
  font-size: 0.875rem;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
}

.collapse-button:hover:not(:disabled),
.refresh-button:hover:not(:disabled) {
  background: #e2e8f0;
  color: #334155;
}

.refresh-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Tags in header */
.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.tag {
  background: #6366f1;
  color: white;
  padding: 0.125rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1.5;
}

/* State displays */
.loading-state,
.error-state,
.unavailable-state,
.empty-context {
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #64748b;
  font-size: 0.875rem;
}

.loading-state {
  justify-content: center;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #f3f4f6;
  border-top: 2px solid #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-state {
  color: #dc2626;
  justify-content: space-between;
}

.retry-button {
  background: #dc2626;
  color: white;
  border: none;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.75rem;
  transition: background-color 0.2s;
}

.retry-button:hover {
  background: #b91c1c;
}

.empty-context {
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.5rem;
}

.hint {
  font-size: 0.75rem;
  font-style: italic;
  color: #94a3b8;
}

/* Context Grid Layout */
.context-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1rem;
  padding: 1rem 1.25rem;
  max-height: 24rem;
  overflow-y: auto;
}

/* Responsive grid */
@media (max-width: 1200px) {
  .context-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .context-grid {
    grid-template-columns: 1fr;
  }
}

/* Context Sections */
.context-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.context-section h5 {
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid transparent;
}

.outline-section h5 {
  border-bottom-color: #3b82f6;
}

.characters-section h5 {
  border-bottom-color: #8b5cf6;
}

.settings-section h5 {
  border-bottom-color: #10b981;
}

/* Content Boxes */
.content-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 0.875rem;
  font-size: 0.875rem;
  line-height: 1.6;
  color: #374151;
  overflow-y: auto;
  flex: 1;
}

.content-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  flex: 1;
  min-height: 0;
}

.content-list .content-box {
  flex: none;
  max-height: 8rem;
}

/* Markdown styling within content boxes */
.content-box :deep(h1),
.content-box :deep(h2),
.content-box :deep(h3),
.content-box :deep(h4),
.content-box :deep(h5),
.content-box :deep(h6) {
  margin: 0.5rem 0;
  font-weight: 600;
  color: #1e293b;
}

.content-box :deep(h1) { font-size: 1.125rem; }
.content-box :deep(h2) { font-size: 1rem; }
.content-box :deep(h3) { font-size: 0.875rem; }
.content-box :deep(h4),
.content-box :deep(h5),
.content-box :deep(h6) { font-size: 0.8125rem; }

.content-box :deep(p) {
  margin: 0.5rem 0;
}

.content-box :deep(ul),
.content-box :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.25rem;
}

.content-box :deep(li) {
  margin: 0.25rem 0;
}

.content-box :deep(strong) {
  font-weight: 600;
  color: #1e293b;
}

.content-box :deep(em) {
  font-style: italic;
}

.content-box :deep(code) {
  background: #e2e8f0;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  font-size: 0.8125rem;
}

.content-box :deep(blockquote) {
  border-left: 3px solid #cbd5e1;
  padding-left: 0.75rem;
  margin: 0.5rem 0;
  color: #64748b;
  font-style: italic;
}

/* Color-coded borders for different content types */
.outline-section .content-box {
  border-left: 3px solid #3b82f6;
}

.characters-section .content-box {
  border-left: 3px solid #8b5cf6;
}

.settings-section .content-box {
  border-left: 3px solid #10b981;
}

/* Scrollbar styling */
.context-grid::-webkit-scrollbar,
.content-box::-webkit-scrollbar {
  width: 6px;
}

.context-grid::-webkit-scrollbar-track,
.content-box::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.context-grid::-webkit-scrollbar-thumb,
.content-box::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.context-grid::-webkit-scrollbar-thumb:hover,
.content-box::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
