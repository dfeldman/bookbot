<template>
  <div class="bot-task-editor">
    <!-- Header: Task Name -->
    <div class="editor-header">
      <input
        id="bot-task-name"
        v-model="name"
        class="bot-name-input"
        placeholder="Enter Task Name"
      />

    </div>

    <div class="editor-main">
      <!-- Left side: Main Prompt Template -->
      <div class="system-prompt-container">
        <label for="task-content">Main Prompt Template</label>
        <MarkdownEditor
          id="task-content"
          v-model="content"
          :show-toolbar="true"
          :show-word-count="true"
          placeholder="Enter the main prompt template. Use placeholders like {{PreviousChunk}}..."
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
            <p class="form-description">Assigns the task to a category for easier management.</p>
            <select 
              id="llm-group" 
              v-model="llm_group"
            >
              <option value="Writer">Writer</option>
              <option value="Editor">Editor</option>
              <option value="Reviewer">Reviewer</option>
              <option value="Thinker">Thinker</option>
              <option value="Explicit">Explicit</option>
            </select>
          </div>

          <!-- Jobs -->
          <div class="form-group">
            <label for="applicable-jobs">Applicable Jobs</label>
            <p class="form-description">Comma-separated list of job types this task can be used for (e.g., GenerateChunk, EditChunk).</p>
            <input
              id="applicable-jobs"
              v-model="applicable_jobs"
              placeholder="e.g., generate_text, create_foundation"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { PropType } from 'vue'
import MarkdownEditor from './SceneEditor.vue';
import type { Chunk } from '../stores/types'

const props = defineProps({
  modelValue: {
    type: Object as PropType<Chunk>,
    required: true
  },
  isSaving: {
    type: Boolean,
    default: false
  },
  saveStatus: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'save'])

// Local state to hold the chunk data.
// This is necessary to handle the asynchronous loading from the parent.
const localModel = ref<Chunk>({ ...props.modelValue });

watch(() => props.modelValue, (newVal) => {
  localModel.value = { ...newVal };
}, { deep: true });

// Writable computed properties to sync with parent
const name = computed({
  get: () => localModel.value.props?.name || '',
  set: (value) => {
    const newProps = { ...localModel.value.props, name: value };
    emit('update:modelValue', { ...localModel.value, props: newProps });
  }
});

const content = computed({
  get: () => localModel.value.text || '',
  set: (value) => {
    emit('update:modelValue', { ...localModel.value, text: value });
  }
});

const llm_group = computed({
  get: () => localModel.value.props?.llm_group || 'Writer',
  set: (value) => {
    const newProps = { ...localModel.value.props, llm_group: value };
    emit('update:modelValue', { ...localModel.value, props: newProps });
  }
});

const applicable_jobs = computed({
  get: () => (localModel.value.props?.applicable_jobs || []).join(', '),
  set: (value) => {
    const newProps = { ...localModel.value.props, applicable_jobs: value.split(',').map((s: string) => s.trim()) };
    emit('update:modelValue', { ...localModel.value, props: newProps });
  }
});
</script>

<style scoped>
/* Copied from BotEditor.vue for consistency */
.bot-task-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  overflow: hidden;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
