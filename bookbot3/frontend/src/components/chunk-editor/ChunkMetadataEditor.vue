<template>
  <div class="metadata-editor">
    <div class="form-row">
      <div class="form-group">
        <label for="chunk-type">Type</label>
        <select id="chunk-type" :value="modelValue.type" @change="update('type', ($event.target as HTMLSelectElement).value)">
          <option value="markdown">Markdown</option>
          <option value="bot">Bot</option>
          <option value="bot_task">Bot Task</option>
        </select>
      </div>
      <div class="form-group">
        <label for="chunk-chapter">Chapter</label>
        <input id="chunk-chapter" type="number" :value="modelValue.chapter" @input="update('chapter', parseInt(($event.target as HTMLInputElement).value) || 0)" />
      </div>
      <div class="form-group">
        <label for="chunk-order">Order</label>
        <input id="chunk-order" type="number" :value="modelValue.order" @input="update('order', parseInt(($event.target as HTMLInputElement).value) || 0)" />
      </div>
    </div>
    <div class="form-group">
      <label for="chunk-properties">Properties (JSON)</label>
      <textarea id="chunk-properties" :value="propertiesString" @input="updateProperties(($event.target as HTMLTextAreaElement).value)"></textarea>
      <div v-if="propertiesError" class="error-message">{{ propertiesError }}</div>
    </div>
    <div class="form-group">
      <label for="chunk-tags">Tags</label>
      <input id="chunk-tags" type="text" :value="tagsString" @input="updateTags(($event.target as HTMLInputElement).value)" placeholder="comma, separated, tags" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { Chunk } from '@/stores/book';

const props = defineProps<{
  modelValue: Chunk;
}>();

const emit = defineEmits(['update:modelValue']);

const propertiesString = ref('');
const propertiesError = ref('');
const tagsString = ref('');

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    propertiesString.value = JSON.stringify(newVal.props || {}, null, 2);
    tagsString.value = (newVal.props?.tags || []).join(', ');
  }
}, { immediate: true, deep: true });

function update<K extends keyof Chunk>(key: K, value: Chunk[K]) {
  emit('update:modelValue', { ...props.modelValue, [key]: value });
}

function updateProperties(value: string) {
  propertiesString.value = value;
  try {
    const newProperties = JSON.parse(value);
    update('props', newProperties);
    propertiesError.value = '';
  } catch (e) {
    propertiesError.value = 'Invalid JSON format.';
  }
}

function updateTags(value: string) {
  tagsString.value = value;
  const newTags = value.split(',').map(tag => tag.trim()).filter(Boolean);
  const newProps = { ...props.modelValue.props, tags: newTags };
  update('props', newProps);
}
</script>

<style scoped>
.metadata-editor {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
  background-color: #fdfdfd;
}
.form-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}
.form-group {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}
.form-group label {
  margin-bottom: 0.5rem;
  font-weight: bold;
  font-size: 0.875rem;
}
.form-group input, .form-group select, .form-group textarea {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.form-group textarea {
  min-height: 100px;
  font-family: monospace;
}
.error-message {
  color: red;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}
</style>