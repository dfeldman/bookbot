<template>
  <div class="bot-editor">
    <!-- Header: Bot Name -->
    <div class="editor-header">
      <input
        id="bot-name"
        class="bot-name-input"
        :value="editableProps.name"
        @input="updateProp('name', ($event.target as HTMLInputElement).value)"
        placeholder="Enter Bot Name"
      />
    </div>

    <div class="editor-main">
      <!-- Left side: System Prompt -->
      <div class="system-prompt-container">
        <label for="system-prompt">System Prompt (Bot's Instructions)</label>
        <MarkdownEditor
          id="system-prompt"
          :modelValue="editableContent"
          @update:modelValue="updateContent"
          :show-toolbar="true"
          :show-word-count="true"
          placeholder="Define the bot's personality, role, and instructions here..."
          fontFamily="'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace"
          :fontSize="'14px'"
          class="markdown-editor-instance"
        />
      </div>

      <!-- Right side: Properties -->
      <div class="properties-sidebar">
        <div class="sidebar-section">
          <h3 class="sidebar-title">Configuration</h3>
          
          <!-- LLM Group -->
          <div class="form-group">
            <label for="llm-group">LLM Group</label>
            <p class="form-description">Assigns the bot to a category for easier management and LLM selection.</p>
            <select 
              id="llm-group" 
              :value="editableProps.llm_group"
              @change="updateProp('llm_group', ($event.target as HTMLSelectElement).value)"
            >
              <option value="Writer">Writer</option>
              <option value="Editor">Editor</option>
              <option value="Reviewer">Reviewer</option>
              <option value="Thinker">Thinker</option>
              <option value="Explicit">Explicit</option>
            </select>
          </div>

          <!-- Temperature -->
          <div class="form-group">
            <label for="temperature">Temperature</label>
            <p class="form-description">Controls creativity. Higher values (e.g., 0.8) are more creative, lower values (e.g., 0.2) are more deterministic.</p>
            <input
              id="temperature"
              :value="editableProps.temperature"
              @input="updateProp('temperature', parseFloat(($event.target as HTMLInputElement).value))"
              type="number"
              step="0.1"
              min="0"
              max="2"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, toRefs } from 'vue'
import type { PropType } from 'vue'
import MarkdownEditor from './MarkdownEditor.vue'
import type { Chunk } from '../stores/book'

const props = defineProps({
  modelValue: {
    type: Object as PropType<Chunk>,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const { modelValue } = toRefs(props)

// Create local reactive copies for editing
const editableContent = ref(modelValue.value.text || '')
const editableProps = ref({ ...modelValue.value.props })

// Watch for incoming changes to the modelValue prop
watch(modelValue, (newVal) => {
  editableContent.value = newVal.text || ''
  editableProps.value = { ...newVal.props }
}, { deep: true, immediate: true }) // Use immediate to set initial state

const updateProp = (key: string, value: any) => {
  editableProps.value[key] = value
  emitUpdate()
}

const updateContent = (newContent: string) => {
  editableContent.value = newContent
  emitUpdate()
}

const emitUpdate = () => {
  const updatedChunk: Chunk = {
    ...modelValue.value,
    text: editableContent.value,
    props: editableProps.value
  }
  emit('update:modelValue', updatedChunk)
}
</script>

<style scoped>
.bot-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  overflow: hidden;
}

.editor-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  background-color: #f8fafc;
}

.bot-name-input {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1e293b;
  border: none;
  background: transparent;
  width: 100%;
  padding: 0.5rem;
  border-radius: 0.375rem;
  transition: background-color 0.2s;
}

.bot-name-input:focus {
  outline: none;
  background-color: #f1f5f9;
}

.bot-name-input::placeholder {
  color: #94a3b8;
}

.editor-main {
  display: flex;
  flex-grow: 1;
  overflow: hidden;
}

.system-prompt-container {
  flex-grow: 1;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.system-prompt-container label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #334155;
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.markdown-editor-instance {
  flex-grow: 1;
}

.properties-sidebar {
  width: 320px;
  flex-shrink: 0;
  border-left: 1px solid #e2e8f0;
  background-color: #f8fafc;
  padding: 1.5rem;
  overflow-y: auto;
}

.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.sidebar-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1e293b;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 0.75rem;
  margin: 0 0 0.5rem 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #334155;
}

.form-description {
    font-size: 0.8rem;
    color: #64748b;
    margin: 0;
}

.form-group input,
.form-group select {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  background: white;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}
</style>
