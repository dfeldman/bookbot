import axios, { AxiosInstance } from 'axios'

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
  async getBooks(): Promise<{ books: any[] }> {
    const response = await this.api.get('/books')
    return response.data
  }

  async getBook(bookId: string): Promise<any> {
    const response = await this.api.get(`/books/${bookId}`)
    return response.data
  }

  async createBook(data: { props: any }): Promise<any> {
    const response = await this.api.post('/books', data)
    return response.data
  }

  async updateBook(bookId: string, data: { props: any }): Promise<any> {
    const response = await this.api.put(`/books/${bookId}`, data)
    return response.data
  }

  async deleteBook(bookId: string): Promise<void> {
    await this.api.delete(`/books/${bookId}`)
  }

  // Chunk endpoints
  async getChunks(bookId: string, params?: any): Promise<{ chunks: any[] }> {
    const response = await this.api.get(`/books/${bookId}/chunks`, { params })
    return response.data
  }

  async getChunk(chunkId: string): Promise<any> {
    const response = await this.api.get(`/chunks/${chunkId}`)
    return response.data
  }

  async createChunk(bookId: string, data: any): Promise<any> {
    const response = await this.api.post(`/books/${bookId}/chunks`, data)
    return response.data
  }

  async updateChunk(chunkId: string, data: any): Promise<any> {
    const response = await this.api.put(`/chunks/${chunkId}`, data)
    return response.data
  }

  async deleteChunk(chunkId: string): Promise<void> {
    await this.api.delete(`/chunks/${chunkId}`)
  }

  async getChunkContext(bookId: string, chunkId: string): Promise<any> {
    const response = await this.api.get(`/books/${bookId}/chunks/${chunkId}/context`)
    return response.data
  }

  // Job endpoints
  async getJobs(bookId: string, params?: any): Promise<{ jobs: any[] }> {
    const response = await this.api.get(`/books/${bookId}/jobs`, { params })
    return response.data
  }

  async getJob(jobId: string): Promise<any> {
    const response = await this.api.get(`/jobs/${jobId}`)
    return response.data
  }

  async getJobLogs(jobId: string): Promise<{ logs: any[] }> {
    const response = await this.api.get(`/jobs/${jobId}/logs`)
    return response.data
  }

  async createJob(bookId: string, data: any): Promise<any> {
    const response = await this.api.post(`/books/${bookId}/jobs`, data)
    return response.data
  }

  async cancelJob(jobId: string): Promise<void> {
    await this.api.delete(`/jobs/${jobId}`)
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
