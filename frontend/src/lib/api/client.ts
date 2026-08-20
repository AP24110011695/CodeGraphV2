import { useConnectionStore } from '@/stores/connection-store'
import { ApiClientError } from './errors'
import type {
  ApiClient,
  ChatMessageResponse,
  ChatSessionResponse,
  CreateSessionRequest,
  CreateSessionResponse,
  FileDetail,
  FileListResponse,
  GraphResponse,
  HealthResponse,
  NodeDetailResponse,
  PaginationParams,
  RepositoryListResponse,
  RepositoryResponse,
  RepositoryStatusResponse,
  SearchRequest,
  SearchResponse,
  SendMessageRequest,
  SourceItem,
  StreamChatCallbacks,
  SymbolResponse,
} from './types'

export interface RealClientConfig {
  baseUrl?: string
  getApiKey?: () => string | null
}

export class RealApiClient implements ApiClient {
  private customBaseUrl?: string
  private getApiKey?: () => string | null

  constructor(config: RealClientConfig = {}) {
    if (config.baseUrl) {
      this.customBaseUrl = config.baseUrl.replace(/\/$/, '')
    }
    this.getApiKey = config.getApiKey
  }

  private getEffectiveBaseUrl(): string {
    if (this.customBaseUrl) {
      return this.customBaseUrl
    }
    try {
      const storeUrl = useConnectionStore.getState?.()?.apiBaseUrl
      if (storeUrl) {
        return storeUrl.replace(/\/$/, '')
      }
    } catch {
      // Store may not be initialized
    }
    return (
      (typeof import.meta !== 'undefined' &&
        import.meta.env?.VITE_API_BASE_URL) ||
      'http://localhost:8000'
    ).replace(/\/$/, '')
  }

  private getHeaders(contentType: string | null = 'application/json'): HeadersInit {
    const headers: Record<string, string> = {}
    if (contentType) {
      headers['Content-Type'] = contentType
    }

    let apiKey: string | null = null
    if (this.getApiKey) {
      apiKey = this.getApiKey()
    } else {
      try {
        apiKey = useConnectionStore.getState?.()?.apiKey || null
      } catch {
        // Store may not be initialized
      }
    }

    if (apiKey) {
      headers['X-API-Key'] = apiKey
    }
    return headers
  }

