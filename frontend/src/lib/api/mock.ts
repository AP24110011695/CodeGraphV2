import { ApiClientError } from './errors'
import { mockRepositories } from './fixtures/repositories'
import {
  mockFilesByRepo,
  mockFileAuthPy,
  mockSymbolsAuth,
} from './fixtures/files'
import { mockGraphResponse, mockNodeDetailAuth } from './fixtures/graph'
import {
  mockChatSessions,
  mockChatMessages,
  mockSearchResults,
} from './fixtures/chat'
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
  StreamChatCallbacks,
  SymbolResponse,
} from './types'

export interface MockClientOptions {
  latencyMs?: number
  pipelineStepDurationMs?: number
}

export class MockApiClient implements ApiClient {
  private repositories: RepositoryResponse[]
  private files: Record<string, FileDetail[]>
  private sessions: ChatSessionResponse[]
  private messages: Record<string, ChatMessageResponse[]>
  private repoCreationTimes: Map<string, number>
  private latencyMs: number
  private pipelineStepDurationMs: number

  constructor(options: MockClientOptions = {}) {
    this.repositories = JSON.parse(JSON.stringify(mockRepositories))
    this.files = JSON.parse(JSON.stringify(mockFilesByRepo))
    this.sessions = JSON.parse(JSON.stringify(mockChatSessions))
    this.messages = {
      'cs-001': JSON.parse(JSON.stringify(mockChatMessages)),
    }
    this.repoCreationTimes = new Map()
    this.latencyMs = options.latencyMs ?? 50
    this.pipelineStepDurationMs = options.pipelineStepDurationMs ?? 1000
  }

  private async delay(ms: number = this.latencyMs): Promise<void> {
    if (ms <= 0) return
    await new Promise((resolve) => setTimeout(resolve, ms))
  }

  private updateDynamicRepoStatus(repo: RepositoryResponse): RepositoryResponse {
    const creationTime = this.repoCreationTimes.get(repo.id)
    if (!creationTime) return repo

    const elapsed = Date.now() - creationTime
    const step = this.pipelineStepDurationMs

    if (elapsed < step) {
      repo.status = 'pending'
    } else if (elapsed < step * 2) {
      repo.status = 'ingesting'
    } else if (elapsed < step * 3) {
      repo.status = 'parsing'
    } else if (elapsed < step * 4) {
      repo.status = 'indexing'
    } else {
      repo.status = 'ready'
    }
    return repo
  }

  async health(): Promise<HealthResponse> {
    await this.delay()
    return {
      status: 'ok',
      version: '2.0.0',
      checks: {
        database: 'ok',
        redis: 'ok',
        celery: 'ok',
      },
    }
  }

  async listRepositories(
    params?: PaginationParams
  ): Promise<RepositoryListResponse> {
    await this.delay()
    const page = params?.page ?? 1
    const pageSize = params?.page_size ?? 20

    const updated = this.repositories.map((r) =>
      this.updateDynamicRepoStatus({ ...r })
    )

    const startIndex = (page - 1) * pageSize
    const paginatedItems = updated.slice(startIndex, startIndex + pageSize)

    return {
      items: paginatedItems.map((r) => ({
        id: r.id,
        name: r.name,
        slug: r.slug,
        status: r.status,
        source: r.source,
        file_count: r.file_count,
        created_at: r.created_at,
      })),
      total: updated.length,
      page,
      page_size: pageSize,
    }
  }

  async getRepository(id: string): Promise<RepositoryResponse> {
    await this.delay()
    const repo = this.repositories.find((r) => r.id === id)
    if (!repo) {
      throw new ApiClientError('Repository not found', 404, 'REPO_NOT_FOUND')
    }
    return this.updateDynamicRepoStatus({ ...repo })
  }

