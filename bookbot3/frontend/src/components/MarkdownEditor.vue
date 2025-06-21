<template>
  <div 
    class="markdown-editor"
    :class="{ 
      'is-editing': isEditing,
      'is-focused': isFocused,
      'read-only': readonly
    }"
    ref="editorContainerRef"
  >
    <!-- Editor Toolbar or Placeholder Spacer -->
    <div class="editor-toolbar" v-if="isEditing && !readonly">
      <div class="toolbar-group">
        <button 
          class="toolbar-btn" 
          :class="{ active: editor && editor.isActive('heading', { level: 1 }) }"
          @click="editor.chain().focus().toggleHeading({ level: 1 }).run()"
          title="Heading 1"
        >
          H1
        </button>
        <button 
          class="toolbar-btn"
          :class="{ active: editor && editor.isActive('heading', { level: 2 }) }"
          @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
          title="Heading 2"
        >
          H2
        </button>
        <button 
          class="toolbar-btn"
          :class="{ active: editor && editor.isActive('heading', { level: 3 }) }"
          @click="editor.chain().focus().toggleHeading({ level: 3 }).run()"
          title="Heading 3"
        >
          H3
        </button>
      </div>

      <div class="toolbar-group">
        <button 
          class="toolbar-btn"
          :class="{ active: editor && editor.isActive('bold') }"
          @click="editor.chain().focus().toggleBold().run()"
          title="Bold"
        >
          B
        </button>
        <button 
          class="toolbar-btn"
          :class="{ active: editor && editor.isActive('italic') }"
          @click="editor.chain().focus().toggleItalic().run()"
          title="Italic"
        >
          I
        </button>
      </div>

      <div class="toolbar-group">
        <button 
          class="toolbar-btn"
          :disabled="!canUndo"
          @click="editor.chain().focus().undo().run()"
          title="Undo"
        >
          <span class="undo-icon">↶</span>
        </button>
        <button 
          class="toolbar-btn"
          :disabled="!canRedo"
          @click="editor.chain().focus().redo().run()"
          title="Redo"
        >
          <span class="redo-icon">↷</span>
        </button>
      </div>
      
      <div class="toolbar-spacer"></div>
      
      <div class="word-count" v-if="showWordCount && isEditing">
        {{ wordCount }} words
      </div>
    </div>
    
    <!-- Empty spacer with same height as toolbar when not editing -->
    <div class="toolbar-spacer" v-if="!isEditing || readonly"></div>
    
    <!-- Main Editor Content -->
    <div class="editor-content" :style="fontStyles">
      <div 
        v-if="!isEditing" 
        class="display-content markdown-styled" 
        v-html="renderedHtml" 
        @click="handleContainerClick($event)"
        @mouseup="handleContainerMouseUp($event)"
      ></div>
      <template v-else>
        <editor-content :editor="editor" />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { Editor, EditorContent, useEditor } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Typography from '@tiptap/extension-typography'
import { Extension } from '@tiptap/core'
import { Plugin, PluginKey } from 'prosemirror-state'
import { Decoration, DecorationSet } from 'prosemirror-view'
import { marked } from 'marked'

// Define custom extension to highlight hashtags
// We'll use CSS for tag highlighting instead
// of relying on a Tiptap extension

// Use markdown parser for display mode with proper styling
const renderMarkdown = (text: string) => {
  if (!text) return ''
  // Configure marked to output proper styling
  marked.setOptions({
    breaks: true,   // Convert newlines to <br>
    gfm: true      // Use GitHub Flavored Markdown
  })
  return marked(text)
}

interface Props {
  modelValue: string
  placeholder?: string
  readonly?: boolean
  showToolbar?: boolean
  showWordCount?: boolean
  fontFamily?: string
  fontSize?: string
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'focus'): void
  (e: 'blur'): void
  (e: 'edit-mode-change', value: boolean): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Start writing...',
  readonly: false,
  showToolbar: true,
  showWordCount: true,
  fontFamily: 'Georgia, serif',
  fontSize: '18px'
})

const emit = defineEmits<Emits>()

// State and refs
const isEditing = ref(false)
const isFocused = ref(false)
const editorContainerRef = ref<HTMLElement | null>(null)
const renderedHtml = computed(() => {
  // First convert markdown to HTML, then highlight hashtags
  const html = renderMarkdown(props.modelValue)
  return renderHashtags(html)
})

