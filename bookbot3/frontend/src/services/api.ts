import axios, { AxiosInstance } from 'axios'
import type { LLMInfo, Book, Chunk, Job } from '../stores/types'



class ApiService {
  private api: AxiosInstance

  constructor() {
    this.api = axios.create({
      baseURL: '/api',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Add request interceptor for auth
    this.api.interceptors.request.use((config) => {
      // TODO: Add authentication headers when needed
      return config
    })

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message)
        return Promise.reject(error)
      }
    )
  }

  // Config endpoints
  async getConfig(): Promise<any> {
    const response = await this.api.get('/config')
    return response.data
  }

  async checkTokenStatus(apiKey: string): Promise<any> {
    const response = await this.api.post('/token-status', { api_key: apiKey })
    return response.data
  }

  // Book endpoints
  async getBooks(): Promise<{ books: Book[] }> {
    const response = await this.api.get('/books')
    return response.data
  }

  async getBook(bookId: string): Promise<Book> {
    const response = await this.api.get(`/books/${bookId}`)
    return response.data
  }

  async createBook(data: Partial<Book>): Promise<Book> {
    const response = await this.api.post('/books', data)
    return response.data
  }

  async updateBook(bookId: string, data: Partial<Book>): Promise<Book> {
    const response = await this.api.put(`/books/${bookId}`, data)
    return response.data
  }

  async deleteBook(bookId: string): Promise<void> {
    await this.api.delete(`/books/${bookId}`)
  }

  // LLM endpoints
  async getLlmCatalog(): Promise<{ llms: LLMInfo[] }> {
    const response = await this.api.get('/llms');
    return response.data;
  }

  async getLlmDefaults(bookId: string): Promise<{ [key: string]: string }> {
    const response = await this.api.get(`/llms/books/${bookId}/defaults`);
    return response.data;
  }

  async updateLlmDefaults(bookId: string, defaults: { [key: string]: string }): Promise<any> {
    const response = await this.api.put(`/llms/books/${bookId}/defaults`, defaults);
    return response.data;
  }

  async getLlmOverride(bookId: string): Promise<{ llm_id: string | null }> {
    const response = await this.api.get(`/llms/books/${bookId}/override`);
    return response.data;
  }

  async updateLlmOverride(bookId: string, llmId: string | null): Promise<any> {
    const response = await this.api.put(`/llms/books/${bookId}/override`, { llm_id: llmId });
    return response.data;
  }

  // Chunk endpoints
  async getChunks(bookId: string, params?: any): Promise<{ chunks: Chunk[] }> {
    const response = await this.api.get(`/books/${bookId}/chunks`, { params })
    return response.data
  }

  async getChunk(chunkId: string): Promise<Chunk> {
    const response = await this.api.get(`/chunks/${chunkId}`, { params: { include_text: true } })
    return response.data
  }

  async createChunk(bookId: string, data: Partial<Chunk>): Promise<Chunk> {
    const response = await this.api.post(`/books/${bookId}/chunks`, data)
    return response.data
  }

  async updateChunk(chunkId: string, data: Partial<Chunk>): Promise<Chunk> {
    const response = await this.api.put(`/chunks/${chunkId}`, data)
    return response.data
  }

  async deleteChunk(chunkId: string): Promise<void> {
    await this.api.delete(`/chunks/${chunkId}`)
  }

  // Chunk version endpoints
  async getChunkVersions(chunkId: string): Promise<{ versions: Chunk[] }> {
    const response = await this.api.get(`/chunks/${chunkId}/versions`)
    return response.data
  }

  async getChunkVersion(chunkId: string, version: number): Promise<Chunk> {
    const response = await this.api.get(`/chunks/${chunkId}`, { params: { version } })
    return response.data
  }
  
  async restoreChunkVersion(chunkId: string, version: number): Promise<Chunk> {
    // Get the version we want to restore
    const oldVersion = await this.getChunkVersion(chunkId, version)
    
    // Update the chunk with this version's content (automatically creates a new version)
    return await this.updateChunk(chunkId, oldVersion)
  }

  async getChunkContext(bookId: string, chunkId: string): Promise<any> {
    const response = await this.api.get(`/books/${bookId}/chunks/${chunkId}/context`)
    return response.data
  }

  // Job endpoints
  async getJobs(bookId: string, params?: any): Promise<{ jobs: Job[] }> {
    const response = await this.api.get(`/books/${bookId}/jobs`, { params })
    return response.data
  }

  async getJob(jobId: string): Promise<Job> {
    const response = await this.api.get(`/jobs/${jobId}`)
    return response.data
  }

  async getJobLogs(jobId: string): Promise<{ logs: any[] }> {
    const response = await this.api.get(`/jobs/${jobId}/logs`)
    return response.data
  }

  async createJob(bookId: string, data: any): Promise<Job> {
    const response = await this.api.post(`/books/${bookId}/jobs`, data)
    return response.data
  }

  async cancelJob(jobId: string): Promise<void> {
    await this.api.delete(`/jobs/${jobId}`)
  }

  async getRunningJobs(): Promise<{ jobs: Job[] }> {
    const response = await this.api.get('/jobs/running');
    return response.data;
  }

  async getAllJobs(params?: any): Promise<{ jobs: Job[] }> {
    const response = await this.api.get('/jobs', { params });
    return response.data;
  }

  async getTotalCostAllJobs(): Promise<{ total_cost: number }> {
    const response = await this.api.get('/jobs/total_cost');
    return response.data;
  }

  // Server-sent events for job streaming
  createJobEventSource(bookId: string): EventSource {
    return new EventSource(`/api/books/${bookId}/jobs/stream`)
  }

  // Generic API request methods for flexibility
  async get(url: string, params?: any): Promise<any> {
    const response = await this.api.get(url, { params })
    return response.data
  }

  async post(url: string, data?: any): Promise<any> {
    const response = await this.api.post(url, data)
    return response.data
  }

  async put(url: string, data?: any): Promise<any> {
    const response = await this.api.put(url, data)
    return response.data
  }

  async delete(url: string): Promise<any> {
    const response = await this.api.delete(url)
    return response.data
  }

  // Health check
  async healthCheck(): Promise<any> {
    const response = await this.api.get('/health')
    return response.data
  }
}

export const apiService = new ApiService()
