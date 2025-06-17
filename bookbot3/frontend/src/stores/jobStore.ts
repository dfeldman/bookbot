import { defineStore } from 'pinia'
import { ref, onUnmounted } from 'vue'
import { apiService } from '../services/api'
import type { Job } from '@/stores/types.ts' // Assuming you have a Job type defined, adjust if necessary

const POLLING_INTERVAL = 10000 // 10 seconds

export const useJobStore = defineStore('jobStore', () => {
  const globalRunningJobs = ref<Job[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const showStartingIndicator = ref(false)
  let pollIntervalId: number | null = null

  async function fetchGlobalRunningJobs() {
    isLoading.value = true
    error.value = null
    try {
      const response = await apiService.getRunningJobs()
      globalRunningJobs.value = response.jobs || []
    } catch (e: any) {
      console.error('Failed to fetch global running jobs:', e)
      error.value = e.message || 'Failed to fetch running jobs.'
      // Optionally, clear jobs on error or keep stale data
      // globalRunningJobs.value = [] 
    } finally {
      isLoading.value = false
    }
  }

  function startPolling(interval: number = POLLING_INTERVAL) {
    stopPolling() // Clear existing interval if any
    fetchGlobalRunningJobs() // Initial fetch
    pollIntervalId = window.setInterval(fetchGlobalRunningJobs, interval)
    document.addEventListener('visibilitychange', handleVisibilityChange)
  }

  function stopPolling() {
    if (pollIntervalId !== null) {
      window.clearInterval(pollIntervalId)
      pollIntervalId = null
    }
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  }

  function handleVisibilityChange() {
    if (document.hidden) {
      // If page is hidden, you might want to stop polling or reduce frequency
      // For simplicity, we'll keep polling but this is a place for optimization
      // console.log('Page hidden, polling continues for now.')
    } else {
      // Page is visible, fetch immediately to refresh data
      fetchGlobalRunningJobs()
    }
  }
  
  // Cleanup when the store instance is effectively unmounted
  // This happens if the component using it is unmounted and no other component is using this store instance.
  // Pinia's setup stores are singleton by default, so this onUnmounted might not behave as expected
  // for global cleanup unless managed carefully (e.g. called from App.vue or a global setup).
  // A more robust approach for a truly global store is to manage polling lifecycle explicitly from App.vue or StatusBar.vue.
  onUnmounted(() => {
    // stopPolling() // Consider if this is the right place or if StatusBar should manage it
  })

  return {
    globalRunningJobs,
    isLoading,
    error,
    fetchGlobalRunningJobs,
    startPolling,
    stopPolling,
    showStartingIndicator, // Expose the new state
    triggerStartingIndicator // Expose the new action
  }

  function triggerStartingIndicator() {
    showStartingIndicator.value = true
    setTimeout(() => {
      showStartingIndicator.value = false
    }, 1000) // Indicator lasts for 1 second
  }
})