  async uploadRepository(
    file: File,
    name?: string
  ): Promise<RepositoryResponse> {
    await this.delay()
    const repoName = name || file.name.replace(/\.zip$/i, '') || 'uploaded-repo'
    const newRepo: RepositoryResponse = {
      id: crypto.randomUUID(),
      name: repoName,
      slug: repoName.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
      status: 'pending',
      source: 'upload',
      size_bytes: file.size,
      file_count: 12,
      primary_language: 'Python',
      detected_languages: { Python: 100 },
      frameworks: ['FastAPI'],
      created_at: new Date().toISOString(),
    }

    this.repoCreationTimes.set(newRepo.id, Date.now())
    this.repositories.unshift(newRepo)
    this.files[newRepo.id] = [mockFileAuthPy]
    return { ...newRepo }
  }

  async cloneRepository(gitUrl: string): Promise<RepositoryResponse> {
    await this.delay()
    if (!gitUrl.startsWith('https://')) {
      throw new ApiClientError(
        'Git URL must use HTTPS protocol',
        400,
        'INVALID_GIT_URL'
      )
    }

    const segments = gitUrl.replace(/\.git$/i, '').split('/')
    const repoName = segments[segments.length - 1] || 'cloned-repo'

    const newRepo: RepositoryResponse = {
      id: crypto.randomUUID(),
      name: repoName,
      slug: repoName.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
      status: 'pending',
      source: 'clone',
      size_bytes: 204800,
      file_count: 8,
      primary_language: 'TypeScript',
      detected_languages: { TypeScript: 100 },
      frameworks: ['React'],
      created_at: new Date().toISOString(),
    }

    this.repoCreationTimes.set(newRepo.id, Date.now())
    this.repositories.unshift(newRepo)
    this.files[newRepo.id] = [mockFileAuthPy]
    return { ...newRepo }
  }

  async deleteRepository(id: string): Promise<void> {
    await this.delay()
    const index = this.repositories.findIndex((r) => r.id === id)
    if (index === -1) {
      throw new ApiClientError('Repository not found', 404, 'REPO_NOT_FOUND')
    }
    this.repositories.splice(index, 1)
    delete this.files[id]
    this.repoCreationTimes.delete(id)
  }

  async getRepositoryStatus(id: string): Promise<RepositoryStatusResponse> {
    await this.delay()
    const repo = this.repositories.find((r) => r.id === id)
    if (!repo) {
      throw new ApiClientError('Repository not found', 404, 'REPO_NOT_FOUND')
    }

    const creationTime = this.repoCreationTimes.get(id)
    if (!creationTime) {
      return {
        status: repo.status,
        progress: repo.status === 'ready' ? 100 : 50,
        phase: repo.status === 'ready' ? 'indexing' : 'parsing',
        error_message: null,
      }
    }

    const elapsed = Date.now() - creationTime
    const step = this.pipelineStepDurationMs

    if (elapsed < step) {
      return { status: 'pending', progress: 10, phase: 'ingestion', error_message: null }
    }
    if (elapsed < step * 2) {
      return { status: 'ingesting', progress: 25, phase: 'extraction', error_message: null }
    }
    if (elapsed < step * 3) {
      return { status: 'parsing', progress: 50, phase: 'parsing', error_message: null }
    }
    if (elapsed < step * 4) {
      return { status: 'indexing', progress: 70, phase: 'graph', error_message: null }
    }
    if (elapsed < step * 5) {
      return { status: 'indexing', progress: 90, phase: 'indexing', error_message: null }
    }

    repo.status = 'ready'
    return { status: 'ready', progress: 100, phase: 'indexing', error_message: null }
  }

  async listFiles(
    repoId: string,
    params?: PaginationParams
  ): Promise<FileListResponse> {
    await this.delay()
    const repoFiles = this.files[repoId] || [mockFileAuthPy]
    const page = params?.page ?? 1
    const pageSize = params?.page_size ?? 20

    const startIndex = (page - 1) * pageSize
    const paginated = repoFiles.slice(startIndex, startIndex + pageSize)

    return {
      items: paginated.map((f) => ({
        id: f.id,
        path: f.path,
        language: f.language,
        size_bytes: f.size_bytes,
        line_count: f.line_count,
        is_binary: f.is_binary,
      })),
      total: repoFiles.length,
      page,
      page_size: pageSize,
    }
  }