  private buildQuery(params?: PaginationParams | Record<string, unknown>): string {
    if (!params) return ''
    const query = new URLSearchParams()
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        query.append(key, String(value))
      }
    }
    const queryString = query.toString()
    return queryString ? `?${queryString}` : ''
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.getEffectiveBaseUrl()}${path}`
    const isFormData = options.body instanceof FormData
    const defaultHeaders = this.getHeaders(isFormData ? null : 'application/json')

    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers as Record<string, string>),
      },
    })

    if (!response.ok) {
      let data: unknown
      try {
        data = await response.json()
      } catch {
        // Response wasn't JSON
      }
      throw ApiClientError.fromErrorResponse(response.status, data)
    }

    if (response.status === 204) {
      return undefined as unknown as T
    }

    return (await response.json()) as T
  }

  async health(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health')
  }

  async listRepositories(
    params?: PaginationParams
  ): Promise<RepositoryListResponse> {
    const query = this.buildQuery(params)
    return this.request<RepositoryListResponse>(`/api/v1/repositories${query}`)
  }

  async getRepository(id: string): Promise<RepositoryResponse> {
    return this.request<RepositoryResponse>(`/api/v1/repositories/${id}`)
  }

  async uploadRepository(
    file: File,
    name?: string
  ): Promise<RepositoryResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (name) {
      formData.append('name', name)
    }

    return this.request<RepositoryResponse>('/api/v1/repositories', {
      method: 'POST',
      body: formData,
    })
  }

  async cloneRepository(gitUrl: string): Promise<RepositoryResponse> {
    return this.request<RepositoryResponse>('/api/v1/repositories/clone', {
      method: 'POST',
      body: JSON.stringify({ git_url: gitUrl }),
    })
  }

  async deleteRepository(id: string): Promise<void> {
    await this.request<void>(`/api/v1/repositories/${id}`, {
      method: 'DELETE',
    })
  }

  async getRepositoryStatus(id: string): Promise<RepositoryStatusResponse> {
    return this.request<RepositoryStatusResponse>(
      `/api/v1/repositories/${id}/status`
    )
  }

  async listFiles(
    repoId: string,
    params?: PaginationParams
  ): Promise<FileListResponse> {
    const query = this.buildQuery(params)
    return this.request<FileListResponse>(
      `/api/v1/repositories/${repoId}/files${query}`
    )
  }

  async getFile(repoId: string, fileId: string): Promise<FileDetail> {
    return this.request<FileDetail>(
      `/api/v1/repositories/${repoId}/files/${fileId}`
    )
  }

  async getSymbols(
    repoId: string,
    fileId: string
  ): Promise<SymbolResponse[]> {
    return this.request<SymbolResponse[]>(
      `/api/v1/repositories/${repoId}/files/${fileId}/symbols`
    )
  }

  async getGraph(repoId: string): Promise<GraphResponse> {
    return this.request<GraphResponse>(
      `/api/v1/repositories/${repoId}/graph`
    )
  }

  async getNodeDetail(
    repoId: string,
    fileId: string
  ): Promise<NodeDetailResponse> {
    return this.request<NodeDetailResponse>(
      `/api/v1/repositories/${repoId}/graph/node/${fileId}`
    )
  }

  async search(
    repoId: string,
    request: SearchRequest
  ): Promise<SearchResponse> {
    return this.request<SearchResponse>(
      `/api/v1/repositories/${repoId}/search`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    )
  }

  async createChatSession(
    repoId: string,
    request?: CreateSessionRequest
  ): Promise<CreateSessionResponse> {
    return this.request<CreateSessionResponse>(
      `/api/v1/repositories/${repoId}/chat/sessions`,
      {
        method: 'POST',
        body: JSON.stringify(request || {}),
      }
    )
  }

  async listChatSessions(repoId: string): Promise<ChatSessionResponse[]> {
    return this.request<ChatSessionResponse[]>(
      `/api/v1/repositories/${repoId}/chat/sessions`
    )
  }

  async listChatMessages(
    repoId: string,
    sessionId: string
  ): Promise<ChatMessageResponse[]> {
    return this.request<ChatMessageResponse[]>(
      `/api/v1/repositories/${repoId}/chat/sessions/${sessionId}/messages`
    )
  }

  async sendMessageStream(
    repoId: string,
    sessionId: string,
    request: SendMessageRequest,
    callbacks: StreamChatCallbacks,
    signal?: AbortSignal
  ): Promise<void> {
    const url = `${this.getEffectiveBaseUrl()}/api/v1/repositories/${repoId}/chat/sessions/${sessionId}/messages`
    const defaultHeaders = this.getHeaders('application/json')

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          ...defaultHeaders,
          Accept: 'text/event-stream',
        },
        body: JSON.stringify(request),
        signal,
      })

      if (!response.ok) {
        let data: unknown
        try {
          data = await response.json()
        } catch {
          // not json
        }
        throw ApiClientError.fromErrorResponse(response.status, data)
      }

      if (!response.body) {
        throw new ApiClientError('Response body is missing', 500)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trimEnd()
          if (!trimmed.startsWith('data:')) continue

          // SSE specification: if a single space follows the colon, it is ignored
          const dataContent = trimmed.startsWith('data: ')
            ? trimmed.slice(6)
            : trimmed.slice(5)

          if (dataContent === '[DONE]') {
            callbacks.onDone?.()
            return
          }

          if (dataContent.startsWith('__sources__:')) {
            try {
              const rawJson = dataContent.slice('__sources__:'.length)
              const sources: SourceItem[] = JSON.parse(rawJson)
              callbacks.onSources?.(sources)
            } catch (err) {
              console.error('Failed to parse chat sources', err)
            }
            continue
          }

          callbacks.onToken?.(dataContent)
        }
      }

      callbacks.onDone?.()
    } catch (error) {
      if (signal?.aborted) return
      const err =
        error instanceof ApiClientError
          ? error
          : new ApiClientError(
              error instanceof Error ? error.message : 'Chat stream failed'
            )
      callbacks.onError?.(err)
      throw err
    }
  }
}

export const realClient = new RealApiClient()
