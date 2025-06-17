import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import GenerateChunkText from '@/components/GenerateChunkText.vue'
import { useBookStore } from '@/stores/book'
import { apiService } from '@/services/api'

// Mock the API service
vi.mock('@/services/api', () => ({
  apiService: {
    createJob: vi.fn(),
    getJob: vi.fn(),
  }
}))

// Mock vue-router
vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: {
      bookId: '1',
      chunkId: '1'
    }
  }),
  useRouter: () => ({
    push: vi.fn()
  })
}))

describe('GenerateChunkText', () => {
  let wrapper: any
  let bookStore: any

  beforeEach(() => {
    setActivePinia(createPinia())
    bookStore = useBookStore()
    
    // Mock API responses
    vi.mocked(apiService.createJob).mockResolvedValue({
      job_id: 'job-123',
      book_id: '1',
      job_type: 'generate_text',
      state: 'waiting',
      created_at: new Date().toISOString()
    })

    wrapper = mount(GenerateChunkText, {
      props: {
        chunkId: '1',
        bookId: '1'
      },
      global: {
        plugins: [createPinia()],
      }
    })
  })

  describe('Component Rendering', () => {
    it('renders correctly', () => {
      expect(wrapper.exists()).toBe(true)
    })
  })
})