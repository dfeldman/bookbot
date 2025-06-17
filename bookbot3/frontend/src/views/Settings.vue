<template>
  <div class="settings-container">
    <!-- Status Bar -->
    <StatusBar />
    
    <div class="settings-content">
      <div class="settings-header">
        <h1>User Settings</h1>
        <p>Manage your account and API configuration</p>
      </div>

      <div class="settings-sections">
        <!-- API Token Section -->
        <div class="settings-section">
          <h2>🔑 API Token</h2>
          <div class="setting-item">
            <label for="api-token">OpenRouter API Token</label>
            <div class="token-input-group">
              <input
                id="api-token"
                v-model="apiToken"
                type="password"
                placeholder="sk-or-v1-..."
                class="token-input"
              />
              <button @click="validateToken" class="validate-button" :disabled="!apiToken || isValidating">
                {{ isValidating ? 'Validating...' : 'Validate' }}
              </button>
            </div>
            <p v-if="tokenStatus" :class="['token-status', tokenStatus.valid ? 'valid' : 'invalid']">
              {{ tokenStatus.valid ? `✅ Valid - Balance: $${tokenStatus.balance}` : `❌ ${tokenStatus.error}` }}
            </p>
            <p class="setting-description">
              Your OpenRouter API token is used to generate book content. 
              <a href="https://openrouter.ai/keys" target="_blank">Get your API key here</a>
            </p>
          </div>
        </div>

        <!-- Account Section -->
        <div class="settings-section">
          <h2>👤 Account</h2>
          <div class="setting-item">
            <label for="user-name">Name</label>
            <input
              id="user-name"
              v-model="userName"
              type="text"
              placeholder="Your name"
              class="setting-input"
            />
          </div>
          <div class="setting-item">
            <label for="user-email">Email</label>
            <input
              id="user-email"
              v-model="userEmail"
              type="email"
              placeholder="your@email.com"
              class="setting-input"
            />
          </div>
        </div>

        <!-- Preferences Section -->
        <div class="settings-section">
          <h2>⚙️ Preferences</h2>
          <div class="setting-item">
            <label>Default Writing Style</label>
            <select v-model="defaultStyle" class="setting-select">
              <option value="professional">Professional</option>
              <option value="casual">Casual</option>
              <option value="academic">Academic</option>
              <option value="creative">Creative</option>
              <option value="technical">Technical</option>
            </select>
          </div>
          <div class="setting-item">
            <label>Default Genre</label>
            <select v-model="defaultGenre" class="setting-select">
              <option value="fiction">Fiction</option>
              <option value="non-fiction">Non-Fiction</option>
              <option value="sci-fi">Science Fiction</option>
              <option value="fantasy">Fantasy</option>
              <option value="mystery">Mystery</option>
              <option value="romance">Romance</option>
              <option value="thriller">Thriller</option>
              <option value="biography">Biography</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Save Button -->
      <div class="settings-actions">
        <button @click="saveSettings" class="save-button" :disabled="isSaving">
          {{ isSaving ? 'Saving...' : 'Save Changes' }}
        </button>
        <button @click="goBack" class="cancel-button">
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'
import StatusBar from '../components/StatusBar.vue'

const router = useRouter()
const appStore = useAppStore()

const apiToken = ref('')
const userName = ref('')
const userEmail = ref('')
const defaultStyle = ref('professional')
const defaultGenre = ref('fiction')

const isValidating = ref(false)
const isSaving = ref(false)
const tokenStatus = ref<any>(null)

onMounted(() => {
  // Load current settings
  if (appStore.user) {
    userName.value = appStore.user.props.name || ''
    userEmail.value = appStore.user.props.email || ''
    apiToken.value = appStore.currentApiToken || ''
  }
})

async function validateToken() {
  if (!apiToken.value) return
  
  isValidating.value = true
  tokenStatus.value = null
  
  try {
    const isValid = await appStore.validateApiToken(apiToken.value)
    if (isValid) {
      // Get the full status from the store or make another call
      tokenStatus.value = { valid: true, balance: '25.50' } // Placeholder
    } else {
      tokenStatus.value = { valid: false, error: 'Invalid API token' }
    }
  } catch (error) {
    tokenStatus.value = { valid: false, error: 'Failed to validate token' }
  } finally {
    isValidating.value = false
  }
}

async function saveSettings() {
  isSaving.value = true
  
  try {
    // Save API token
    if (apiToken.value) {
      await appStore.setApiToken(apiToken.value)
    }
    
    // TODO: Save other settings to user profile
    console.log('Settings saved:', {
      name: userName.value,
      email: userEmail.value,
      defaultStyle: defaultStyle.value,
      defaultGenre: defaultGenre.value
    })
    
    // Go back to previous page
    router.back()
  } catch (error) {
    console.error('Failed to save settings:', error)
  } finally {
    isSaving.value = false
  }
}

function goBack() {
  router.back()
}
</script>

<style scoped>
.settings-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

.settings-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.settings-header {
  text-align: center;
  margin-bottom: 3rem;
}

.settings-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.settings-header p {
  color: #64748b;
  font-size: 1.1rem;
}

.settings-sections {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  margin-bottom: 3rem;
}

.settings-section {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.settings-section h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 0.75rem;
}

.setting-item {
  margin-bottom: 1.5rem;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.setting-item label {
  display: block;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
}

.setting-input,
.setting-select,
.token-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.setting-input:focus,
.setting-select:focus,
.token-input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.token-input-group {
  display: flex;
  gap: 0.75rem;
  align-items: stretch;
}

.token-input {
  flex: 1;
}

.validate-button {
  background: #6366f1;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  white-space: nowrap;
}

.validate-button:hover:not(:disabled) {
  background: #4f46e5;
}

.validate-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.token-status {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.token-status.valid {
  background: #dcfce7;
  color: #166534;
}

.token-status.invalid {
  background: #fecaca;
  color: #991b1b;
}

.setting-description {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.setting-description a {
  color: #6366f1;
  text-decoration: none;
}

.setting-description a:hover {
  text-decoration: underline;
}

.settings-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  padding-top: 2rem;
  border-top: 1px solid #e2e8f0;
}

.save-button,
.cancel-button {
  padding: 0.75rem 2rem;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.save-button {
  background: #6366f1;
  color: white;
  border: none;
}

.save-button:hover:not(:disabled) {
  background: #4f46e5;
}

.save-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.cancel-button {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.cancel-button:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

@media (max-width: 768px) {
  .settings-content {
    padding: 1rem;
  }
  
  .token-input-group {
    flex-direction: column;
  }
  
  .settings-actions {
    flex-direction: column;
  }
}
</style>
