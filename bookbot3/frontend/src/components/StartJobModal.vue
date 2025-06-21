<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal" @click.stop>
      <h3>Start Job: {{ chunk.props?.name || 'Untitled Task' }}</h3>
      <p class="description">Please provide values for the following placeholders found in the task content.</p>
      
      <div v-if="placeholders.length > 0" class="form-container">
        <div v-for="placeholder in placeholders" :key="placeholder" class="form-group">
          <label :for="placeholder">{{ placeholder }}</label>
          <input :id="placeholder" v-model="formValues[placeholder]" type="text" :placeholder="`Enter value for ${placeholder}`" />
        </div>
      </div>
      <p v-else class="no-placeholders">This bot task has no placeholders. You can start the job directly.</p>
      
      <div class="modal-actions">
        <button @click="$emit('close')" class="cancel-button">Cancel</button>
        <button @click="handleStartJob" class="start-button">Start Job</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import type { Chunk } from '../stores/book';

const props = defineProps<{
  chunk: Chunk;
}>();

const emit = defineEmits(['close', 'start-job']);

const placeholders = ref<string[]>([]);
const formValues = ref<Record<string, string>>({});

const placeholderRegex = /\{\{([^}]+)\}\}/g;

onMounted(() => {
  if (props.chunk && props.chunk.text) {
    const matches = [...props.chunk.text.matchAll(placeholderRegex)];
    const uniquePlaceholders = [...new Set(matches.map(match => match[1].trim()))];
    placeholders.value = uniquePlaceholders;
    placeholders.value.forEach(p => {
      formValues.value[p] = '';
    });
  }
});

function handleStartJob() {
  emit('start-job', formValues.value);
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  text-align: left;
}

.modal h3 {
  margin: 0 0 0.5rem 0;
  color: #111827;
  font-size: 1.25rem;
  font-weight: 600;
}

.modal .description {
  margin: 0 0 1.5rem 0;
  color: #6b7280;
  font-size: 0.875rem;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}

.form-group input {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.no-placeholders {
  color: #6b7280;
  font-style: italic;
  margin-bottom: 2rem;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.cancel-button, .start-button {
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.cancel-button {
  background: #f3f4f6;
  color: #374151;
}
.cancel-button:hover {
  background: #e5e7eb;
}

.start-button {
  background: #4f46e5;
  color: white;
}
.start-button:hover {
  background: #4338ca;
}
</style>