// Font styling
const fontStyles = computed(() => ({
  fontFamily: props.fontFamily,
  fontSize: props.fontSize
}))

// Custom Scene Highlight Extension
const SceneHighlight = Extension.create({
  name: 'sceneHighlight',
  
  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: new PluginKey('sceneHighlight'),
        props: {
          decorations(state) {
            const {doc} = state
            const decorations: Decoration[] = []
            
            // Find all instances of [[Scene XXX]] where XXX is a number
            const sceneRegex = /\[\[Scene \d+\]\]/g
            
            doc.descendants((node, pos) => {
              if (!node.isText) return
              
              const text = node.text as string
              let match
              
              // Find all matches in this text node
              while ((match = sceneRegex.exec(text)) !== null) {
                const from = pos + match.index
                const to = from + match[0].length
                
                // Create a decoration for this match
                decorations.push(
                  Decoration.inline(from, to, {
                    class: 'scene-decoration'
                  })
                )
              }
            })
            
            return DecorationSet.create(doc, decorations)
          }
        }
      })
    ]
  }
})

// Track user input vs programmatic updates
const isUserInput = ref(false)

// Initialize editor with reactive setup
const editor = useEditor({
  extensions: [
    StarterKit.configure({
      heading: {
        levels: [1, 2, 3],
      },
      bold: true,
      italic: true,
      bulletList: true,
      orderedList: true,
    }),
    SceneHighlight,
    Typography,
    Placeholder.configure({
      placeholder: props.placeholder,
    }),
  ],
  content: renderMarkdown(props.modelValue || ''),
  editable: !props.readonly,
  onUpdate: ({ editor, transaction }) => {
    // Only consider it user input if typing or actual text changes were made by the user
    // This helps us to distinguish between user typing and programmatic updates
    isUserInput.value = transaction.docChanged && transaction.getMeta('addToHistory') !== false
    
    // Convert the HTML content to markdown and emit update
    const html = editor.getHTML()
    const markdown = convertToMarkdown(html)
    emit('update:modelValue', markdown)
    
    // Reset the isUserInput flag after a short delay
    // This ensures future external updates will be processed
    if (isUserInput.value) {
      setTimeout(() => {
        isUserInput.value = false
      }, 300) // Delay long enough to prevent cursor jump but short enough to allow future updates
    }
    
    // Update undo/redo state after changes
    canUndo.value = editor.can().undo()
    canRedo.value = editor.can().redo()
  },
  onFocus: () => {
    isFocused.value = true
    emit('focus')
  },
  onBlur: () => {
    isFocused.value = false
    emit('blur')
  }
})

// Watch for external changes to content when not editing
watch(() => props.modelValue, (newVal, oldVal) => {
  // Skip updates when the editor is focused and the user is typing
  // This prevents the cursor from jumping when typing
  if (!editor.value || !newVal || isUserInput.value) {
    return
  }
  
  // Only update if the content actually changed significantly
  const currentMarkdown = convertToMarkdown(editor.value.getHTML())
  if (currentMarkdown === newVal) {
    return
  }

  // Update content
  editor.value.commands.setContent(renderMarkdown(newVal))
}, { immediate: true })

// Watch for readonly changes
watch(() => props.readonly, (newValue) => {
  if (editor) {
    editor.setEditable(!newValue)
    if (newValue && isEditing.value) {
      isEditing.value = false
      emit('edit-mode-change', false)
    }
  }
})

// Computed
const wordCount = computed(() => {
  if (!editor.value) return 0
  const text = editor.value.getText()
  return text ? text.trim().split(/\s+/).length : 0
})

// Since Tiptap doesn't expose direct can().undo() method, we'll simplify this
const canUndo = ref(false)
const canRedo = ref(false)

// Watch for editor initialization
watch(editor, (newEditor) => {
  if (newEditor) {
    // Update undo/redo state
    canUndo.value = newEditor.can().undo()
    canRedo.value = newEditor.can().redo()
    
    // Sync readonly state if it changes
    newEditor.setEditable(!props.readonly)
  }
}, { immediate: true })

// Watch readonly prop
watch(() => props.readonly, (newValue) => {
  if (editor.value) {
    editor.value.setEditable(!newValue)
  }
})

// Handle container click to enter edit mode
function handleContainerClick(event: MouseEvent): void {
  // Only proceed if we're not in readonly mode
  if (props.readonly) return
  
  // Check if this was a simple click (not part of selection)
  const selection = window.getSelection()
  if (selection && selection.toString().length === 0) {
    // If no text is selected, switch to edit mode immediately
    activateEditor()
  }
}

