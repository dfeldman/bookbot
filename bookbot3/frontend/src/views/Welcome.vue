<template>
  <div class="welcome-container">
    <div class="welcome-content">
      <!-- Header -->
      <div class="welcome-header">
        <div class="logo">
          <div class="logo-icon">📚</div>
          <h1>BookBot</h1>
        </div>
        <p class="tagline">Your AI-powered book writing assistant</p>
      </div>

      <!-- Main Content -->
      <div class="welcome-main">
        <div class="card welcome-card">
          <div class="card-content">
            <!-- API Token Setup -->
            <div v-if="!appStore.hasApiToken" class="token-setup">
              <h2>Welcome to BookBot! 🎉</h2>
              <p class="setup-description">
                To get started, you'll need to provide your OpenRouter API token. 
                This allows BookBot to generate amazing content for your books.
              </p>
              
              <div class="setup-steps">
                <div class="step">
                  <div class="step-number">1</div>
                  <div class="step-content">
                    <h3>Get Your API Token</h3>
                    <p>Visit <a href="https://openrouter.ai" target="_blank" rel="noopener">OpenRouter.ai</a> to create an account and get your API key.</p>
                  </div>
                </div>
                
                <div class="step">
                  <div class="step-number">2</div>
                  <div class="step-content">
                    <h3>Enter Your Token</h3>
                    <div class="form-group">
                      <label class="form-label" for="api-token">OpenRouter API Token</label>
                      <input
                        id="api-token"
                        v-model="tokenInput"
                        type="password"
                        class="form-input"
                        placeholder="sk-or-v1-..."
                        :disabled="isValidating"
                      />
                      <div v-if="tokenError" class="error-message">
                        {{ tokenError }}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="step">
                  <div class="step-number">3</div>
                  <div class="step-content">
                    <h3>Start Writing</h3>
                    <p>Once your token is validated, you can begin creating your first book!</p>
                  </div>
                </div>
              </div>

              <div class="setup-actions">
                <button
                  class="btn btn-primary btn-large"
                  :disabled="!tokenInput || isValidating"
                  @click="validateAndSaveToken"
                >
                  <span v-if="isValidating">Validating...</span>
                  <span v-else>Validate & Continue</span>
                </button>
              </div>
            </div>

            <!-- Ready to Start -->
            <div v-else class="ready-section">
              <h2>Ready to Create! ✨</h2>
              <p class="ready-description">
                Your API token is configured and ready to go. Let's create your first book!
              </p>
              
              <div class="ready-actions">
                <button
                  class="btn btn-primary btn-large"
                  @click="startWizard"
                >
                  Create Your First Book
                </button>
                
                <button
                  v-if="bookStore.hasBooks"
                  class="btn btn-secondary"
                  @click="goToDashboard"
                >
                  View Existing Books
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="welcome-footer">
        <p>&copy; 2025 BookBot. Powered by AI, crafted with care.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'
import { useBookStore } from '../stores/book'

const router = useRouter()
const appStore = useAppStore()
const bookStore = useBookStore()

const tokenInput = ref('')
const tokenError = ref('')
const isValidating = ref(false)

onMounted(async () => {
  // Load books to check if user has any existing books
  if (appStore.hasApiToken) {
    try {
      await bookStore.loadBooks()
    } catch (error) {
      console.error('Failed to load books:', error)
    }
  }
})

async function validateAndSaveToken() {
  if (!tokenInput.value) return
  
  isValidating.value = true
  tokenError.value = ''
  
  try {
    const isValid = await appStore.validateApiToken(tokenInput.value)
    
    if (isValid) {
      await appStore.setApiToken(tokenInput.value)
      // Load books after setting token
      await bookStore.loadBooks()
    } else {
      tokenError.value = 'Invalid API token. Please check your token and try again.'
    }
  } catch (error) {
    tokenError.value = 'Failed to validate token. Please try again.'
    console.error('Token validation error:', error)
  } finally {
    isValidating.value = false
  }
}

function startWizard() {
  router.push('/wizard')
}

function goToDashboard() {
  router.push('/dashboard')
}
</script>

<style scoped>
.welcome-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

.welcome-content {
  width: 100%;
  max-width: 600px;
}

.welcome-header {
  text-align: center;
  margin-bottom: 3rem;
  color: white;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.logo-icon {
  font-size: 3rem;
}

.logo h1 {
  font-size: 3rem;
  font-weight: 700;
  margin: 0;
}

.tagline {
  font-size: 1.2rem;
  opacity: 0.9;
  margin: 0;
}

.welcome-card {
  padding: 3rem;
  margin-bottom: 2rem;
}

.token-setup h2,
.ready-section h2 {
  color: #1e293b;
  margin-bottom: 1rem;
  text-align: center;
}

.setup-description,
.ready-description {
  text-align: center;
  color: #64748b;
  margin-bottom: 2.5rem;
  line-height: 1.6;
}

.setup-steps {
  margin-bottom: 2.5rem;
}

.step {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  align-items: flex-start;
}

.step-number {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.step-content h3 {
  margin: 0 0 0.5rem 0;
  color: #1e293b;
  font-size: 1.1rem;
}

.step-content p {
  margin: 0;
  color: #64748b;
  line-height: 1.5;
}

.step-content a {
  color: #667eea;
  text-decoration: none;
}

.step-content a:hover {
  text-decoration: underline;
}

.setup-actions,
.ready-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: center;
}

.btn-large {
  padding: 1rem 2rem;
  font-size: 1.1rem;
  min-width: 200px;
}

.error-message {
  margin-top: 0.5rem;
  color: #dc2626;
  font-size: 0.9rem;
}

.welcome-footer {
  text-align: center;
  color: white;
  opacity: 0.8;
}

.welcome-footer p {
  margin: 0;
  font-size: 0.9rem;
}

/* Responsive */
@media (max-width: 768px) {
  .welcome-card {
    padding: 2rem 1.5rem;
  }
  
  .logo h1 {
    font-size: 2.5rem;
  }
  
  .logo-icon {
    font-size: 2.5rem;
  }
  
  .tagline {
    font-size: 1.1rem;
  }
  
  .step {
    flex-direction: column;
    text-align: center;
  }
  
  .step-number {
    align-self: center;
  }
}
</style>
