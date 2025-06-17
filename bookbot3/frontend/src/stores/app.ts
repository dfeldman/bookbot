import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService } from '../services/api'

export interface User {
  user_id: string
  props: {
    name?: string
    email?: string
    api_token?: string
    [key: string]: any
  }
  created_at?: string
  updated_at?: string
}

export const useAppStore = defineStore('app', () => {
  // State
  const isLoading = ref(false)
  const user = ref<User | null>(null)
  const apiToken = ref<string>('')
  const config = ref<any>(null)

  // Getters
  const hasApiToken = computed(() => {
    return !!(apiToken.value || user.value?.props?.api_token)
  })

  const currentApiToken = computed(() => {
    return apiToken.value || user.value?.props?.api_token || ''
  })

  const isInitialized = computed(() => {
    return !!user.value
  })

  // Actions
  async function initialize() {
    isLoading.value = true
    try {
      // Get app config
      config.value = await apiService.getConfig()
      
      // For now, simulate getting the default user
      // In production, this would check authentication
      user.value = {
        user_id: 'default-user-123',
        props: {
          name: 'Default User',
          email: 'user@example.com',
          // api_token will be null initially - user needs to set it
        }
      }
    } catch (error) {
      console.error('Failed to initialize app:', error)
    } finally {
      isLoading.value = false
    }
  }

  async function setApiToken(token: string) {
    apiToken.value = token
    
    // TODO: Save to user props in backend
    if (user.value) {
      user.value.props.api_token = token
    }
  }

  async function validateApiToken(token: string): Promise<boolean> {
    try {
      const status = await apiService.checkTokenStatus(token)
      return status.valid
    } catch (error) {
      console.error('Token validation failed:', error)
      return false
    }
  }

  return {
    // State
    isLoading,
    user,
    apiToken,
    config,
    
    // Getters
    hasApiToken,
    currentApiToken,
    isInitialized,
    
    // Actions
    initialize,
    setApiToken,
    validateApiToken
  }
})
