<template>
  <div 
    class="scene-editor"
    :class="{ 
      'is-editing': isEditing,
      'is-focused': isFocused,
      'read-only': readonly
    }"
    ref="editorContainerRef"
  >
    <!-- Editor Toolbar or Placeholder Spacer -->
    <div class="editor-toolbar" v-if="isEditing && !readonly && editor">
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
      <editor-content :editor="editor" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Typography from '@tiptap/extension-typography'
import { Extension } from '@tiptap/core'
import { Plugin, PluginKey } from 'prosemirror-state'
import { Decoration, DecorationSet } from 'prosemirror-view'
import { Node as ProseMirrorNode } from 'prosemirror-model'
import { marked } from 'marked'
import { defaultMarkdownSerializer } from 'prosemirror-markdown'
import CharacterCount from '@tiptap/extension-character-count'

// 1. PROPS & EMITS
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
  (e: 'update:text', value: string): void
  (e: 'edit-mode-change', value: boolean): void
  (e: 'text-selected', text: string): void
  (e: 'focus'): void
  (e: 'blur'): void
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

// 2. STATE
const isEditing = ref(false)
const isFocused = ref(false)
const editorContainerRef = ref<HTMLElement | null>(null)
const canUndo = ref(false)
const canRedo = ref(false)
const wordCount = ref(0)

const fontStyles = computed(() => ({
  fontFamily: props.fontFamily,
  fontSize: props.fontSize
}))

// 3. EDITOR SETUP
const SceneHighlight = Extension.create({
  name: 'sceneHighlight',
  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: new PluginKey('sceneHighlight'),
        state: {
          init: (_, { doc }) => findSceneHighlights(doc),
          apply: (tr, old) => (tr.docChanged ? findSceneHighlights(tr.doc) : old),
        },
        props: {
          decorations(state) {
            return this.getState(state)
          },
        },
      }),
    ]
  },
})

function findSceneHighlights(doc: ProseMirrorNode) {
  const decorations: Decoration[] = []
  const sceneRegex = /@scene:(\w+)/g
  doc.descendants((node: ProseMirrorNode, pos: number) => {
    if (!node.isText) return
    let match
    while ((match = sceneRegex.exec(node.text!)) !== null) {
      const start = pos + match.index
      const end = start + match[0].length
      decorations.push(Decoration.inline(start, end, { class: 'scene-decoration' }))
    }
  })
  return DecorationSet.create(doc, decorations)
}

// IMPORTANT: Markdown Handling
// This editor is configured to work with Markdown. It uses a two-step process:
// 1. Inbound: The `modelValue` (a Markdown string) is converted to HTML using `marked()`
//    before being passed to the editor's `content` property. This allows TipTap
//    to render rich text and formatting.
// 2. Outbound: On updates, the editor's internal state (`editor.state.doc`) is
//    serialized back into a Markdown string using `defaultMarkdownSerializer`.
//    This ensures that the `update:modelValue` emit sends clean Markdown.
// This approach keeps the data pure (Markdown) while leveraging TipTap's
// rich text editing capabilities.
const editor = useEditor({
  extensions: [
    StarterKit.configure({ heading: { levels: [1, 2, 3] } }),
    SceneHighlight,
    Typography,
    Placeholder.configure({ placeholder: props.placeholder }),
    CharacterCount,
  ],
  content: marked(props.modelValue || ''),
  editable: false,
  editorProps: {
    handleClick: () => {
      if (!isEditing.value && !props.readonly) {
        activateEditor()
        return true
      }
      return false
    },
  },
  onUpdate({ editor }) {
    const markdown = defaultMarkdownSerializer.serialize(editor.state.doc)
    emit('update:modelValue', markdown)

    const text = editor.getText()
    emit('update:text', text)
    wordCount.value = editor.storage.characterCount.words()
    canUndo.value = editor.can().undo()
    canRedo.value = editor.can().redo()
  },
  onFocus() {
    isFocused.value = true
    emit('focus')
  },
  onBlur() {
    handleBlur()
  },
})

// 4. LIFECYCLE & WATCHERS
watch(() => props.modelValue, (newVal) => {
  if (editor.value && !editor.value.isFocused) {
    const currentMarkdown = defaultMarkdownSerializer.serialize(editor.value.state.doc)
    if (newVal !== currentMarkdown) {
      // Use nextTick to ensure the update happens after Vue's rendering cycle
      nextTick(() => {
        if (editor.value) { // Check if editor still exists
          editor.value.commands.setContent(marked(newVal || ''), false)
        }
      })
    }
  }
})

watch(isEditing, (editing) => {
  emit('edit-mode-change', editing)
})

onMounted(() => {
  document.addEventListener('click', handleDocumentClick, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick, true)
  editor.value?.destroy()
})

// 5. METHODS
function activateEditor() {
  if (props.readonly || isEditing.value) return
  isEditing.value = true
  nextTick(() => {
    editor.value?.setEditable(true)
    editor.value?.commands.focus()
  })
}

function handleBlur() {
  setTimeout(() => {
    if (editorContainerRef.value && !editorContainerRef.value.contains(document.activeElement)) {
      isEditing.value = false
      isFocused.value = false
      editor.value?.setEditable(false)
      emit('blur')
    }
  }, 200)
}

function handleDocumentClick(event: MouseEvent) {
  if (isEditing.value && editorContainerRef.value && !editorContainerRef.value.contains(event.target as Node)) {
    isEditing.value = false
    isFocused.value = false
    editor.value?.setEditable(false)
    emit('blur')
  }
}

// Expose methods
defineExpose({
  focus: () => editor.value?.commands.focus(),
  blur: () => editor.value?.commands.blur(),
  clearContent: () => editor.value?.commands.clearContent(),
  setContent: (content: string) => editor.value?.commands.setContent(content, true)
})
</script>

<style scoped>
.scene-editor {
  position: relative;
  border-radius: 8px;
  transition: all 0.2s ease;
  cursor: text;
  background: #f8fafc;
  border: 1px solid transparent; /* Invisible border to maintain spacing */
}

.scene-editor.is-editing {
  border: 1px solid #d1d5db;
  background: white;
}

.scene-editor.is-focused {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgb(102 126 234 / 0.1);
}

.scene-editor.read-only {
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

/* Styling for the scene display mode */
.scene-styled :deep(h1) {
  font-size: 1.8em;
  font-weight: bold;
  margin: 0.8em 0 0.5em;
}

.scene-styled :deep(h2) {
  font-size: 1.4em;
  font-weight: bold;
  margin: 0.7em 0 0.5em;
}

.scene-styled :deep(h3) {
  font-size: 1.2em;
  font-weight: bold;
  margin: 0.6em 0 0.5em;
}

.scene-styled :deep(strong) {
  font-weight: bold;
}

.scene-styled :deep(em) {
  font-style: italic;
}

.scene-styled :deep(p) {
  margin: 0.5em 0;
}

.scene-styled :deep(ul), 
.scene-styled :deep(ol) {
  margin-left: 1.5em;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

.scene-styled :deep(code) {
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
