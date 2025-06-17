<template>
  <div class="text-editor">
    <div class="editor-toolbar" v-if="showToolbar">
      <div class="toolbar-group">
        <button 
          class="toolbar-btn"
          :class="{ active: isBold }"
          @click="toggleBold"
          title="Bold"
        >
          <strong>B</strong>
        </button>
        <button 
          class="toolbar-btn"
          :class="{ active: isItalic }"
          @click="toggleItalic"
          title="Italic"
        >
          <em>I</em>
        </button>
        <button 
          class="toolbar-btn"
          @click="insertHeading"
          title="Heading"
        >
          H1
        </button>
      </div>
      
      <div class="toolbar-group">
        <button 
          class="toolbar-btn"
          @click="undo"
          :disabled="!canUndo"
          title="Undo"
        >
          ↶
        </button>
        <button 
          class="toolbar-btn"
          @click="redo"
          :disabled="!canRedo"
          title="Redo"
        >
          ↷
        </button>
      </div>
      
      <div class="toolbar-spacer"></div>
      
      <div class="word-count" v-if="showWordCount">
        {{ wordCount }} words
      </div>
    </div>
    
    <div 
      ref="editorElement"
      class="editor-content"
      :class="{ 'with-toolbar': showToolbar }"
      contenteditable="true"
      @input="handleInput"
      @keydown="handleKeyDown"
      @focus="handleFocus"
      @blur="handleBlur"
      :data-placeholder="placeholder"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

interface Props {
  modelValue: string
  placeholder?: string
  showToolbar?: boolean
  showWordCount?: boolean
  readonly?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'focus'): void
  (e: 'blur'): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Start writing...',
  showToolbar: true,
  showWordCount: true,
  readonly: false
})

const emit = defineEmits<Emits>()

// Refs
const editorElement = ref<HTMLDivElement>()
const history = ref<string[]>([])
const historyIndex = ref(-1)
const isFocused = ref(false)

// State tracking
const isBold = ref(false)
const isItalic = ref(false)

// Computed
const wordCount = computed(() => {
  const text = props.modelValue.replace(/<[^>]*>/g, '').trim()
  return text ? text.split(/\s+/).length : 0
})

const canUndo = computed(() => historyIndex.value > 0)
const canRedo = computed(() => historyIndex.value < history.value.length - 1)

// Watch for external content changes
watch(() => props.modelValue, (newValue) => {
  if (editorElement.value) {
    const htmlContent = textToHtml(newValue)
    if (editorElement.value.innerHTML !== htmlContent) {
      editorElement.value.innerHTML = htmlContent
    }
  }
}, { immediate: true })

onMounted(() => {
  if (editorElement.value) {
    const htmlContent = textToHtml(props.modelValue)
    editorElement.value.innerHTML = htmlContent
    addToHistory(props.modelValue)
  }
})

// History management
function addToHistory(content: string) {
  // Remove any future history if we're not at the end
  if (historyIndex.value < history.value.length - 1) {
    history.value = history.value.slice(0, historyIndex.value + 1)
  }
  
  // Add new state
  history.value.push(content)
  historyIndex.value = history.value.length - 1
  
  // Limit history size
  if (history.value.length > 50) {
    history.value.shift()
    historyIndex.value--
  }
}

// Text conversion utilities
function textToHtml(text: string): string {
  if (!text) return ''
  
  // Escape HTML entities first
  let escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  
  // Convert markdown headers to HTML (must be done before paragraph processing)
  escaped = escaped
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')     // ### Header -> <h3>
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')      // ## Header -> <h2>  
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')       // # Header -> <h1>
  
  // Convert newlines to HTML (skip lines that are already headers)
  const lines = escaped.split('\n')
  const processedLines = lines.map(line => {
    // Skip lines that are already HTML headers
    if (line.match(/^<h[1-6]>.*<\/h[1-6]>$/)) {
      return line
    }
    return line
  })
  
  // Join lines and handle paragraphs
  const rejoined = processedLines.join('\n')
  return rejoined
    .replace(/\n\n/g, '</p><p>')               // Double newlines become paragraph breaks
    .replace(/\n/g, '<br>')                    // Single newlines become line breaks
    .replace(/^(.+)$/s, '<p>$1</p>')          // Wrap entire content in paragraph tags
    .replace(/<p>(<h[1-6]>.*?<\/h[1-6]>)<\/p>/g, '$1')  // Remove paragraph tags around headers
    .replace(/<p><\/p>/g, '<p><br></p>')      // Handle empty paragraphs
}

