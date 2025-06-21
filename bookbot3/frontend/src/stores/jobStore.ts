import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiService } from '../services/api'
import type { Job } from '@/stores/types.ts' // Assuming you have a Job type defined, adjust if necessary

const POLLING_INTERVAL = 2000 // 2 seconds

export const useJobStore = defineStore('jobStore', () => {
  const globalRunningJobs = ref<Job[]>([])
  const allJobs = ref<Job[]>([]) // For JobsViewer
  const currentJobDetails = ref<Job | null>(null) // For JobDetailsViewer
  const currentJobLogs = ref<any[]>([]) // For JobLogsViewer
  const isLoading = ref(false) // For global running jobs
  const isJobsViewerLoading = ref(false) // For all jobs
  const isJobDetailsLoading = ref(false) // For job details
  const isJobLogsLoading = ref(false) // For job logs
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


  async function fetchAllJobs(bookId?: string, state?: string) {
    isJobsViewerLoading.value = true;
    error.value = null;
    try {
      const params: { book_id?: string; state?: string } = {};
      if (bookId) {
        params.book_id = bookId;
      }
      if (state) {
        params.state = state;
      }

      const response = await apiService.getAllJobs(params);
      allJobs.value = response.jobs || [];
    } catch (e: any) {
      console.error('Failed to fetch all jobs:', e);
      error.value = e.message || 'Failed to fetch jobs.';
    } finally {
      isJobsViewerLoading.value = false;
    }
  }

  async function fetchJobDetails(jobId: string) {
    isJobDetailsLoading.value = true;
    error.value = null;
    try {
      const response = await apiService.getJob(jobId);
      currentJobDetails.value = response;
      return response;
    } catch (e: any) {
      console.error('Failed to fetch job details:', e);
      error.value = e.message || 'Failed to fetch job details.';
      return null;
    } finally {
      isJobDetailsLoading.value = false;
    }
  }

  async function fetchJobLogs(jobId: string) {
    isJobLogsLoading.value = true;
    error.value = null;
    try {
      const response = await apiService.getJobLogs(jobId);
      // Handle both array format and {logs: [...]} format
      if (Array.isArray(response)) {
        currentJobLogs.value = response;
        return response;
      } else if (response && Array.isArray(response.logs)) {
        currentJobLogs.value = response.logs;
        return response.logs;
      } else {
        currentJobLogs.value = [];
        return [];
      }
    } catch (e: any) {
      console.error('Failed to fetch job logs:', e);
      error.value = e.message || 'Failed to fetch job logs.';
      return [];
    } finally {
      isJobLogsLoading.value = false;
    }
  }
  
  return {
    globalRunningJobs,
    allJobs,
    currentJobDetails,
    currentJobLogs,
    isLoading,
    isJobsViewerLoading,
    isJobDetailsLoading,
    isJobLogsLoading,
    error,
    fetchGlobalRunningJobs,
    fetchAllJobs,
    fetchJobDetails,
    fetchJobLogs,
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
