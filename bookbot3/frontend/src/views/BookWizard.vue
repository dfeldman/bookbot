<template>
  <div class="wizard-container">
    <div class="wizard-content">
      <!-- Header -->
      <div class="wizard-header">
        <h1>Create Your Book</h1>
        <p>Let's gather some information to get started</p>
      </div>

      <!-- Progress Bar -->
      <div class="progress-section">
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: `${(currentStep / totalSteps) * 100}%` }"
          ></div>
        </div>
        <div class="progress-text">
          Step {{ currentStep }} of {{ totalSteps }}
        </div>
      </div>

      <!-- Wizard Steps -->
      <div class="wizard-main">
        <div class="card wizard-card">
          <div class="card-content">
            <!-- Step 1: Book Name -->
            <div v-if="currentStep === 1" class="wizard-step">
              <h2>What's your book called?</h2>
              <p class="step-description">
                Give your book a working title. You can always change this later.
              </p>
              
              <div class="form-group">
                <label class="form-label" for="book-name">Book Title</label>
                <input
                  id="book-name"
                  v-model="bookData.name"
                  type="text"
                  class="form-input form-input-large"
                  placeholder="Enter your book title..."
                  @keyup.enter="nextStep"
                />
              </div>
              
              <div class="example-section">
                <p class="example-label">Examples:</p>
                <div class="example-items">
                  <button 
                    v-for="example in nameExamples" 
                    :key="example"
                    class="example-btn"
                    @click="bookData.name = example"
                  >
                    {{ example }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Step 2: Description -->
            <div v-if="currentStep === 2" class="wizard-step">
              <h2>Tell us about your book</h2>
              <p class="step-description">
                Describe your book's premise, main characters, or central conflict. 
                This helps the AI understand your vision.
              </p>
              
              <div class="form-group">
                <label class="form-label" for="book-description">Book Description</label>
                <textarea
                  id="book-description"
                  v-model="bookData.description"
                  class="form-input form-textarea"
                  placeholder="Describe your book's story, characters, setting, or theme..."
                  rows="6"
                ></textarea>
              </div>
              
              <div class="example-section">
                <p class="example-label">Example:</p>
                <div class="example-text">
                  "A young detective discovers that the serial killer she's hunting is actually her future self, 
                  traveling back in time to prevent an apocalyptic event. As she races to solve the case, 
                  she must decide whether to trust her future self or arrest her."
                </div>
              </div>
            </div>

            <!-- Step 3: Style -->
            <div v-if="currentStep === 3" class="wizard-step">
              <h2>What's your writing style?</h2>
              <p class="step-description">
                Choose the style that best matches how you want your book to feel.
              </p>
              
              <div class="style-options">
                <div 
                  v-for="style in styleOptions" 
                  :key="style.value"
                  class="style-option"
                  :class="{ active: bookData.style === style.value }"
                  @click="bookData.style = style.value"
                >
                  <div class="style-icon">{{ style.icon }}</div>
                  <h3>{{ style.label }}</h3>
                  <p>{{ style.description }}</p>
                </div>
              </div>
            </div>

            <!-- Step 4: Confirmation -->
            <div v-if="currentStep === 4" class="wizard-step">
              <h2>Ready to create your book?</h2>
              <p class="step-description">
                Review your choices and we'll generate a complete foundation for your book.
              </p>
              
              <div class="summary-section">
                <div class="summary-item">
                  <label>Title:</label>
                  <span>{{ bookData.name }}</span>
                </div>
                
                <div class="summary-item">
                  <label>Description:</label>
                  <span>{{ bookData.description }}</span>
                </div>
                
                <div class="summary-item">
                  <label>Style:</label>
                  <span>{{ selectedStyleLabel }}</span>
                </div>
              </div>
              
              <div class="creation-info">
                <div class="info-box">
                  <h3>🎯 What happens next?</h3>
                  <ul>
                    <li>We'll create a detailed outline for your book</li>
                    <li>Generate compelling character profiles</li>
                    <li>Develop rich settings and world-building</li>
                    <li>Create scene breakdowns to guide your writing</li>
                  </ul>
                  <p class="info-note">This process typically takes 2-3 minutes.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <div class="wizard-nav">
        <button
          v-if="currentStep > 1"
          class="btn btn-secondary"
          @click="previousStep"
        >
          Back
        </button>
        
        <div class="nav-spacer"></div>
        
        <button
          v-if="currentStep < totalSteps"
          class="btn btn-primary"
          :disabled="!canProceed"
          @click="nextStep"
        >
          Next
        </button>
        
        <button
          v-if="currentStep === totalSteps"
          class="btn btn-primary btn-create"
          :disabled="!canProceed || isCreating"
          @click="createBook"
        >
          <span v-if="isCreating">Creating...</span>
          <span v-else>Create Book</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useBookStore } from '../stores/book'

const router = useRouter()
const bookStore = useBookStore()

// Wizard state
const currentStep = ref(1)
const totalSteps = 4
const isCreating = ref(false)

// Book data
const bookData = ref({
  name: '',
  description: '',
  style: ''
})

