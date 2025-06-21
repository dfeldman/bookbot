import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import { apiService } from '../src/services/api'

// Mock axios
vi.mock('axios', () => {
  return {
    default: {
      create: vi.fn(() => ({
        get: vi.fn(),
        put: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() }
        }
      }))
    }
  }
})

describe('API Service - Chunk Version History Methods', () => {
  let mockAxios

  beforeEach(() => {
    mockAxios = {
      get: vi.fn(),
      put: vi.fn()
    }
    
    // Set up the mocked axios instance
    apiService.api = mockAxios
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('getChunkVersions', () => {
    it('fetches the list of versions for a chunk', async () => {
      const mockVersions = [
        { chunk_id: 'chunk-123', version: 3, created_at: '2025-06-20T10:00:00Z', is_latest: true },
        { chunk_id: 'chunk-123', version: 2, created_at: '2025-06-19T15:00:00Z', is_latest: false },
        { chunk_id: 'chunk-123', version: 1, created_at: '2025-06-18T09:00:00Z', is_latest: false }
      ]
      
      mockAxios.get.mockResolvedValue({ data: { versions: mockVersions } })
      
      const result = await apiService.getChunkVersions('chunk-123')
      
      expect(mockAxios.get).toHaveBeenCalledWith('/chunks/chunk-123/versions')
      expect(result).toEqual({ versions: mockVersions })
    })

    it('handles errors when fetching versions', async () => {
      mockAxios.get.mockRejectedValue(new Error('Failed to fetch versions'))
      
      await expect(apiService.getChunkVersions('chunk-123')).rejects.toThrow('Failed to fetch versions')
      expect(mockAxios.get).toHaveBeenCalledWith('/chunks/chunk-123/versions')
    })
  })

  describe('getChunkVersion', () => {
    it('fetches a specific version of a chunk', async () => {
      const mockChunk = {
        chunk_id: 'chunk-123',
        version: 2,
        text: 'Version 2 content',
        created_at: '2025-06-19T15:00:00Z'
      }
      
      mockAxios.get.mockResolvedValue({ data: mockChunk })
      
      const result = await apiService.getChunkVersion('chunk-123', 2)
      
      expect(mockAxios.get).toHaveBeenCalledWith('/chunks/chunk-123', { params: { version: 2 } })
      expect(result).toEqual(mockChunk)
    })

    it('handles errors when fetching a specific version', async () => {
      mockAxios.get.mockRejectedValue(new Error('Version not found'))
      
      await expect(apiService.getChunkVersion('chunk-123', 2)).rejects.toThrow('Version not found')
      expect(mockAxios.get).toHaveBeenCalledWith('/chunks/chunk-123', { params: { version: 2 } })
    })
  })

  describe('restoreChunkVersion', () => {
    it('restores a chunk to a previous version', async () => {
      // Mock the getChunkVersion call
      const oldVersion = {
        chunk_id: 'chunk-123',
        version: 2,
        text: 'Old version content',
        props: { title: 'Old Title' }
      }
      
      // Mock the updateChunk call result
      const updateResult = {
        chunk_id: 'chunk-123',
        version: 4,
        text: 'Old version content',
        props: { title: 'Old Title' },
        is_latest: true
      }
      
      // Setup the mock responses
      mockAxios.get.mockResolvedValue({ data: oldVersion })
      mockAxios.put.mockResolvedValue({ data: updateResult })
      
      const result = await apiService.restoreChunkVersion('chunk-123', 2)
      
      // Check that getChunkVersion was called with the right params
      expect(mockAxios.get).toHaveBeenCalledWith('/chunks/chunk-123', { params: { version: 2 } })
      
      // Check that updateChunk was called with the right data
      expect(mockAxios.put).toHaveBeenCalledWith('/chunks/chunk-123', oldVersion)
      
      // Check that the result is what we expect
      expect(result).toEqual(updateResult)
    })

    it('handles errors when restoring a version', async () => {
      mockAxios.get.mockRejectedValue(new Error('Failed to fetch version'))
      
      await expect(apiService.restoreChunkVersion('chunk-123', 2)).rejects.toThrow('Failed to fetch version')
      expect(mockAxios.get).toHaveBeenCalledWith('/chunks/chunk-123', { params: { version: 2 } })
      expect(mockAxios.put).not.toHaveBeenCalled()
    })
  })
})
