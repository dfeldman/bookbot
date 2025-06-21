import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ChunkVersionHistory from '../src/components/ChunkVersionHistory.vue'
import MarkdownEditor from '../src/components/MarkdownEditor.vue'
import { apiService } from '../src/services/api'

// Mock the API service
vi.mock('../src/services/api', () => ({
  apiService: {
    getChunkVersions: vi.fn(),
    getChunkVersion: vi.fn(),
    restoreChunkVersion: vi.fn()
  }
}))

// Mock the MarkdownEditor component
vi.mock('../src/components/MarkdownEditor.vue', () => ({
  default: {
    name: 'MarkdownEditor',
    props: ['modelValue', 'readonly', 'showToolbar', 'fontFamily', 'fontSize'],
    template: '<div class="mock-markdown-editor">{{ modelValue }}</div>'
  }
}))

describe('ChunkVersionHistory.vue', () => {
  const mockVersions = [
    {
      chunk_id: 'chunk-123',
      version: 3,
      is_latest: true,
      word_count: 150,
      created_at: '2025-06-20T10:00:00Z'
    },
    {
      chunk_id: 'chunk-123',
      version: 2,
      is_latest: false,
      word_count: 120,
      created_at: '2025-06-19T15:30:00Z'
    },
    {
      chunk_id: 'chunk-123',
      version: 1,
      is_latest: false,
      word_count: 100,
      created_at: '2025-06-18T09:45:00Z'
    }
  ]

  beforeEach(() => {
    // Reset mocks
    vi.resetAllMocks()
    
    // Setup default mock responses
    apiService.getChunkVersions.mockResolvedValue({ versions: mockVersions })
    apiService.getChunkVersion.mockResolvedValue({ text: 'Mock version content' })
    apiService.restoreChunkVersion.mockResolvedValue({})
  })

  it('loads versions on mount', async () => {
    // Set up the API mock to return our mock versions
    apiService.getChunkVersions.mockResolvedValue({ versions: mockVersions })

    const wrapper = mount(ChunkVersionHistory, {
      props: {
        chunkId: 'chunk-123',
        fontFamily: 'Arial',
        fontSize: '16px'
      },
      global: {
        stubs: {
          MarkdownEditor: true
        }
      }
    })
    
    // Wait for API calls to resolve
    await flushPromises()
    
    expect(apiService.getChunkVersions).toHaveBeenCalledWith('chunk-123')
    
    // Should display all versions
    const versionItems = wrapper.findAll('.version-item')
    expect(versionItems.length).toBe(3)
    
    // Should mark current version
    expect(versionItems[0].classes()).toContain('is-current')
    expect(versionItems[0].find('.badge').text()).toContain('Current')
  })

  it('loads version content when view button is clicked', async () => {
    // Set up API responses
    apiService.getChunkVersions.mockResolvedValue({ versions: mockVersions })
    apiService.getChunkVersion.mockResolvedValue({ text: 'Mock version content' })
    
    const wrapper = mount(ChunkVersionHistory, {
      props: {
        chunkId: 'chunk-123',
        fontFamily: 'Arial',
        fontSize: '16px'
      },
      global: {
        stubs: {
          MarkdownEditor: true
        }
      }
    })
    
    // Wait for initial versions to load
    await flushPromises()
    
    // Find and click the view button for version 2 (index 1 in the list)
    const viewButton = wrapper.findAll('.version-actions button')[0] // First view button in the list
    await viewButton.trigger('click')
    
    // Verify getChunkVersion was called with the right parameters
    // The second item in the list has version 2
    expect(apiService.getChunkVersion).toHaveBeenCalledWith('chunk-123', mockVersions[1].version)
    
    // Wait for the preview content to load
    await flushPromises()
    
    // Preview should be visible
    expect(wrapper.find('.version-preview').exists()).toBe(true)
  })

  it('restores a version when restore button is clicked', async () => {
    // Mock confirm to return true
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    
    // Set up API responses
    apiService.getChunkVersions.mockResolvedValue({ versions: mockVersions })
    apiService.restoreChunkVersion.mockResolvedValue({ success: true })
    
    const wrapper = mount(ChunkVersionHistory, {
      props: {
        chunkId: 'chunk-123',
        fontFamily: 'Arial',
        fontSize: '16px'
      },
      global: {
        stubs: {
          MarkdownEditor: true
        }
      }
    })
    
    // Wait for initial versions to load
    await flushPromises()
    
    // Find and click the restore button for version 2 (non-latest version)
    const versionItems = wrapper.findAll('.version-item')
    // The restore button should be in the second version item (index 1)
    // and it's the button with text 'Restore'
    const restoreButton = versionItems[1].find('.restore-button')
    await restoreButton.trigger('click')
    
    expect(confirmSpy).toHaveBeenCalled()
    
    // Verify restoreChunkVersion was called with the right parameters
    expect(apiService.restoreChunkVersion).toHaveBeenCalledWith('chunk-123', mockVersions[1].version)
    
    // Wait for the restore operation to complete
    await flushPromises()
    
    // Should emit restored event
    expect(wrapper.emitted().restored).toBeTruthy()
    expect(wrapper.emitted().restored[0]).toEqual(['chunk-123'])
    
    confirmSpy.mockRestore()
  })

  it('shows error message when API call fails', async () => {
    // Mock API error
    apiService.getChunkVersions.mockRejectedValue(new Error('API Error'))
    
    const wrapper = mount(ChunkVersionHistory, {
      props: {
        chunkId: 'chunk-123',
        fontFamily: 'Arial',
        fontSize: '16px'
      },
      global: {
        stubs: {
          MarkdownEditor: true
        }
      }
    })
    
    // Wait for API call to fail
    await flushPromises()
    
    // Error should be displayed
    expect(wrapper.find('.error').exists()).toBe(true)
    expect(wrapper.find('.error p').text()).toBe('API Error')
    
    // Should show retry button
    const retryButton = wrapper.find('.retry-button')
    expect(retryButton.exists()).toBe(true)
    
    // Mock API success for retry
    apiService.getChunkVersions.mockResolvedValue({ versions: mockVersions })
    
    // Click retry
    await retryButton.trigger('click')
    await flushPromises()
    
    // After successful retry, error should be gone and versions should be shown
    expect(apiService.getChunkVersions).toHaveBeenCalledTimes(2)
    expect(wrapper.find('.error').exists()).toBe(false)
    expect(wrapper.findAll('.version-item').length).toBe(3)
  })

  it('closes when close button is clicked', async () => {
    // Set up API responses
    apiService.getChunkVersions.mockResolvedValue({ versions: mockVersions })
    
    const wrapper = mount(ChunkVersionHistory, {
      props: {
        chunkId: 'chunk-123',
        fontFamily: 'Arial',
        fontSize: '16px'
      },
      global: {
        stubs: {
          MarkdownEditor: true
        }
      }
    })
    
    // Wait for initial versions to load
    await flushPromises()
    
    // Find and click close button (should be in the header)
    const closeButton = wrapper.find('.header .close-button')
    await closeButton.trigger('click')
    
    // Should emit close event
    expect(wrapper.emitted().close).toBeTruthy()
  })

  it('toggles preview when clicking the same version twice', async () => {
    // Set up API responses
    apiService.getChunkVersions.mockResolvedValue({ versions: mockVersions })
    apiService.getChunkVersion.mockResolvedValue({ text: 'Mock version content' })
    
    const wrapper = mount(ChunkVersionHistory, {
      props: {
        chunkId: 'chunk-123',
        fontFamily: 'Arial',
        fontSize: '16px'
      },
      global: {
        stubs: {
          MarkdownEditor: true
        }
      }
    })
    
    // Wait for initial versions to load
    await flushPromises()
    
    // Find and click view button for first non-latest version
    const viewButtons = wrapper.findAll('.view-button')
    await viewButtons[0].trigger('click')
    
    // Wait for content to load
    await flushPromises()
    
    // Preview should be visible
    expect(wrapper.find('.version-preview').exists()).toBe(true)
    
    // Click the same view button again to close preview
    await viewButtons[0].trigger('click')
    
    // Wait for reactivity to update
    await flushPromises()
    
    // Preview should now be gone
    expect(wrapper.find('.version-preview').exists()).toBe(false)
  })
})
