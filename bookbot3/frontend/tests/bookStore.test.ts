import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBookStore } from '@/stores/book'
import { apiService } from '@/services/api'

// Mock the API service
vi.mock('@/services/api', () => ({
  apiService: {
    getBooks: vi.fn(),
    getBook: vi.fn(),
    getChunks: vi.fn(),
    getJobs: vi.fn(),
    getChunk: vi.fn(),
    createBook: vi.fn(),
    createJob: vi.fn(),
    getJob: vi.fn(),
    updateChunk: vi.fn(),
    deleteJob: vi.fn(),
  }
}))

describe('Book Store', () => {
  let bookStore: any

  const mockBook = {
    book_id: '1',
    user_id: 'user1',
    props: {
      name: 'Test Book',
      description: 'A test book',
      style: 'adventure',
      genre: 'fantasy'
    },
    is_locked: false,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
    chunk_count: 5,
    word_count: 1000
  }

  const mockChunks = [
    {
      chunk_id: '1',
      book_id: '1',
      type: 'scene',
      chapter: 1,
      order: 1,
      word_count: 500,
      version: 1,
      is_locked: false,
      is_deleted: false,
      is_latest: true,
      text: 'Scene content',
      props: {
        name: 'Chapter 1',
        scene_title: 'Opening Scene'
      },
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z'
    }
  ]

  const mockJobs = [
    {
      job_id: 'job-1',
      book_id: '1',
      job_type: 'generate_text',
      state: 'running' as const,
      props: {
        chunk_id: '1',
        mode: 'write'
      },
      started_at: '2023-01-01T00:00:00Z',
      created_at: '2023-01-01T00:00:00Z'
    }
  ]

  beforeEach(() => {
    setActivePinia(createPinia())
    bookStore = useBookStore()
    
    // Reset mocks
    vi.clearAllMocks()
    
    // Mock API responses
    vi.mocked(apiService.getBooks).mockResolvedValue({ books: [mockBook] })
    vi.mocked(apiService.getBook).mockResolvedValue(mockBook)
    vi.mocked(apiService.getChunks).mockResolvedValue({ chunks: mockChunks })
    vi.mocked(apiService.getJobs).mockResolvedValue({ jobs: mockJobs })
    vi.mocked(apiService.getChunk).mockResolvedValue(mockChunks[0])
    vi.mocked(apiService.createBook).mockResolvedValue(mockBook)
    vi.mocked(apiService.createJob).mockResolvedValue({
      job_id: 'new-job-123',
      book_id: '1',
      job_type: 'create_foundation',
      state: 'waiting',
      created_at: new Date().toISOString()
    })
  })

  describe('Initial State', () => {
    it('has correct initial state', () => {
      expect(bookStore.currentBook).toBeNull()
      expect(bookStore.books).toEqual([])
      expect(bookStore.chunks).toEqual([])
      expect(bookStore.jobs).toEqual([])
      expect(bookStore.currentJob).toBeNull()
      expect(bookStore.isLoading).toBe(false)
      expect(bookStore.hasBooks).toBe(false)
    })
  })

  describe('Books Management', () => {
    it('loads books successfully', async () => {
      await bookStore.loadBooks()
      
      expect(apiService.getBooks).toHaveBeenCalled()
      expect(bookStore.books).toEqual([mockBook])
      expect(bookStore.hasBooks).toBe(true)
      expect(bookStore.isLoading).toBe(false)
    })

    it('sets loading state during book loading', async () => {
      const loadPromise = bookStore.loadBooks()
      
      expect(bookStore.isLoading).toBe(true)
      
      await loadPromise
      
      expect(bookStore.isLoading).toBe(false)
    })

    it('handles book loading errors', async () => {
      const error = new Error('Failed to load books')
      vi.mocked(apiService.getBooks).mockRejectedValue(error)
      
      await expect(bookStore.loadBooks()).rejects.toThrow('Failed to load books')
      expect(bookStore.isLoading).toBe(false)
    })

    it('creates a new book', async () => {
      const bookData = {
        name: 'New Book',
        description: 'A new test book',
        style: 'mystery'
      }

      const result = await bookStore.createBook(bookData)
      
      expect(apiService.createBook).toHaveBeenCalledWith({
        props: {
          name: 'New Book',
          description: 'A new test book',
          style: 'mystery',
          genre: 'General',
          created_via: 'wizard'
        }
      })
      expect(result).toEqual(mockBook)
      expect(bookStore.books).toEqual([mockBook]) // Changed from toContain to toEqual since we start with empty array
    })
  })

  describe('Book Loading', () => {
    it('loads book data successfully', async () => {
      const result = await bookStore.loadBook('1')
      
      expect(apiService.getBook).toHaveBeenCalledWith('1')
      expect(bookStore.currentBook).toEqual(mockBook)
      expect(result).toEqual(mockBook)
    })

    it('handles book loading errors', async () => {
      const error = new Error('Failed to load book')
      vi.mocked(apiService.getBook).mockRejectedValue(error)
      
      await expect(bookStore.loadBook('1')).rejects.toThrow('Failed to load book')
    })

    it('clears current book', () => {
      bookStore.currentBook = mockBook
      bookStore.currentJob = mockJobs[0]
      
      bookStore.clearCurrentBook()
      
      expect(bookStore.currentBook).toBeNull()
      expect(bookStore.currentJob).toBeNull()
    })
  })

  describe('Chunks Management', () => {
    it('loads chunks for a book', async () => {
      const result = await bookStore.loadChunks('1')
      
      expect(apiService.getChunks).toHaveBeenCalledWith('1')
      expect(bookStore.chunks).toEqual(mockChunks)
      expect(result).toEqual(mockChunks)
    })

    it('handles chunk loading errors', async () => {
      const error = new Error('Failed to load chunks')
      vi.mocked(apiService.getChunks).mockRejectedValue(error)
      
      await expect(bookStore.loadChunks('1')).rejects.toThrow('Failed to load chunks')
    })

    it('loads a single chunk', async () => {
      const result = await bookStore.loadChunk('1')
      
      expect(apiService.getChunk).toHaveBeenCalledWith('1')
      expect(result).toEqual(mockChunks[0])
    })
  })

  describe('Jobs Management', () => {
    it('loads jobs for a book', async () => {
      const result = await bookStore.loadJobs('1')
      
      expect(apiService.getJobs).toHaveBeenCalledWith('1')
      expect(bookStore.jobs).toEqual(mockJobs)
      expect(result).toEqual(mockJobs)
    })

    it('handles job loading errors', async () => {
      const error = new Error('Failed to load jobs')
      vi.mocked(apiService.getJobs).mockRejectedValue(error)
      
      await expect(bookStore.loadJobs('1')).rejects.toThrow('Failed to load jobs')
    })

    it('starts create foundation job', async () => {
      // First need to mock getBook call since startCreateFoundationJob calls it
      vi.mocked(apiService.getBook).mockResolvedValue(mockBook)
      
      const result = await bookStore.startCreateFoundationJob('1')
      
      expect(apiService.getBook).toHaveBeenCalledWith('1')
      expect(apiService.createJob).toHaveBeenCalledWith('1', {
        job_type: 'create_foundation',
        props: {
          brief: 'A test book',
          style: 'adventure'
        }
      })
      expect(bookStore.currentJob).toBeDefined()
      expect(result).toBeDefined()
    })

    it('polls job status', async () => {
      const mockJobUpdate = {
        ...mockJobs[0],
        state: 'complete' as const,
        completed_at: new Date().toISOString()
      }
      
      vi.mocked(apiService.getJob).mockResolvedValue(mockJobUpdate)
      
      const result = await bookStore.pollJobStatus('job-1')
      
      expect(apiService.getJob).toHaveBeenCalledWith('job-1')
      expect(bookStore.currentJob).toEqual(mockJobUpdate)
      expect(result).toEqual(mockJobUpdate)
    })
  })
})
