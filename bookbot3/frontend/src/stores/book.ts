import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService } from '../services/api'
import { useJobStore } from './jobStore'
import type { Job, Book, Chunk, ContextData } from './types'

export const useBookStore = defineStore('book', () => {
  const jobStore = useJobStore() // Get instance of jobStore
  // State
  const books = ref<Book[]>([])
  const currentBook = ref<Book | null>(null)
  const chunks = ref<Chunk[]>([])
  const jobs = ref<Job[]>([])
  const bots = ref<Chunk[]>([])
  const currentJob = ref<Job | null>(null)
  const isLoading = ref(false)
  const sceneContext = ref<ContextData | null>(null)
  const isContextLoading = ref(false)
  const contextError = ref<string | null>(null)

  const versions = ref<Chunk[]>([])
  const isVersionsLoading = ref(false)
  const versionsError = ref<string | null>(null)

  // Getters
  const hasBooks = computed(() => books.value.length > 0)
  const isGenerating = computed(() => {
    return jobs.value.some(job => job.job_type === 'GenerateChunk' && (job.state === 'running' || job.state === 'waiting'))
  })

  // Actions
  async function loadBooks() {
    isLoading.value = true
    try {
      const response = await apiService.getBooks()
      books.value = response.books
    } catch (error) {
      console.error('Failed to load books:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function createBook(bookData: {
    name: string
    description: string
    style: string
  }): Promise<Book> {
    isLoading.value = true
    try {
      const book = await apiService.createBook({
        props: {
          name: bookData.name,
          description: bookData.description,
          style: bookData.style,
          genre: 'General', // Default genre
          created_via: 'wizard'
        }
      })
      
      books.value.push(book)
      currentBook.value = book
      return book
    } catch (error) {
      console.error('Failed to create book:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function startCreateFoundationJob(bookId: string): Promise<Job> {
    try {
      // Get the book to access its props
      const book = await apiService.getBook(bookId)
      
      const jobPayload = {
        job_type: 'create_foundation',
        props: {
          brief: book.props.description || 'Generate a complete book foundation',
          style: book.props.style || 'professional'
        }
      };
      const job = await apiService.createJob(bookId, jobPayload);
      
      // Immediately after job creation is successful, trigger the indicator
      jobStore.triggerStartingIndicator();
      
      // Add the job to the jobs array
      jobs.value.push(job);
      currentJob.value = job;

    // Lock the book in the store
    const bookInStore = books.value.find(b => b.book_id === bookId);
    if (bookInStore) {
      bookInStore.is_locked = true;
    }
    if (currentBook.value && currentBook.value.book_id === bookId) {
      currentBook.value.is_locked = true;
    }

    return job;
    } catch (error) {
      console.error('Failed to start CreateFoundation job:', error)
      throw error
    }
  }

  async function pollJobStatus(jobId: string): Promise<Job> {
    try {
      const job = await apiService.getJob(jobId)
      
      // Update the job in the jobs array
      const index = jobs.value.findIndex(j => j.job_id === job.job_id)
      if (index !== -1) {
        jobs.value[index] = job
      }
      
      currentJob.value = job

    // If job is finished, unlock the book
    // Assuming job object from apiService.getJob uses states like 'completed', 'failed', 'cancelled'
    if (job.state === 'completed' || job.state === 'failed' || job.state === 'cancelled') {
      const bookToUnlock = books.value.find(b => b.book_id === job.book_id);
      if (bookToUnlock) {
        bookToUnlock.is_locked = false;
      }
      if (currentBook.value && currentBook.value.book_id === job.book_id) {
        currentBook.value.is_locked = false;
        if (job.state === 'completed') {
          // Refresh book details and chunks for the currently viewed book
          // This ensures that if the user is looking at the book when the job finishes,
          // the new chunks (e.g., foundation) are loaded.
          console.log(`Job ${job.job_id} completed for current book ${job.book_id}. Reloading book and chunks.`);
          loadBook(job.book_id); // Reload book metadata
          loadChunks(job.book_id); // Reload chunks
        }
      }
    }
    return job
    } catch (error) {
      console.error('Failed to poll job status:', error)
      throw error
    }
  }

  async function loadBook(bookId: string): Promise<Book> {
    try {
      const book = await apiService.getBook(bookId)
      currentBook.value = book
      return book
    } catch (error) {
      console.error('Failed to load book:', error)
      throw error
    }
  }

  async function loadChunks(bookId: string): Promise<Chunk[]> {
    try {
      const response = await apiService.getChunks(bookId)
      chunks.value = response.chunks
      return response.chunks
    } catch (error) {
      console.error('Failed to load chunks:', error)
      throw error
    }
  }

  async function loadJobs(bookId: string): Promise<Job[]> {
    try {
      const response = await apiService.getJobs(bookId)
      jobs.value = response.jobs
      return response.jobs
    } catch (error) {
      console.error('Failed to load jobs:', error)
      throw error
    }
  }

  async function loadChunk(chunkId: string): Promise<Chunk> {
    try {
      const chunk = await apiService.getChunk(chunkId)
      return chunk
    } catch (error) {
      console.error('Failed to load chunk:', error)
      throw error
    }
  }

  function updateChunkInStore(updatedChunk: Chunk) {
    const index = chunks.value.findIndex(c => c.chunk_id === updatedChunk.chunk_id)
    if (index !== -1) {
      chunks.value[index] = updatedChunk
    }
  }

  function clearCurrentBook() {
    currentBook.value = null
    currentJob.value = null
    sceneContext.value = null
    contextError.value = null
    bots.value = []
    versions.value = []
  }

  async function loadBots(bookId: string) {
    try {
      const response = await apiService.getChunks(bookId, { type: 'bot' })
      bots.value = response.chunks
    } catch (error) {
      console.error('Failed to load bots:', error)
    }
  }

    async function fetchSceneContext(chunkId: string) {
    if (!currentBook.value) {
      contextError.value = 'Cannot fetch context without a loaded book.'
      console.error(contextError.value)
      return
    }
    isContextLoading.value = true
    contextError.value = null
    try {
      const context = await apiService.getChunkContext(currentBook.value.book_id, chunkId)
      sceneContext.value = context
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      console.error(`Failed to fetch scene context for chunk ${chunkId}:`, message)
      contextError.value = 'Failed to load scene context. Please try again.'
    } finally {
      isContextLoading.value = false
    }
  }

    async function cancelGeneration(jobId: string) {
    try {
      await apiService.cancelJob(jobId)
      const job = jobs.value.find(j => j.job_id === jobId)
      if (job) {
        job.state = 'cancelled'
      }
    } catch (error) {
      console.error(`Failed to cancel job ${jobId}:`, error)
    }
  }

  async function startGenerateChunkJob(chunkId: string, placeholderValues: Record<string, string>): Promise<Job> {
    try {
      const chunk = await apiService.getChunk(chunkId);
      const bookId = chunk.book_id;

      const jobPayload = {
        job_type: 'GenerateChunk',
        props: {
          task_chunk_id: chunkId,
          placeholder_values: placeholderValues,
        }
      };
      const job = await apiService.createJob(bookId, jobPayload);
      
      jobStore.triggerStartingIndicator();
      jobs.value.push(job);
      currentJob.value = job;

      return job;
    } catch (error) {
      console.error('Failed to start GenerateChunk job:', error);
      throw error;
    }
  }

  async function startSceneGeneration(chunkId: string, botId: string, mode: string, options: Record<string, any>): Promise<Job> {
    try {
      const chunk = await apiService.getChunk(chunkId);
      const bookId = chunk.book_id;

      const jobPayload = {
        job_type: 'GenerateChunk',
        props: {
          input_chunk_id: chunkId,
          bot_chunk_id: botId,
          mode: mode,
          ...options
        }
      };
      const job = await apiService.createJob(bookId, jobPayload);
      
      jobStore.triggerStartingIndicator();
      jobs.value.push(job);
      currentJob.value = job;

      return job;
    } catch (error) {
      console.error('Failed to start scene generation job:', error);
      throw error;
    }
  }

  async function fetchVersions(chunkId: string) {
    isVersionsLoading.value = true
    versionsError.value = null
    try {
      const response = await apiService.getChunkVersions(chunkId)
      versions.value = response.versions
    } catch (error) {
      console.error(`Failed to fetch versions for chunk ${chunkId}:`, error)
      versionsError.value = 'Failed to load version history.'
    } finally {
      isVersionsLoading.value = false
    }
  }

  async function restoreChunkVersion(chunkId: string, version: number) {
    try {
      const restoredChunk = await apiService.restoreChunkVersion(chunkId, version)
      updateChunkInStore(restoredChunk)
      await fetchVersions(chunkId)
    } catch (error) {
      console.error(`Failed to restore version ${version} for chunk ${chunkId}:`, error)
      throw error
    }
  }

  async function deleteChunk(chunkId: string) {
    try {
      await apiService.deleteChunk(chunkId)
      // Remove the chunk from the local store if it exists
      if (currentBook.value && currentBook.value.chunks) {
        const index = currentBook.value.chunks.findIndex(c => c.chunk_id === chunkId)
        if (index !== -1) {
          currentBook.value.chunks.splice(index, 1)
        }
      }
    } catch (error) {
      console.error(`Failed to delete chunk ${chunkId}:`, error)
      throw error
    }
  }

  return {
    // State
    books,
    currentBook,
    currentJob,
    isLoading,
    chunks,
    jobs,
    bots,
    sceneContext,
    isContextLoading,
    contextError,
    versions,
    isVersionsLoading,
    versionsError,
    
    // Getters
    hasBooks,
    isGenerating,
    
    // Actions
    loadBooks,
    createBook,
    startCreateFoundationJob,
    pollJobStatus,
    loadBook,
    loadChunks,
    loadJobs,
    loadChunk,
    clearCurrentBook,
    updateChunkInStore,
    startGenerateChunkJob,
    fetchSceneContext,
    loadBots,
    cancelGeneration,
    startSceneGeneration,
    fetchVersions,
    restoreChunkVersion,
    deleteChunk
  }
})
