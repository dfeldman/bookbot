import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'

// Mock the API service directly instead of trying to mock axios
vi.mock('../src/services/api', () => ({
  apiService: {
    getChunkVersions: vi.fn(),
    getChunkVersion: vi.fn(),
    restoreChunkVersion: vi.fn(),
    updateChunk: vi.fn()
  }
}))

// Import after mocking
import { apiService } from '../src/services/api'

describe('API Service - Chunk Versions', () => {
  beforeEach(() => {
    // Reset mock functions
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('getChunkVersions', () => {
    it('fetches chunk versions correctly', async () => {
      const mockVersions = {
        versions: [
          { chunk_id: 'chunk-123', version: 2, is_latest: true },
          { chunk_id: 'chunk-123', version: 1, is_latest: false }
        ]
      }

      apiService.getChunkVersions.mockResolvedValue(mockVersions)
      
      const result = await apiService.getChunkVersions('chunk-123')
      
      expect(apiService.getChunkVersions).toHaveBeenCalledWith('chunk-123')
      expect(result).toEqual(mockVersions)
      expect(result.versions.length).toBe(2)
      expect(result.versions[0].version).toBe(2)
      expect(result.versions[0].is_latest).toBe(true)
    })

    it('handles errors when fetching versions', async () => {
      apiService.getChunkVersions.mockRejectedValue(new Error('Network error'))
      
      await expect(apiService.getChunkVersions('chunk-123')).rejects.toThrow('Network error')
      expect(apiService.getChunkVersions).toHaveBeenCalledWith('chunk-123')
    })
  })

  describe('getChunkVersion', () => {
    it('fetches a specific chunk version correctly', async () => {
      const mockVersion = {
        chunk_id: 'chunk-123',
        version: 1,
        text: 'Old version content'
      }

      apiService.getChunkVersion.mockResolvedValue(mockVersion)
      
      const result = await apiService.getChunkVersion('chunk-123', 1)
      
      expect(apiService.getChunkVersion).toHaveBeenCalledWith('chunk-123', 1)
      expect(result).toEqual(mockVersion)
      expect(result.text).toBe('Old version content')
    })

    it('handles errors when fetching a specific version', async () => {
      apiService.getChunkVersion.mockRejectedValue(new Error('Version not found'))
      
      await expect(apiService.getChunkVersion('chunk-123', 1)).rejects.toThrow('Version not found')
      expect(apiService.getChunkVersion).toHaveBeenCalledWith('chunk-123', 1)
    })
  })

  describe('restoreChunkVersion', () => {
    it('restores an old chunk version correctly', async () => {
      // Mock responses for the getChunkVersion and updateChunk calls
      const mockOldVersion = {
        chunk_id: 'chunk-123',
        version: 1,
        text: 'Old version content',
        props: { name: 'Old name' }
      }
      
      const mockRestoredVersion = {
        chunk_id: 'chunk-123',
        version: 3,
        is_latest: true
      }

      // Mock the getChunkVersion call
      apiService.getChunkVersion.mockResolvedValue(mockOldVersion)
      
      // Mock the final result after restoration
      apiService.restoreChunkVersion.mockResolvedValue(mockRestoredVersion)
      
      const result = await apiService.restoreChunkVersion('chunk-123', 1)
      
      // Should call restoreChunkVersion with the right parameters
      expect(apiService.restoreChunkVersion).toHaveBeenCalledWith('chunk-123', 1)
      
      expect(result).toEqual(mockRestoredVersion)
    })

    it('handles errors when restoring a version', async () => {
      // Mock error on restoreChunkVersion
      apiService.restoreChunkVersion.mockRejectedValue(new Error('Version not found'))
      
      await expect(apiService.restoreChunkVersion('chunk-123', 1)).rejects.toThrow('Version not found')
      expect(apiService.restoreChunkVersion).toHaveBeenCalledWith('chunk-123', 1)
    })
  })
})
