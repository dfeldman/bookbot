import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import ChunkVersionHistory from '../src/components/ChunkVersionHistory.vue'
import { apiService } from '../src/services/api'

// Mock apiService methods
vi.mock('../src/services/api', () => {
  return {
    apiService: {
      getChunkVersions: vi.fn(),
      getChunkVersion: vi.fn(),
      restoreChunkVersion: vi.fn()
    }
  }
})

// Mock window.confirm
vi.spyOn(window, 'confirm').mockImplementation(() => true)

// Helper function to create wrapper with props
const createWrapper = (props = {}) => {
  return mount(ChunkVersionHistory, {
    props: {
      chunkId: 'chunk-123',
      fontFamily: 'serif',
      fontSize: '16px',
      ...props
    },
    global: {
      stubs: {
        MarkdownEditor: {
          template: '<div class="markdown-editor-stub">{{ modelValue }}</div>',
          props: ['modelValue', 'readonly', 'placeholder', 'showToolbar', 'fontFamily', 'fontSize']
        }
      }
    }
  })
}

describe('ChunkVersionHistory.vue', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('shows loading state initially', async () => {
    // Set up a ref to resolve the promise manually
    let resolvePromise;
    apiService.getChunkVersions.mockImplementation(() => new Promise((resolve) => {
      resolvePromise = resolve;
    }))
    
    const wrapper = createWrapper()
    await nextTick() // Wait for initial render
    
    // Check loading state
    expect(wrapper.find('.loading').exists()).toBe(true)
    expect(wrapper.text()).toContain('Loading version history')
    
    // Cleanup - resolve the promise to avoid hanging test
    resolvePromise({ versions: [] })
  })

  it('loads versions when mounted', async () => {
    // Mock API response
    const mockVersions = [
      { 
        version: 3, 
        created_at: '2023-05-20T10:30:00Z', 
        word_count: 500, 
        is_latest: true 
      },
      { 
        version: 2, 
        created_at: '2023-05-19T15:45:00Z', 
        word_count: 450, 
        is_latest: false 
      },
      { 
        version: 1, 
        created_at: '2023-05-18T08:15:00Z', 
        word_count: 400, 
        is_latest: false 
      }
    ]
    
    apiService.getChunkVersions.mockResolvedValue({ versions: mockVersions })
    
    const wrapper = createWrapper()
    await flushPromises() // Wait for API promises to resolve
    
    // Check that API was called
    expect(apiService.getChunkVersions).toHaveBeenCalledWith('chunk-123')
    
    // Check that versions are displayed
    const versionItems = wrapper.findAll('.version-item')
    expect(versionItems.length).toBe(3)
    
    // Check content of each version item
    expect(wrapper.find('.current-badge').exists()).toBe(true)
    expect(wrapper.find('.current-badge').text()).toContain('Current')
    expect(wrapper.text()).toContain('words')
  })

  it('handles loading error', async () => {
    // Mock API error
    apiService.getChunkVersions.mockRejectedValue(new Error('Failed to load versions'))
    
    const wrapper = createWrapper()
    await flushPromises() // Wait for API promises to resolve
    
    // Check that error is displayed
    expect(wrapper.find('.error').exists()).toBe(true)
    expect(wrapper.text()).toContain('Failed to load versions')
    
    // Test retry functionality
    apiService.getChunkVersions.mockResolvedValue({ versions: [] })
    
    await wrapper.find('.retry-button').trigger('click')
    await flushPromises()
    
    expect(apiService.getChunkVersions).toHaveBeenCalledTimes(2)
    expect(wrapper.find('.error').exists()).toBe(false)
  })

  it('displays version preview when view button is clicked', async () => {
    // Mock API responses
    const mockVersions = [
      { version: 2, created_at: '2023-05-19T15:45:00Z', word_count: 450, is_latest: false },
      { version: 1, created_at: '2023-05-18T08:15:00Z', word_count: 400, is_latest: false }
    ]
    
    const mockVersionContent = {
      text: 'This is version 2 content',
      version: 2
    }
    
    apiService.getChunkVersions.mockResolvedValue({ versions: mockVersions })
    apiService.getChunkVersion.mockResolvedValue(mockVersionContent)
    
    const wrapper = createWrapper()
    await flushPromises() // Wait for versions to load
    
    // Click on view button
    await wrapper.find('.view-button').trigger('click')
    await flushPromises() // Wait for version content to load
    
    // Check that the correct API call was made
    expect(apiService.getChunkVersion).toHaveBeenCalledWith('chunk-123', 2)
    
    // Check that preview is displayed with correct content
    expect(wrapper.find('.version-preview').exists()).toBe(true)
    expect(wrapper.find('.markdown-editor-stub').exists()).toBe(true)
    expect(wrapper.text()).toContain('Preview of Version 2')
  })

  it('restores a version when restore button is clicked', async () => {
    // Mock API responses
    const mockVersions = [
      { version: 2, created_at: '2023-05-19T15:45:00Z', word_count: 450, is_latest: false },
      { version: 1, created_at: '2023-05-18T08:15:00Z', word_count: 400, is_latest: false }
    ]
    
    apiService.getChunkVersions.mockResolvedValue({ versions: mockVersions })
    apiService.restoreChunkVersion.mockResolvedValue({ version: 3 })
    
    // Setup spy directly on window.confirm that actually returns true
    // This MUST happen before component is mounted
    const confirmSpy = vi.spyOn(window, 'confirm').mockImplementation(() => true)
    
    try {
      const wrapper = createWrapper()
      await flushPromises() // Wait for versions to load
      
      // Verify versions loaded correctly
      expect(wrapper.findAll('.version-item').length).toBe(2)
      
      // Find and click the first restore button (for version 2)
      const restoreButton = wrapper.find('.restore-button')
      expect(restoreButton.exists()).toBe(true)
      await restoreButton.trigger('click')
      
      // Wait for all promises to resolve after the click
      await nextTick()
      await flushPromises()
      
      // Confirm that our mock was called
      expect(confirmSpy).toHaveBeenCalled()
      
      // Now the apiService.restoreChunkVersion should have been called
      expect(apiService.restoreChunkVersion).toHaveBeenCalledWith('chunk-123', 2)
      
      // Check that a restored event was emitted
      expect(wrapper.emitted('restored')).toBeTruthy()
      expect(wrapper.emitted('restored')[0]).toEqual(['chunk-123'])
    } finally {
      // Restore the original spy
      confirmSpy.mockRestore()
    }
  })

  it('emits close event when close button is clicked', async () => {
    apiService.getChunkVersions.mockResolvedValue({ versions: [] })
    
    const wrapper = createWrapper()
    await flushPromises()
    
    await wrapper.find('.close-button').trigger('click')
    
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('formats dates correctly', async () => {
    // Mock API response with a specific date
    const mockVersions = [
      { 
        version: 1, 
        created_at: '2023-05-18T08:15:30Z', 
        word_count: 400,
        is_latest: false
      }
    ]
    
    apiService.getChunkVersions.mockResolvedValue({ versions: mockVersions })
    
    const wrapper = createWrapper()
    await flushPromises()
    
    // Check that the timestamp element exists and contains date information
    const timestamp = wrapper.find('.timestamp')
    expect(timestamp.exists()).toBe(true)
    
    // The exact format might vary depending on locale, but should contain these parts
    const text = timestamp.text()
    expect(text).toMatch(/\d{4}/) // Should contain year in 4 digits
  })
})
