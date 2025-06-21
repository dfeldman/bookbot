<template>
  <div class="editor-demo">
    <h1>Markdown Editor Demo</h1>
    
    <div class="demo-section">
      <h2>Basic Editor</h2>
      <p class="description">Click to start editing. Features: markdown formatting, tag highlighting, and elegant styling.</p>
      <div class="editor-container">
        <MarkdownEditor
          v-model="content"
          placeholder="Click here to start writing..."
          @edit-mode-change="editModeChanged"
        />
      </div>
      <div class="controls">
        <button @click="resetEditor">Reset Content</button>
      </div>
    </div>
    
    <div class="demo-section">
      <h2>Different Font Settings</h2>
      <p class="description">With custom serif font and larger text size.</p>
      <div class="editor-container">
        <MarkdownEditor
          v-model="content2"
          placeholder="Click here to start writing..."
          fontFamily="'Playfair Display', Georgia, serif"
          fontSize="22px"
        />
      </div>
    </div>
    
    <div class="demo-section">
      <h2>Read-only Mode</h2>
      <p class="description">Non-editable version of the editor.</p>
      <div class="editor-container">
        <MarkdownEditor
          v-model="readonlyContent"
          :readonly="true"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MarkdownEditor from '../components/MarkdownEditor.vue'

// Sample content with markdown and tags
const initialContent = `# Welcome to the BookBot Editor

This is a **markdown** editor with *special* features.

## Features
- Tag highlighting with #tags like #writing and #novel
- Elegant typography
- Click-to-edit interface
- Customizable fonts

### How to use
Simply click anywhere to start editing. Use markdown syntax for formatting.

#bookbot #writing #productivity`

const content = ref(initialContent)
const content2 = ref('# Custom Font Example\n\nThis editor has a larger serif font that\'s perfect for writing prose.\n\n#typography #writing')
const readonlyContent = ref('# Read-only Content\n\nThis content cannot be edited, only viewed. It still supports **markdown** formatting and #tags.')

function resetEditor() {
  content.value = initialContent
}

function editModeChanged(isEditing: boolean) {
  console.log(`Edit mode changed: ${isEditing ? 'now editing' : 'stopped editing'}`)
}
</script>

<style scoped>
.editor-demo {
  max-width: 800px;
  margin: 2rem auto;
  padding: 1rem;
}

h1 {
  margin-bottom: 2rem;
  color: #1e293b;
  font-weight: 600;
  text-align: center;
}

.demo-section {
  margin-bottom: 3rem;
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.demo-section h2 {
  margin-top: 0;
  color: #334155;
  font-weight: 600;
  font-size: 1.25rem;
}

.description {
  font-size: 0.9rem;
  color: #64748b;
  margin-bottom: 1.5rem;
}

.editor-container {
  margin-bottom: 1rem;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.controls {
  margin-top: 1rem;
  display: flex;
  justify-content: center;
}

button {
  background: #6366f1;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

button:hover {
  background: #4f46e5;
}
</style>
