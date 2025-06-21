<template>
  <div class="bot-task-editor">
    <div class="form-group">
      <label for="bot-task-name">Task Name</label>
      <input
        id="bot-task-name"
        type="text"
        v-model="editableProps.name"
        placeholder="e.g., 'Summarize Chapter'"
        @input="emitUpdate"
      />
    </div>
    <div class="form-group">
      <label for="bot-task-content">Task Content (Template)</label>
      <MarkdownEditor
        v-model="editableContent"
        :show-toolbar="true"
        :show-word-count="true"
        placeholder="Enter the task instructions or template here. You can use placeholders like {{scene_text}}."
        fontFamily="'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace"
        :fontSize="'14px'"
        @update:modelValue="emitUpdate"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, toRefs } from 'vue'
import MarkdownEditor from './MarkdownEditor.vue'
import type { Chunk } from '../stores/book'

const props = defineProps<{ modelValue: Chunk }>()
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

function emitUpdate() {
  const updatedChunk: Partial<Chunk> = {
    ...modelValue.value,
    text: editableContent.value,
    props: editableProps.value
  }
  emit('update:modelValue', updatedChunk)
}
</script>

<style scoped>
.bot-task-editor {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  font-size: 0.875rem;
  color: #374151;
}

.form-group input {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}
</style>