// Handle mouse up event to capture text selection
function handleContainerMouseUp(event: MouseEvent): void {
  // Only proceed if we're not in readonly mode
  if (props.readonly) return
  
  // Check if text was selected
  const selection = window.getSelection()
  
  // Wait a brief moment to let the selection finalize
  setTimeout(() => {
    // If text was selected, activate editor and preserve selection if possible
    activateEditor()
  }, 10)
}

// Common function to activate the editor
function activateEditor(): void {
  // Switch to edit mode
  isEditing.value = true
  
  // Focus the editor after DOM updates
  setTimeout(() => {
    if (editor.value) {
      editor.value.commands.focus()
    }
  }, 50)
}

// Handle editor blur to exit edit mode
function handleEditorBlur(): void {
  // Small delay to allow for button clicks to register before hiding toolbar
  setTimeout(() => {
    isEditing.value = false
  }, 150)
}

// Function to convert HTML to markdown
function convertToMarkdown(html: string): string {
  if (!html) return ''
  
  // Use a turndown service to convert HTML to markdown
  // This is a simplified version - in production you'd use a library like turndown
  let markdown = html
    // Replace heading tags
    .replace(/<h1>(.*?)<\/h1>/g, '# $1\n')
    .replace(/<h2>(.*?)<\/h2>/g, '## $1\n')
    .replace(/<h3>(.*?)<\/h3>/g, '### $1\n')
    // Replace paragraph tags
    .replace(/<p>(.*?)<\/p>/g, '$1\n\n')
    // Replace strong/bold tags
    .replace(/<strong>(.*?)<\/strong>/g, '**$1**')
    .replace(/<b>(.*?)<\/b>/g, '**$1**')
    // Replace em/italic tags
    .replace(/<em>(.*?)<\/em>/g, '*$1*')
    .replace(/<i>(.*?)<\/i>/g, '*$1*')
    // Replace br tags
    .replace(/<br\s*\/?>/g, '\n')
    // Replace list items
    .replace(/<ul>(.*?)<\/ul>/gs, (match, content) => {
      return content.replace(/<li>(.*?)<\/li>/g, '- $1\n') + '\n'
    })
    .replace(/<ol>(.*?)<\/ol>/gs, (match, content) => {
      let index = 1
      return content.replace(/<li>(.*?)<\/li>/g, () => `${index++}. $1\n`) + '\n'
    })
    // Remove remaining tags
    .replace(/<[^>]*>/g, '')
    // Fix entities
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
  
  // Cleanup multiple line breaks
  markdown = markdown.replace(/\n{3,}/g, '\n\n').trim()
  
  return markdown
}

