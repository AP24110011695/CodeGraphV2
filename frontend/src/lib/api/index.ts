import { mockClient } from './mock'
import { realClient } from './client'
import type { ApiClient } from './types'

export const isUsingMock =
  typeof import.meta !== 'undefined' &&
  import.meta.env?.VITE_USE_MOCK_API !== 'false'

export const apiClient: ApiClient = isUsingMock ? mockClient : realClient

export * from './types'
export * from './errors'
export * from './mock'
export * from './client'
export * from './fixtures/repositories'
export * from './fixtures/files'
export * from './fixtures/graph'
export * from './fixtures/chat'
