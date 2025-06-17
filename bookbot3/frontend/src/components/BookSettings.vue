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
          <div class="form-item">
            <label>Book Title:</label>
            <input 
              v-model="bookSettings.name"
              @input="markAsChanged"
              placeholder="Enter book title"
              class="form-input"
            />
          </div>
          
          <div class="form-item">
            <label>Genre:</label>
            <select 
              v-model="bookSettings.genre"
              @change="markAsChanged"
              class="form-input"
            >
              <option value="">Select genre</option>
              <option value="Fiction">Fiction</option>
              <option value="Non-Fiction">Non-Fiction</option>
              <option value="Fantasy">Fantasy</option>
              <option value="Science Fiction">Science Fiction</option>
              <option value="Mystery">Mystery</option>
              <option value="Romance">Romance</option>
              <option value="Thriller">Thriller</option>
              <option value="Biography">Biography</option>
              <option value="History">History</option>
              <option value="Self-Help">Self-Help</option>
              <option value="Other">Other</option>
            </select>
          </div>
          
          <div class="form-item full-width">
            <label>Description:</label>
            <textarea 
              v-model="bookSettings.description"
              @input="markAsChanged"
              placeholder="Enter book description"
              class="form-textarea"
              rows="4"
            ></textarea>
          </div>
          
          <div class="form-item">
            <label>Writing Style:</label>
            <input 
              v-model="bookSettings.style"
              @input="markAsChanged"
              placeholder="e.g., Literary, Contemporary, Casual"
              class="form-input"
            />
          </div>
          
          <div class="form-item">
            <label>Target Audience:</label>
            <select 
              v-model="bookSettings.target_audience"
              @change="markAsChanged"
              class="form-input"
            >
              <option value="">Select audience</option>
              <option value="Children">Children</option>
              <option value="Young Adult">Young Adult</option>
              <option value="Adult">Adult</option>
              <option value="General">General</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Writing Preferences -->
      <div class="settings-section">
        <h4>Writing Preferences</h4>
        <div class="form-grid">
          <div class="form-item">
            <label>Default Chapter Length:</label>
            <select 
              v-model="bookSettings.default_chapter_length"
              @change="markAsChanged"
              class="form-input"
            >
              <option value="">No preference</option>
              <option value="short">Short (1,000-2,000 words)</option>
              <option value="medium">Medium (2,000-4,000 words)</option>
              <option value="long">Long (4,000+ words)</option>
            </select>
          </div>
          
          <div class="form-item">
            <label>Narrative Perspective:</label>
            <select 
              v-model="bookSettings.narrative_perspective"
              @change="markAsChanged"
              class="form-input"
            >
              <option value="">Select perspective</option>
              <option value="first">First Person</option>
              <option value="second">Second Person</option>
              <option value="third">Third Person</option>
              <option value="omniscient">Omniscient</option>
            </select>
          </div>
          
          <div class="form-item">
            <label>Tense:</label>
            <select 
              v-model="bookSettings.tense"
              @change="markAsChanged"
              class="form-input"
            >
              <option value="">Select tense</option>
              <option value="present">Present Tense</option>
              <option value="past">Past Tense</option>
              <option value="future">Future Tense</option>
            </select>
          </div>
          
          <div class="form-item">
            <label>Content Rating:</label>
            <select 
              v-model="bookSettings.content_rating"
              @change="markAsChanged"
              class="form-input"
            >
              <option value="">Select rating</option>
              <option value="G">G - General Audiences</option>
              <option value="PG">PG - Parental Guidance</option>
              <option value="PG-13">PG-13 - Parents Strongly Cautioned</option>
              <option value="R">R - Restricted</option>
              <option value="NC-17">NC-17 - Adults Only</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Publication Settings -->
      <div class="settings-section">
        <h4>Publication Settings</h4>
        <div class="form-grid">
          <div class="form-item">
            <label>Author Name:</label>
            <input 
              v-model="bookSettings.author"
              @input="markAsChanged"
              placeholder="Enter author name"
              class="form-input"
            />
          </div>
          
          <div class="form-item">
            <label>ISBN:</label>
            <input 
              v-model="bookSettings.isbn"
              @input="markAsChanged"
              placeholder="Enter ISBN (optional)"
              class="form-input"
            />
          </div>
          
          <div class="form-item">
            <label>Publisher:</label>
            <input 
              v-model="bookSettings.publisher"
              @input="markAsChanged"
              placeholder="Enter publisher (optional)"
              class="form-input"
            />
          </div>
          
          <div class="form-item">
            <label>Publication Date:</label>
            <input 
              type="date"
              v-model="bookSettings.publication_date"
              @input="markAsChanged"
              class="form-input"
            />
          </div>
        </div>
      </div>

      <!-- Book Statistics -->
      <div class="settings-section">
        <h4>Book Statistics</h4>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">Total Chapters:</span>
            <span class="stat-value">{{ bookStats.chapterCount }}</span>
          </div>
          
          <div class="stat-item">
            <span class="stat-label">Total Scenes:</span>
            <span class="stat-value">{{ bookStats.sceneCount }}</span>
          </div>
          
          <div class="stat-item">
            <span class="stat-label">Total Words:</span>
            <span class="stat-value">{{ bookStats.wordCount.toLocaleString() }}</span>
          </div>
          
          <div class="stat-item">
            <span class="stat-label">Created:</span>
            <span class="stat-value">{{ formatDate(book?.created_at) }}</span>
          </div>
          
          <div class="stat-item">
            <span class="stat-label">Last Updated:</span>
            <span class="stat-value">{{ formatDate(book?.updated_at) }}</span>
          </div>
          
          <div class="stat-item">
            <span class="stat-label">Est. Reading Time:</span>
            <span class="stat-value">{{ bookStats.readingTime }}</span>
          </div>
        </div>
      </div>

      <!-- Advanced Settings -->
      <div class="settings-section">
        <h4>Advanced Settings</h4>
        <div class="advanced-options">
          <label class="option-item">
            <input 
              type="checkbox" 
              v-model="bookSettings.auto_save"
              @change="markAsChanged"
            />
            <span>Enable auto-save</span>
          </label>
          
          <label class="option-item">
            <input 
              type="checkbox" 
              v-model="bookSettings.version_control"
              @change="markAsChanged"
            />
            <span>Enable version control for chunks</span>
          </label>
          
          <label class="option-item">
            <input 
              type="checkbox" 
              v-model="bookSettings.collaboration"
              @change="markAsChanged"
            />
            <span>Allow collaboration (coming soon)</span>
          </label>
          
          <label class="option-item">
            <input 
              type="checkbox" 
              v-model="bookSettings.public_sharing"
              @change="markAsChanged"
            />
            <span>Allow public sharing (coming soon)</span>
          </label>
        </div>
      </div>

      <!-- Save Actions -->
      <div class="settings-actions">
        <button 
          @click="resetSettings"
          :disabled="!hasChanges"
          class="reset-btn"
        >
          Reset Changes
        </button>
        
        <button 
          @click="saveSettings"
          :disabled="!hasChanges || isSaving"
          :class="['save-btn', { saving: isSaving }]"
        >
          {{ isSaving ? 'Saving...' : 'Save Settings' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { apiService } from '../services/api'

interface Props {
  book: any
  chunks: any[]
}

const props = defineProps<Props>()
const emit = defineEmits(['book-updated'])

// Settings state
const bookSettings = ref({
  name: '',
  description: '',
  genre: '',
  style: '',
  target_audience: '',
  default_chapter_length: '',
  narrative_perspective: '',
  tense: '',
  content_rating: '',
  author: '',
  isbn: '',
  publisher: '',
  publication_date: '',
  auto_save: true,
  version_control: true,
  collaboration: false,
  public_sharing: false
})

const originalSettings = ref(null)
const hasChanges = ref(false)
const isSaving = ref(false)

// Computed properties
const bookStats = computed(() => {
  const chapters = new Set()
  let sceneCount = 0
  let wordCount = 0
  
  props.chunks.forEach(chunk => {
    if (!chunk.is_deleted) {
      chapters.add(chunk.chapter || 0)
      if (chunk.type === 'scene') sceneCount++
      wordCount += chunk.word_count || 0
    }
  })
  
  const readingTimeMinutes = Math.ceil(wordCount / 200) // Average reading speed
  const readingTime = readingTimeMinutes < 60 
    ? `${readingTimeMinutes} min`
    : `${Math.floor(readingTimeMinutes / 60)}h ${readingTimeMinutes % 60}m`
  
  return {
    chapterCount: chapters.size,
    sceneCount,
    wordCount,
    readingTime
  }
})

// Methods
function markAsChanged() {
  hasChanges.value = true
}

function formatDate(dateString: string): string {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString()
}

function loadSettings() {
  if (!props.book) return
  
  const props_data = props.book.props || {}
  
  bookSettings.value = {
    name: props_data.name || '',
    description: props_data.description || '',
    genre: props_data.genre || '',
    style: props_data.style || '',
    target_audience: props_data.target_audience || '',
    default_chapter_length: props_data.default_chapter_length || '',
    narrative_perspective: props_data.narrative_perspective || '',
    tense: props_data.tense || '',
    content_rating: props_data.content_rating || '',
    author: props_data.author || '',
    isbn: props_data.isbn || '',
    publisher: props_data.publisher || '',
    publication_date: props_data.publication_date || '',
    auto_save: props_data.auto_save !== false,
    version_control: props_data.version_control !== false,
    collaboration: props_data.collaboration === true,
    public_sharing: props_data.public_sharing === true
  }
  
  originalSettings.value = JSON.parse(JSON.stringify(bookSettings.value))
  hasChanges.value = false
}

function resetSettings() {
  if (originalSettings.value) {
    bookSettings.value = JSON.parse(JSON.stringify(originalSettings.value))
    hasChanges.value = false
  }
}

async function saveSettings() {
  if (!hasChanges.value || isSaving.value || !props.book) return
  
  isSaving.value = true
  
  try {
    const updateData = {
      props: {
        ...props.book.props,
        ...bookSettings.value
      }
    }
    
    await apiService.updateBook(props.book.book_id, updateData)
    
    // Update original settings
    originalSettings.value = JSON.parse(JSON.stringify(bookSettings.value))
    hasChanges.value = false
    
    // Emit event to update parent component
    emit('book-updated', updateData)
    
  } catch (error) {
    console.error('Failed to save settings:', error)
    alert('Failed to save settings. Please try again.')
  } finally {
    isSaving.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadSettings()
})
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