// We'll handle tag highlighting in CSS instead
// This is a simpler approach that doesn't require the highlight extension
function renderHashtags(content: string): string {
  if (!content) return ''
  
  // Highlight tags that start with #
  let highlighted = content.replace(/(?<=^|\s)(#\w+)/g, '<span class="tag-highlight">$1</span>')
  
  // Highlight scene references like [[Scene 123]]
  highlighted = highlighted.replace(/(\[\[Scene \d+\]\])/g, '<span class="scene-highlight">$1</span>')
  
  return highlighted
}

// Setup click outside detection
function handleDocumentClick(event: MouseEvent) {
  if (!isEditing.value) return
  
  // Check if the click was outside the editor container
  const target = event.target as Node
  if (editorContainerRef.value && !editorContainerRef.value.contains(target)) {
    isEditing.value = false
  }
}

// Add and remove event listeners
onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

// Handle cleanup
onBeforeUnmount(() => {
  // Remove document click handler
  document.removeEventListener('click', handleDocumentClick)
  
  // Proper cleanup for Tiptap
  if (editor.value) {
    editor.value.destroy()
  }
})

// Expose methods
defineExpose({
  startEditing() {
    if (!props.readonly && !isEditing.value) {
      isEditing.value = true
      emit('edit-mode-change', true)
      setTimeout(() => {
        editor?.commands.focus('end')
      }, 50)
    }
  },
  stopEditing() {
    if (isEditing.value) {
      isEditing.value = false
      emit('edit-mode-change', false)
    }
  },
  focus() {
    if (!isEditing.value && !props.readonly) {
      isEditing.value = true
      emit('edit-mode-change', true)
    }
    editor?.commands.focus()
  },
  blur() {
    editor?.commands.blur()
  }
})

// Toolbar actions
function toggleHeading(level: 1 | 2 | 3) {
  if (editor.value) {
    editor.value.commands.toggleHeading({ level })
  }
}

function toggleBold() {
  if (editor.value) {
    editor.value.commands.toggleBold()
  }
}

function toggleItalic() {
  if (editor.value) {
    editor.value.commands.toggleItalic()
  }
}

function undo() {
  if (editor.value) {
    editor.value.commands.undo()
  }
}

function redo() {
  if (editor.value) {
    editor.value.commands.redo()
  }
}
</script>

<style scoped>
.markdown-editor {
  position: relative;
  border-radius: 8px;
  background: transparent;
  transition: all 0.2s ease;
  border: 1px solid transparent; /* Invisible border to maintain spacing */
}

.markdown-editor.is-editing {
  border: 1px solid #d1d5db;
  background: white;
}

.markdown-editor.is-focused {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgb(102 126 234 / 0.1);
}

.markdown-editor.read-only {
  cursor: default;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  gap: 0.5rem;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  height: 49px; /* Fixed height to prevent content jumping */
  box-sizing: border-box;
}

.toolbar-spacer {
  height: 49px; /* Same height as toolbar */
  box-sizing: border-box;
  background: transparent;
  border: none;
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
  min-height: 150px;
  padding: 1rem;
}

/* Display mode styling */
.display-content {
  cursor: text;
  min-height: 2.5rem;
}

/* Ensure the editor has good spacing */
:deep(.ProseMirror) {
  outline: none;
  min-height: 150px;
}

:deep(.ProseMirror p) {
  margin: 0.5em 0;
}

:deep(.ProseMirror h1),
:deep(.ProseMirror h2),
:deep(.ProseMirror h3) {
  margin: 1em 0 0.5em;
  font-weight: 600;
}

:deep(.ProseMirror h2) {
  font-size: 1.3em;
}

:deep(.ProseMirror h3) {
  font-size: 1.1em;
}

:deep(.ProseMirror) > * + * {
  margin-top: 0.75em;
}

/* Tag styling */
:deep(.tag-highlight) {
  color: #2563eb;
  font-weight: 500;
}

/* Scene reference styling - display mode */
:deep(.scene-highlight) {
  color: #9333ea; /* Purple color */
  font-weight: 600;
  background-color: #f3e8ff; /* Light purple background */
  padding: 0.1em 0.3em;
  border-radius: 3px;
}

/* Scene reference styling - edit mode */
:deep(.ProseMirror .scene-decoration) {
  color: #9333ea !important;
  font-weight: 600 !important;
  background-color: #f3e8ff !important;
  padding: 0.1em 0.3em !important;
  border-radius: 3px !important;
}

/* Styling for the markdown display mode */
.markdown-styled :deep(h1) {
  font-size: 1.8em;
  font-weight: bold;
  margin: 0.8em 0 0.5em;
}

.markdown-styled :deep(h2) {
  font-size: 1.4em;
  font-weight: bold;
  margin: 0.7em 0 0.5em;
}

.markdown-styled :deep(h3) {
  font-size: 1.2em;
  font-weight: bold;
  margin: 0.6em 0 0.5em;
}

.markdown-styled :deep(strong) {
  font-weight: bold;
}

.markdown-styled :deep(em) {
  font-style: italic;
}

.markdown-styled :deep(p) {
  margin: 0.5em 0;
}

.markdown-styled :deep(ul), 
.markdown-styled :deep(ol) {
  margin-left: 1.5em;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

.markdown-styled :deep(code) {
  font-family: monospace;
  padding: 0.1em 0.3em;
  background-color: #f0f0f0;
  border-radius: 3px;
}

/* Placeholder styling */
:deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  color: #9ca3af;
  pointer-events: none;
  height: 0;
}

/* Selection styling */
:deep(.ProseMirror-focused) {
  outline: none;
}

/* Display content styling for headers and other elements */
.display-content :deep(h1),
.display-content :deep(h2),
.display-content :deep(h3) {
  margin: 1em 0 0.5em;
  font-weight: 600;
}

.display-content :deep(h2) {
  font-size: 1.3em;
}

.display-content :deep(h3) {
  font-size: 1.1em;
}

.display-content :deep(p) {
  margin: 0.5em 0;
}

.display-content :deep(strong) {
  font-weight: 600;
}

.display-content :deep(em) {
  font-style: italic;
}
</style>
