import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import BotManager from '@/components/BotManager.vue'
import { useBookStore } from '@/stores/book'
import { apiService } from '@/services/api'

// Mock the API service
vi.mock('@/services/api', () => ({
  apiService: {
    getChunks: vi.fn(),
    createChunk: vi.fn(),
    updateChunk: vi.fn(),
    deleteChunk: vi.fn(),
  }
}))

// Mock vue-router
vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: {
      bookId: '1'
    }
  }),
  useRouter: () => ({
    push: vi.fn()
  })
}))

describe('BotManager', () => {
  let wrapper: any
  let bookStore: any

  beforeEach(() => {
    setActivePinia(createPinia())
    bookStore = useBookStore()
    
    // Mock API responses
    vi.mocked(apiService.getChunks).mockResolvedValue({ chunks: [] })

    wrapper = mount(BotManager, {
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