  async getFile(repoId: string, fileId: string): Promise<FileDetail> {
    await this.delay()
    const repoFiles = this.files[repoId] || [mockFileAuthPy]
    const file = repoFiles.find((f) => f.id === fileId || f.path === fileId)
    if (!file) {
      throw new ApiClientError('File not found', 404, 'FILE_NOT_FOUND')
    }
    return { ...file }
  }

  async getSymbols(
    repoId: string,
    fileId: string
  ): Promise<SymbolResponse[]> {
    await this.delay()
    const file = await this.getFile(repoId, fileId)
    return file.symbols || mockSymbolsAuth
  }

  async getGraph(repoId: string): Promise<GraphResponse> {
    await this.delay()
    return {
      ...mockGraphResponse,
      repository_id: repoId,
    }
  }

  async getNodeDetail(
    _repoId: string,
    fileId: string
  ): Promise<NodeDetailResponse> {
    await this.delay()
    return {
      ...mockNodeDetailAuth,
      id: fileId,
    }
  }

  async search(
    _repoId: string,
    request: SearchRequest
  ): Promise<SearchResponse> {
    await this.delay()
    const query = request.query.toLowerCase()
    const matched = mockSearchResults.filter(
      (r) =>
        r.content.toLowerCase().includes(query) ||
        r.path.toLowerCase().includes(query)
    )

    const results = matched.length > 0 ? matched : mockSearchResults
    const limit = request.limit ?? 10
    const limited = results.slice(0, limit)

    return {
      query: request.query,
      results: limited,
      total: limited.length,
    }
  }

  async createChatSession(
    repoId: string,
    request?: CreateSessionRequest
  ): Promise<CreateSessionResponse> {
    await this.delay()
    const sessionId = crypto.randomUUID()
    const newSession: ChatSessionResponse = {
      id: sessionId,
      repository_id: repoId,
      title: request?.title || 'New Conversation',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    this.sessions.unshift(newSession)
    this.messages[sessionId] = []
    return { session_id: sessionId }
  }

  async listChatSessions(repoId: string): Promise<ChatSessionResponse[]> {
    await this.delay()
    return this.sessions.filter((s) => s.repository_id === repoId)
  }

  async listChatMessages(
    _repoId: string,
    sessionId: string
  ): Promise<ChatMessageResponse[]> {
    await this.delay()
    return this.messages[sessionId] || []
  }

  async sendMessageStream(
    _repoId: string,
    sessionId: string,
    request: SendMessageRequest,
    callbacks: StreamChatCallbacks,
    signal?: AbortSignal
  ): Promise<void> {
    await this.delay(10)
    if (signal?.aborted) return

    // Add user message
    const userMsg: ChatMessageResponse = {
      id: crypto.randomUUID(),
      session_id: sessionId,
      role: 'user',
      content: request.question,
      created_at: new Date().toISOString(),
    }
    if (!this.messages[sessionId]) {
      this.messages[sessionId] = []
    }
    this.messages[sessionId].push(userMsg)

    // Stream canned answer
    const answerText = `Based on the repository source files, the implementation for "${request.question}" is organized across modular components with clear separation of concerns.`
    const words = answerText.split(' ')

    for (const word of words) {
      if (signal?.aborted) return
      callbacks.onToken?.(word + ' ')
      await this.delay(20)
    }

    if (signal?.aborted) return

    const sources = [
      {
        path: 'app/services/auth.py',
        start_line: 10,
        end_line: 45,
        symbol_name: 'AuthService',
      },
    ]

    callbacks.onSources?.(sources)

    const assistantMsg: ChatMessageResponse = {
      id: crypto.randomUUID(),
      session_id: sessionId,
      role: 'assistant',
      content: answerText,
      sources,
      created_at: new Date().toISOString(),
    }
    this.messages[sessionId].push(assistantMsg)

    callbacks.onDone?.()
  }
}

export const mockClient = new MockApiClient()
