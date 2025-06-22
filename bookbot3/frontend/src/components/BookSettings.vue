<template>
  <div class="book-settings">
    <div class="settings-header">
      <h3>⚙️ Book Settings</h3>
      <p>Configure your book's properties and preferences.</p>
    </div>

    <div class="settings-sections">
      <!-- Basic Information -->
      <div class="settings-section">
        <h4>Basic Information</h4>
        <div class="form-grid">
          <div class="form-item full-width">
            <label>Book Title:</label>
            <input 
              v-model="bookSettings.title"
              placeholder="Enter book title"
              class="form-input"
            />
          </div>
          
          <div class="form-item full-width">
            <label>Description:</label>
            <textarea 
              v-model="bookSettings.description"
              placeholder="Enter book description"
              class="form-textarea"
              rows="4"
            ></textarea>
          </div>
        </div>
      </div>

      <!-- LLM Preferences -->
      <div class="settings-section">
        <h4>LLM Preferences</h4>
        <p class="section-description">
          Set the default Large Language Model for different task types. 
        </p>
        <LLMPreferenceSelector 
          v-if="llmDefaults"
          :modelValue="llmDefaults"
          @update:modelValue="handleDefaultsUpdate"
        />
      </div>

      <!-- LLM Override -->
      <div class="settings-section">
        <h4>LLM Override</h4>
        <p class="section-description">
          Force all tasks to use a specific model, ignoring group defaults. 
          Set to "No Override" to disable.
        </p>
        <LLMPreferenceSelector 
          :modelValue="llmOverride"
          @update:modelValue="handleOverrideUpdate"
          :isOverride="true"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useBookStore } from '../stores/book';
import type { Book } from '../stores/types';
import { apiService } from '../services/api';
import LLMPreferenceSelector from './LLMPreferenceSelector.vue';

// Props & Emits
const props = defineProps<{ 
  book: Book | null;
}>();

const emit = defineEmits(['book-updated']);

// Settings state
const bookSettings = ref<Partial<Book>>({});

// LLM settings
const llmDefaults = ref<{ [key: string]: string }>({});
const llmOverride = ref<string | null>(null);
const llmCatalog = ref<any[]>([]);

const bookStore = useBookStore();

let debounceTimer: number;

// Methods
function loadSettings() {
  if (props.book) {
    bookSettings.value = {
      title: props.book.title ?? '',
      description: props.book.description ?? '',
    };
  }
}

async function saveSettings() {
  if (!props.book) return;

  try {
    const updatedBook = await apiService.updateBook(props.book.book_id, { props: bookSettings.value });
    bookStore.currentBook = updatedBook;
    emit('book-updated', updatedBook);
  } catch (error) {
    console.error('Failed to save settings:', error);
  }
}

async function handleDefaultsUpdate(newDefaults: { [key: string]: string }) {
  if (!props.book) return;
  try {
    await apiService.updateLlmDefaults(props.book.book_id, newDefaults);
    llmDefaults.value = newDefaults;
  } catch (error) {
    console.error('Failed to update LLM defaults:', error);
  }
}

async function handleOverrideUpdate(newOverride: string | null) {
  if (!props.book) return;
  try {
    await apiService.updateLlmOverride(props.book.book_id, newOverride);
    llmOverride.value = newOverride;
  } catch (error) {
    console.error('Failed to update LLM override:', error);
  }
}

// Watchers
watch(bookSettings, (_, oldValue) => {
  if (Object.keys(oldValue).length > 0) { // Ensure it's not the initial load
    clearTimeout(debounceTimer);
    debounceTimer = window.setTimeout(() => {
      saveSettings();
    }, 1000); // 1-second debounce
  }
}, { deep: true });

watch(() => props.book, loadSettings, { immediate: true, deep: true });

// Lifecycle
onMounted(async () => {
  if (props.book) {
    try {
      const [defaults, override, catalog] = await Promise.all([
        apiService.getLlmDefaults(props.book.book_id),
        apiService.getLlmOverride(props.book.book_id),
        apiService.getLlmCatalog()
      ]);
      llmDefaults.value = defaults;
      llmOverride.value = override.llm_id;
      llmCatalog.value = catalog.llms;
    } catch (error) {
      console.error('Failed to load LLM settings:', error);
    }
  }
});
</script>

<style scoped>
.book-settings {
  padding: 1.5rem;
}

.settings-header {
  text-align: center;
  margin-bottom: 2rem;
}

.settings-header h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  color: #1f2937;
}

.settings-header p {
  margin: 0;
  color: #6b7280;
}

.settings-sections {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.settings-section {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.settings-section h4 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  align-items: start;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-item.full-width {
  grid-column: 1 / -1;
}

.form-item label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.form-input,
.form-textarea {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  transition: border-color 0.2s ease;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 100px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 6px;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
}

.stat-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
}

.advanced-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.option-item input {
  margin: 0;
}

.settings-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.reset-btn,
.save-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.reset-btn {
  background: #f3f4f6;
  color: #374151;
}

.reset-btn:hover:not(:disabled) {
  background: #e5e7eb;
}

.save-btn {
  background: #10b981;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #059669;
  transform: translateY(-1px);
}

.save-btn:disabled,
.reset-btn:disabled {
  background: #9ca3af;
  color: #6b7280;
  cursor: not-allowed;
  transform: none;
}

.save-btn.saving {
  background: #6b7280;
}

/* Responsive Design */
@media (max-width: 768px) {
  .book-settings {
    padding: 1rem;
  }
  
  .form-grid,
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .settings-actions {
    flex-direction: column;
  }
}
</style>