function htmlToText(html: string): string {
  if (!html) return ''
  
  // Convert HTML headers back to markdown first
  let processedHtml = html
    .replace(/<h1>(.*?)<\/h1>/gi, '# $1')      // <h1> -> # Header
    .replace(/<h2>(.*?)<\/h2>/gi, '## $1')     // <h2> -> ## Header  
    .replace(/<h3>(.*?)<\/h3>/gi, '### $1')    // <h3> -> ### Header
    .replace(/<h[4-6]>(.*?)<\/h[4-6]>/gi, '### $1')  // h4-h6 -> ### Header
  
  // Convert HTML structure back to newlines
  processedHtml = processedHtml
    .replace(/<\/p>/gi, '</p>\n\n')           // Paragraph ends = double newline
    .replace(/<br\s*\/?>/gi, '\n')            // Line breaks = single newline
    .replace(/<[^>]*>/g, '')                  // Remove all other HTML tags
  
  // Create a temporary div to decode HTML entities
  const temp = document.createElement('div')
  temp.innerHTML = processedHtml
  let text = temp.textContent || temp.innerText || ''
  
  // Clean up extra whitespace but preserve intentional line breaks
  return text
    .replace(/\n\n\n+/g, '\n\n')             // Multiple blank lines become double newline
    .trim()
}

function undo() {
  if (canUndo.value && editorElement.value) {
    historyIndex.value--
    const textContent = history.value[historyIndex.value]
    const htmlContent = textToHtml(textContent)
    editorElement.value.innerHTML = htmlContent
    emit('update:modelValue', textContent)
  }
}

function redo() {
  if (canRedo.value && editorElement.value) {
    historyIndex.value++
    const textContent = history.value[historyIndex.value]
    const htmlContent = textToHtml(textContent)
    editorElement.value.innerHTML = htmlContent
    emit('update:modelValue', textContent)
  }
}

// Event handlers
function handleInput() {
  if (!editorElement.value) return
  
  const htmlContent = editorElement.value.innerHTML
  const textContent = htmlToText(htmlContent)
  emit('update:modelValue', textContent)
  
  // Add to history with debouncing
  debounceAddToHistory(textContent)
  
  // Update formatting state
  updateFormattingState()
}

function handleKeyDown(event: KeyboardEvent) {
  // Handle keyboard shortcuts
  if (event.ctrlKey || event.metaKey) {
    switch (event.key) {
      case 'b':
        event.preventDefault()
        toggleBold()
        break
      case 'i':
        event.preventDefault()
        toggleItalic()
        break
      case 'z':
        if (event.shiftKey) {
          event.preventDefault()
          redo()
        } else {
          event.preventDefault()
          undo()
        }
        break
    }
  }
  
  // Handle Enter key for better paragraph handling
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    document.execCommand('insertHTML', false, '<br><br>')
  }
}

function handleFocus() {
  isFocused.value = true
  emit('focus')
}

function handleBlur() {
  isFocused.value = false
  emit('blur')
}

// Formatting functions
function toggleBold() {
  document.execCommand('bold', false)
  updateFormattingState()
}

function toggleItalic() {
  document.execCommand('italic', false)
  updateFormattingState()
}

function insertHeading() {
  const selection = window.getSelection()
  if (selection && selection.rangeCount > 0) {
    document.execCommand('formatBlock', false, 'h2')
  }
}

function updateFormattingState() {
  isBold.value = document.queryCommandState('bold')
  isItalic.value = document.queryCommandState('italic')
}

// Debounced history addition
let historyTimeout: NodeJS.Timeout | null = null
function debounceAddToHistory(content: string) {
  if (historyTimeout) {
    clearTimeout(historyTimeout)
  }
  
  historyTimeout = setTimeout(() => {
    addToHistory(content)
  }, 1000)
}

// Public methods
defineExpose({
  focus() {
    editorElement.value?.focus()
  },
  blur() {
    editorElement.value?.blur()
  },
  insertText(text: string) {
    if (editorElement.value) {
      document.execCommand('insertHTML', false, text)
    }
  }
})
</script>

<style scoped>
.text-editor {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  gap: 0.5rem;
}

.toolbar-group {
  display: flex;
  gap: 0.25rem;
}

.toolbar-btn {
  padding: 0.4rem 0.6rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  min-width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toolbar-btn:hover:not(:disabled) {
  background: #f1f5f9;
  border-color: #9ca3af;
}

.toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toolbar-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.toolbar-spacer {
  flex: 1;
}

.word-count {
  font-size: 0.8rem;
  color: #6b7280;
  font-weight: 500;
}

.editor-content {
  min-height: 200px;
  padding: 1rem;
  outline: none;
  line-height: 1.6;
  font-size: 1rem;
}

.editor-content.with-toolbar {
  min-height: 180px;
}

.editor-content:empty::before {
  content: attr(data-placeholder);
  color: #9ca3af;
  pointer-events: none;
}

.editor-content:focus {
  background: #fefefe;
}

/* Rich text styling */
.editor-content h1,
.editor-content h2,
.editor-content h3 {
  margin: 1em 0 0.5em 0;
  font-weight: 600;
}

.editor-content h1 {
  font-size: 1.5em;
}

.editor-content h2 {
  font-size: 1.3em;
}

.editor-content h3 {
  font-size: 1.1em;
}

.editor-content p {
  margin: 0.5em 0;
}

.editor-content strong {
  font-weight: 600;
}

.editor-content em {
  font-style: italic;
}

/* Focus styles */
.text-editor:focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgb(102 126 234 / 0.1);
}
</style>
