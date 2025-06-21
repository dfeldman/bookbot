import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useBookStore } from './book';
import { apiService } from '../services/api';
import type { Book, Chunk } from './types';

// Mock the apiService
vi.mock('../services/api', () => ({
  apiService: {
    deleteChunk: vi.fn(),
    restoreChunkVersion: vi.fn(),
    getChunkVersions: vi.fn(),
  },
}));

// Mock Pinia store setup
beforeEach(() => {
  const pinia = createPinia();
  setActivePinia(pinia);
});

describe('bookStore', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
  });

  describe('deleteChunk', () => {
    it('should call the API and remove the chunk from the store', async () => {
      const bookStore = useBookStore();
      const chunkId = 'chunk1';
      const bookId = 'book1';

      // Setup initial state
      bookStore.currentBook = {
        book_id: bookId,
        chunks: [{ chunk_id: chunkId }, { chunk_id: 'chunk2' }],
      } as any;

      // Mock the API response
      (apiService.deleteChunk as vi.Mock).mockResolvedValue({});

      await bookStore.deleteChunk(chunkId);

      // Assertions
      expect(apiService.deleteChunk).toHaveBeenCalledWith(chunkId);
      expect(bookStore.currentBook?.chunks?.length).toBe(1);
      expect(bookStore.currentBook?.chunks?.[0].chunk_id).toBe('chunk2');
    });
  });

  describe('restoreChunkVersion', () => {
    it('should call the API, update the chunk, and refetch versions', async () => {
      const bookStore = useBookStore();
      const chunkId = 'chunk1';
      const version = 2;
      const originalChunk: Chunk = {
        chunk_id: chunkId,
        book_id: 'book1',
        type: 'prose',
        title: 'Chapter 1',
        text: 'Original content',
        is_deleted: false,
        is_latest: true,
        version: 1,
        word_count: 3,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      const restoredChunk: Chunk = { ...originalChunk, version: 2, text: 'Restored content' };

      // Setup initial state
      const book: Book = {
        book_id: 'book1',
        user_id: 'user1',
        title: 'My Book',
        description: 'A book.',
        props: {},
        is_locked: false,
        is_deleted: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        chunks: [originalChunk],
      };
      bookStore.currentBook = book;

      // Mock the API responses
      (apiService.restoreChunkVersion as vi.Mock).mockResolvedValue(restoredChunk);
      (apiService.getChunkVersions as vi.Mock).mockResolvedValue({ versions: [] });

      await bookStore.restoreChunkVersion(chunkId, version);

      // Assertions
      expect(apiService.restoreChunkVersion).toHaveBeenCalledWith(chunkId, version);
      
      // Check that the chunk in the store has been updated
      const updatedChunk = bookStore.currentBook?.chunks?.find(c => c.chunk_id === chunkId);
      expect(updatedChunk).toEqual(restoredChunk);

      // Check that versions were refetched
      expect(apiService.getChunkVersions).toHaveBeenCalledWith(chunkId);
    });
  });
});
