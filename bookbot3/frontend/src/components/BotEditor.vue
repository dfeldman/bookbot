<template>
  <div class="bot-editor">
    <div class="form-grid">
      <!-- Bot Name -->
      <div class="form-group">
        <label for="bot-name">Bot Name</label>
        <input
          id="bot-name"
          :value="editableProps.name"
          @input="updateProp('name', ($event.target as HTMLInputElement).value)"
          placeholder="e.g., Creative Writer"
        />
      </div>

      <!-- LLM Group -->
      <div class="form-group">
        <label for="llm-group">LLM Group</label>
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

    <!-- System Prompt -->
    <div class="form-group system-prompt-group">
      <label for="system-prompt">System Prompt (Bot's Instructions)</label>
      <MarkdownEditor
        :modelValue="editableContent"
        @update:modelValue="updateContent"
        :show-toolbar="true"
        :show-word-count="true"
        placeholder="Enter the bot's system prompt here. This defines its personality, role, and instructions."
        fontFamily="'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace"
        :fontSize="'14px'"
      />
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
}, { deep: true })

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
  gap: 1.5rem;
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
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
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.system-prompt-group {
  /* The editor component has its own styling, so we just need to manage the label */
}

.system-prompt-group label {
  margin-bottom: 0.25rem;
}
</style>
