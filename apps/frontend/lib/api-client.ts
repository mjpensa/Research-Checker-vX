import axios, { AxiosInstance, AxiosError } from 'axios'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        if (typeof window !== 'undefined') {
          const token = localStorage.getItem('auth_token')
          if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`
          }
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          if (typeof window !== 'undefined') {
            window.location.href = '/login'
          }
        }
        return Promise.reject(error)
      }
    )
  }

  // Pipelines
  async createPipeline(data: { name?: string; metadata?: any }) {
    return this.client.post('/api/v1/pipelines/', data)
  }

  async uploadDocuments(pipelineId: string, files: File[], sourceLlm?: string) {
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))
    if (sourceLlm) formData.append('source_llm', sourceLlm)

    return this.client.post(`/api/v1/pipelines/${pipelineId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  }

  async startPipeline(pipelineId: string) {
    return this.client.post(`/api/v1/pipelines/${pipelineId}/start`)
  }

  async getPipeline(id: string) {
    return this.client.get(`/api/v1/pipelines/${id}`)
  }

  async listPipelines(params?: { limit?: number; offset?: number; status?: string }) {
    return this.client.get('/api/v1/pipelines/', { params })
  }

  async updatePipeline(id: string, data: { name?: string; metadata?: any }) {
    return this.client.patch(`/api/v1/pipelines/${id}`, data)
  }

  async deletePipeline(id: string) {
    return this.client.delete(`/api/v1/pipelines/${id}`)
  }

  // Claims
  async getClaims(params?: { pipeline_id?: string; limit?: number; offset?: number; claim_type?: string }) {
    return this.client.get('/api/v1/claims/', { params })
  }

  async getClaim(id: string) {
    return this.client.get(`/api/v1/claims/${id}`)
  }

  async getClaimDependencies(id: string) {
    return this.client.get(`/api/v1/claims/${id}/dependencies`)
  }

  async getClaimStats(pipelineId: string) {
    return this.client.get(`/api/v1/claims/pipeline/${pipelineId}/stats`)
  }

  // Reports
  async analyzeDependencies(pipelineId: string) {
    return this.client.post(`/api/v1/reports/${pipelineId}/analyze-dependencies`)
  }

  async detectContradictions(pipelineId: string) {
    return this.client.post(`/api/v1/reports/${pipelineId}/detect-contradictions`)
  }

  async generateReport(pipelineId: string, reportType: string = 'synthesis') {
    return this.client.post(`/api/v1/reports/${pipelineId}/generate?report_type=${reportType}`)
  }

  async getReports(pipelineId: string) {
    return this.client.get(`/api/v1/reports/${pipelineId}`)
  }

  async getLatestReport(pipelineId: string) {
    return this.client.get(`/api/v1/reports/${pipelineId}/latest`)
  }

  async getReport(reportId: string) {
    return this.client.get(`/api/v1/reports/report/${reportId}`)
  }

  async getContradictions(pipelineId: string) {
    return this.client.get(`/api/v1/reports/${pipelineId}/contradictions`)
  }
}

export const apiClient = new ApiClient()
