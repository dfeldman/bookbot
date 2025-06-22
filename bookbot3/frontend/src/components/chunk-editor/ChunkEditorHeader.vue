<template>
  <div class="chunk-editor-header">
    <div class="left-actions">
            <router-link :to="`/books/${bookId}`" class="back-link">
        &larr; Back to Book
      </router-link>
      <span class="save-status">{{ saveStatus }}</span>
    </div>
    <div class="right-actions">
      <button @click="$emit('show-versions')" class="action-button">Version History</button>
      <button 
        v-if="isBotTask"
        @click="$emit('start-job')"
        class="start-job-button"
      >
        Start Job
      </button>
      <button v-if="showSaveButton" @click="$emit('save')" :disabled="isSaving" class="action-button save-button">
        {{ isSaving ? 'Saving...' : 'Save Version' }}
      </button>
      <button @click="$emit('delete')" class="action-button delete-button">Delete</button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  bookId: string | number;
  saveStatus: string;
  isSaving: boolean;
  isBotTask: boolean;
  showSaveButton: boolean;
}>();

defineEmits(['save', 'delete', 'show-versions', 'start-job']);
</script>

<style scoped>
.chunk-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background-color: #f7f7f7;
  border-bottom: 1px solid #e0e0e0;
}
.left-actions, .right-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.back-link {
  text-decoration: none;
  color: #007bff;
}
.save-status {
  font-style: italic;
  color: #6c757d;
}
.action-button, .start-job-button {
  padding: 0.5rem 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  background-color: #fff;
  cursor: pointer;
}
.save-button {
  background-color: #28a745;
  color: white;
  border-color: #28a745;
}
.delete-button {
  background-color: #dc3545;
  color: white;
  border-color: #dc3545;
}
.start-job-button {
  background-color: #ffc107;
  border-color: #ffc107;
}
</style>