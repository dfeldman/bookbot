import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useJobStore } from './jobStore';
import { apiService } from '../services/api';
import type { Job } from './book';

// Mock the apiService
vi.mock('../services/api', () => ({
  apiService: {
    getAllJobs: vi.fn(),
  },
}));

// Mock Pinia store setup
beforeEach(() => {
  const pinia = createPinia();
  setActivePinia(pinia);
});

describe('jobStore', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
  });

  it('should fetch all jobs and update the state', async () => {
    const jobStore = useJobStore();
    const mockJobs: Job[] = [
      { job_id: '1', book_id: 'book1', state: 'complete', job_type: 'test', created_at: new Date().toISOString(), total_cost: 10 },
      { job_id: '2', book_id: 'book2', state: 'running', job_type: 'test', created_at: new Date().toISOString(), started_at: new Date().toISOString(), total_cost: 5 },
    ];

    // Mock the API response
    (apiService.getAllJobs as vi.Mock).mockResolvedValue({ jobs: mockJobs });

    expect(jobStore.isJobsViewerLoading).toBe(false);

    // Call the action
    await jobStore.fetchAllJobs();

    // Assertions
    expect(jobStore.isJobsViewerLoading).toBe(false);
    expect(apiService.getAllJobs).toHaveBeenCalledWith({});
    expect(jobStore.allJobs).toEqual(mockJobs);
  });

  it('should handle API errors gracefully', async () => {
    const jobStore = useJobStore();
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    // Mock the API to throw an error
    (apiService.getAllJobs as vi.Mock).mockRejectedValue(new Error('API Error'));
    // Ensure the mock for successful calls is reset or specific to the test if needed
    // For this test, we are testing error handling, so the above is fine.

    await jobStore.fetchAllJobs();

    expect(jobStore.isJobsViewerLoading).toBe(false);
    expect(jobStore.allJobs).toEqual([]);
    expect(console.error).toHaveBeenCalledWith('Failed to fetch all jobs:', expect.any(Error));

    consoleErrorSpy.mockRestore();
  });

  it('should pass filters to the API call', async () => {
    const jobStore = useJobStore();
    (apiService.getAllJobs as vi.Mock).mockResolvedValue({ jobs: [] });

    await jobStore.fetchAllJobs('book123', 'complete');

    expect(apiService.getAllJobs).toHaveBeenCalledWith({ book_id: 'book123', state: 'complete' });
  });
});