// Example data
const nameExamples = [
  'The Last Algorithm',
  'Shadows of Tomorrow',
  'The Memory Thief',
  'City of Echoes'
]

const styleOptions = [
  {
    value: 'thriller',
    label: 'Thriller',
    icon: '🔥',
    description: 'Fast-paced, suspenseful, with high stakes and tension'
  },
  {
    value: 'fantasy',
    label: 'Fantasy',
    icon: '⚔️',
    description: 'Magical worlds, mythical creatures, and epic adventures'
  },
  {
    value: 'romance',
    label: 'Romance',
    icon: '💕',
    description: 'Character-driven stories focused on relationships and love'
  },
  {
    value: 'sci-fi',
    label: 'Science Fiction',
    icon: '🚀',
    description: 'Futuristic concepts, advanced technology, and what-if scenarios'
  },
  {
    value: 'mystery',
    label: 'Mystery',
    icon: '🔍',
    description: 'Puzzles to solve, clues to follow, and secrets to uncover'
  },
  {
    value: 'literary',
    label: 'Literary Fiction',
    icon: '📖',
    description: 'Character development, complex themes, and beautiful prose'
  }
]

// Computed properties
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 1:
      return bookData.value.name.trim().length > 0
    case 2:
      return bookData.value.description.trim().length > 0
    case 3:
      return bookData.value.style.length > 0
    case 4:
      return true
    default:
      return false
  }
})

const selectedStyleLabel = computed(() => {
  const style = styleOptions.find(s => s.value === bookData.value.style)
  return style ? style.label : ''
})

// Methods
function nextStep() {
  if (canProceed.value && currentStep.value < totalSteps) {
    currentStep.value++
  }
}

function previousStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

async function createBook() {
  if (!canProceed.value || isCreating.value) return
  
  isCreating.value = true
  
  try {
    // Create the book
    const book = await bookStore.createBook({
      name: bookData.value.name,
      description: bookData.value.description,
      style: bookData.value.style
    })
    
    // Start the CreateFoundation job
    const job = await bookStore.startCreateFoundationJob(book.book_id)
    
    // Navigate to dashboard to watch progress
    router.push('/dashboard')
  } catch (error) {
    console.error('Failed to create book:', error)
    // TODO: Show error notification
  } finally {
    isCreating.value = false
  }
}
</script>

<style scoped>
.wizard-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  padding: 2rem 1rem;
}

.wizard-content {
  max-width: 800px;
  margin: 0 auto;
}

.wizard-header {
  text-align: center;
  margin-bottom: 3rem;
}

.wizard-header h1 {
  font-size: 2.5rem;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.wizard-header p {
  font-size: 1.1rem;
  color: #64748b;
  margin: 0;
}

.progress-section {
  margin-bottom: 3rem;
}

.progress-text {
  text-align: center;
  margin-top: 0.5rem;
  color: #64748b;
  font-weight: 500;
}

.wizard-card {
  padding: 3rem;
  margin-bottom: 2rem;
  min-height: 400px;
}

.wizard-step h2 {
  font-size: 1.8rem;
  color: #1e293b;
  margin-bottom: 1rem;
  text-align: center;
}

.step-description {
  text-align: center;
  color: #64748b;
  margin-bottom: 2.5rem;
  font-size: 1.1rem;
  line-height: 1.6;
}

.form-input-large {
  font-size: 1.1rem;
  padding: 1rem;
}

.example-section {
  margin-top: 2rem;
}

.example-label {
  font-size: 0.9rem;
  color: #64748b;
  margin-bottom: 1rem;
}

.example-items {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.example-btn {
  padding: 0.5rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
}

.example-btn:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.example-text {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  font-style: italic;
  color: #475569;
  line-height: 1.6;
}

.style-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.style-option {
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.style-option:hover {
  border-color: #cbd5e1;
  transform: translateY(-2px);
}

.style-option.active {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.style-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.style-option h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
}

.style-option p {
  margin: 0;
  font-size: 0.9rem;
  opacity: 0.8;
}

.summary-section {
  margin-bottom: 2rem;
}

.summary-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
}

.summary-item label {
  font-weight: 600;
  color: #374151;
  min-width: 100px;
  flex-shrink: 0;
}

.summary-item span {
  color: #64748b;
  line-height: 1.5;
}

.creation-info {
  margin-top: 2rem;
}

.info-box {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  border-radius: 12px;
}

.info-box h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
}

.info-box ul {
  margin: 0 0 1rem 0;
  padding-left: 1.5rem;
}

.info-box li {
  margin-bottom: 0.5rem;
}

.info-note {
  margin: 0;
  opacity: 0.9;
  font-size: 0.9rem;
}

.wizard-nav {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-spacer {
  flex: 1;
}

.btn-create {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  min-width: 140px;
}

.btn-create:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

/* Responsive */
@media (max-width: 768px) {
  .wizard-card {
    padding: 2rem 1.5rem;
  }
  
  .wizard-header h1 {
    font-size: 2rem;
  }
  
  .style-options {
    grid-template-columns: 1fr;
  }
  
  .summary-item {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .summary-item label {
    min-width: auto;
  }
}
</style>
