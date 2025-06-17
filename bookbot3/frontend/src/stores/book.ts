import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService } from '../services/api'
import { useJobStore } from './jobStore' // Import jobStore

export interface Book {
  book_id: string
  user_id: string
  props: {
    name?: string
    description?: string
    style?: string
    genre?: string
    [key: string]: any
  }
  is_locked: boolean
  job?: string
  created_at: string
  updated_at: string
  chunk_count?: number
  word_count?: number
}

export interface Chunk {
  chunk_id: string
  book_id: string
  type: string
  chapter: number | null
  order: number
  word_count: number
  version: number
  is_locked: boolean
  is_deleted: boolean
  is_latest: boolean
  text?: string  // Optional text content, available when include_text=true
  props: {
    name?: string
    scene_id?: string
    scene_title?: string
    chapter_title?: string
    tags?: string[]
    [key: string]: any
  }
  created_at: string
  updated_at: string
}

export interface Job {
  job_id: string
  book_id: string
  job_type: string
  state: 'waiting' | 'running' | 'complete' | 'error' | 'cancelled'
  props?: any
  started_at?: string
  completed_at?: string
  created_at: string
  updated_at?: string
}

export const useBookStore = defineStore('book', () => {
  const jobStore = useJobStore() // Get instance of jobStore
  // State
  const books = ref<Book[]>([])
  const currentBook = ref<Book | null>(null)
  const chunks = ref<Chunk[]>([])
  const jobs = ref<Job[]>([])
  const currentJob = ref<Job | null>(null)
  const isLoading = ref(false)

  // Getters
  const hasBooks = computed(() => books.value.length > 0)

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

  function clearCurrentBook() {
    currentBook.value = null
    currentJob.value = null
  }

  return {
    // State
    books,
    currentBook,
    currentJob,
    isLoading,
    chunks,
    jobs,
    
    // Getters
    hasBooks,
    
    // Actions
    loadBooks,
    createBook,
    startCreateFoundationJob,
    pollJobStatus,
    loadBook,
    loadChunks,
    loadJobs,
    loadChunk,
    clearCurrentBook
  }
})
