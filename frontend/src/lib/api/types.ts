/**
 * Shared API Contract Types for CodeGraph v2.
 * Mirrors BACKEND.md API Contract — Source of Truth.
 */

export type RepositoryStatus =
  | 'pending'
  | 'ingesting'
  | 'parsing'
  | 'indexing'
  | 'ready'
  | 'error'

export type RepositorySource = 'upload' | 'clone'

export type PipelinePhase =
  | 'ingestion'
  | 'extraction'
  | 'parsing'
  | 'graph'
  | 'indexing'

export type SymbolKind =
  | 'function'
  | 'class'
  | 'method'
  | 'variable'
  | 'interface'
  | 'type_alias'
  | 'enum'
  | 'constant'

export interface PaginationParams {
  page?: number
  page_size?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ErrorDetail {
  code: string
  message: string
  details?: Record<string, unknown>
}

export interface ErrorResponse {
  error: ErrorDetail
}

export interface HealthResponse {
  status: string
  version: string
  checks: Record<string, string>
}

// ---------------------------------------------------------------------------
// Repository Schemas
// ---------------------------------------------------------------------------

export interface RepositoryCreate {
  name: string
  description?: string | null
}

export interface RepositoryCloneRequest {
  git_url: string
}

export interface RepositoryResponse {
  id: string
  name: string
  slug: string
  status: RepositoryStatus
  source: RepositorySource
  size_bytes: number
  file_count: number
  primary_language: string | null
  detected_languages: Record<string, number> | null
  frameworks: string[] | null
  created_at: string
}

export interface RepositoryListItem {
  id: string
  name: string
  slug: string
  status: RepositoryStatus
  source: RepositorySource
  file_count: number
  created_at: string
}

export interface RepositoryListResponse {
  items: RepositoryListItem[]
  total: number
  page: number
  page_size: number
}

export interface RepositoryStatusResponse {
  status: RepositoryStatus
  progress: number
  phase: string
  error_message?: string | null
}

// ---------------------------------------------------------------------------
// File & Symbol Schemas
// ---------------------------------------------------------------------------

export interface SymbolResponse {
  id: string
  name: string
  kind: SymbolKind
  start_line: number
  end_line: number
  is_exported: boolean
  docstring: string | null
}

export interface FileListItem {
  id: string
  path: string
  language: string
  size_bytes: number
  line_count: number
  is_binary: boolean
  parse_error?: string | null
}

export interface FileListResponse {
  items: FileListItem[]
  total: number
  page: number
  page_size: number
}

export interface FileDetail {
  id: string
  repository_id: string
  path: string
  language: string
  size_bytes: number
  line_count: number
  is_binary: boolean
  content: string | null
  error?: string | null
  symbols: SymbolResponse[]
}

// ---------------------------------------------------------------------------
// Graph Schemas
// ---------------------------------------------------------------------------

export interface NodeMetrics {
  in_degree: number
  out_degree: number
  pagerank: number
  is_entry_point: boolean
  is_leaf: boolean
}

export interface NodeRecord {
  id: string
  path: string
  language: string | null
  symbol_count: number
  metrics: NodeMetrics
}

export interface EdgeRecord {
  from_file_id: string
  to_file_id: string
  import_name: string
}

export interface GraphMetrics {
  node_count: number
  edge_count: number
  has_cycles: boolean
  cycle_count: number
  entry_point_count: number
  leaf_count: number
}

export interface GraphResponse {
  repository_id: string
  generated_at: string
  metrics: GraphMetrics
  nodes: NodeRecord[]
  edges: EdgeRecord[]
}

export interface DependencyInfo {
  file_id: string
  path: string
  language: string | null
  import_name: string
}

export interface SymbolInfo {
  id: string
  name: string
  kind: string
  start_line: number
  end_line: number
}

export interface NodeDetailResponse {
  id: string
  path: string
  language: string | null
  symbol_count: number
  metrics: NodeMetrics
  symbols: SymbolInfo[]
  dependencies: DependencyInfo[]
  dependents: DependencyInfo[]
}

// ---------------------------------------------------------------------------
// Search Schemas
// ---------------------------------------------------------------------------

export interface SearchRequest {
  query: string
  limit?: number
}

export interface SearchResult {
  chunk_id: string
  file_id: string
  path: string
  content: string
  start_line: number
  end_line: number
  score: number
  chunk_type: string
  symbol_id?: string | null
}

export interface SearchResponse {
  query: string
  results: SearchResult[]
  total: number
}

// ---------------------------------------------------------------------------
// Chat & RAG Schemas
// ---------------------------------------------------------------------------

export interface CreateSessionRequest {
  title?: string | null
}

export interface CreateSessionResponse {
  session_id: string
}

export interface ChatSessionResponse {
  id: string
  repository_id: string
  title: string | null
  created_at: string
  updated_at: string
}

export interface SendMessageRequest {
  question: string
}

export interface SourceItem {
  path: string
  start_line: number
  end_line: number
  symbol_name?: string | null
}

export interface ChatMessageResponse {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  sources?: SourceItem[] | null
  created_at: string
}

// ---------------------------------------------------------------------------
// ApiClient Interface
// ---------------------------------------------------------------------------

export interface StreamChatCallbacks {
  onToken?: (token: string) => void
  onSources?: (sources: SourceItem[]) => void
  onDone?: () => void
  onError?: (error: Error) => void
}

export interface ApiClient {
  health(): Promise<HealthResponse>
  listRepositories(params?: PaginationParams): Promise<RepositoryListResponse>
  getRepository(id: string): Promise<RepositoryResponse>
  uploadRepository(file: File, name?: string): Promise<RepositoryResponse>
  cloneRepository(gitUrl: string): Promise<RepositoryResponse>
  deleteRepository(id: string): Promise<void>
  getRepositoryStatus(id: string): Promise<RepositoryStatusResponse>
  listFiles(repoId: string, params?: PaginationParams): Promise<FileListResponse>
  getFile(repoId: string, fileId: string): Promise<FileDetail>
  getSymbols(repoId: string, fileId: string): Promise<SymbolResponse[]>
  getGraph(repoId: string): Promise<GraphResponse>
  getNodeDetail(repoId: string, fileId: string): Promise<NodeDetailResponse>
  search(repoId: string, request: SearchRequest): Promise<SearchResponse>
  createChatSession(
    repoId: string,
    request?: CreateSessionRequest
  ): Promise<CreateSessionResponse>
  listChatSessions(repoId: string): Promise<ChatSessionResponse[]>
  listChatMessages(
    repoId: string,
    sessionId: string
  ): Promise<ChatMessageResponse[]>
  sendMessageStream(
    repoId: string,
    sessionId: string,
    request: SendMessageRequest,
    callbacks: StreamChatCallbacks,
    signal?: AbortSignal
  ): Promise<void>
}
