import { mockClient } from './mock'
import { realClient } from './client'
import type { ApiClient } from './types'
import { useConnectionStore } from '@/stores/connection-store'

export function getApiClient(): ApiClient {
  try {
    const isMock = useConnectionStore.getState?.()?.useMockApi
    if (typeof isMock === 'boolean') {
      return isMock ? mockClient : realClient
    }
  } catch {
    // Fallback if store not initialized
  }
  const defaultMock =
    typeof import.meta !== 'undefined'
      ? import.meta.env?.VITE_USE_MOCK_API !== 'false'
      : true
  return defaultMock ? mockClient : realClient
}

export const apiClient: ApiClient = {
  health: (...args) => getApiClient().health(...args),
  listRepositories: (...args) => getApiClient().listRepositories(...args),
  getRepository: (...args) => getApiClient().getRepository(...args),
  uploadRepository: (...args) => getApiClient().uploadRepository(...args),
  cloneRepository: (...args) => getApiClient().cloneRepository(...args),
  deleteRepository: (...args) => getApiClient().deleteRepository(...args),
  getRepositoryStatus: (...args) => getApiClient().getRepositoryStatus(...args),
  listFiles: (...args) => getApiClient().listFiles(...args),
  getFile: (...args) => getApiClient().getFile(...args),
  getSymbols: (...args) => getApiClient().getSymbols(...args),
  getGraph: (...args) => getApiClient().getGraph(...args),
  getNodeDetail: (...args) => getApiClient().getNodeDetail(...args),
  search: (...args) => getApiClient().search(...args),
  createChatSession: (...args) => getApiClient().createChatSession(...args),
  listChatSessions: (...args) => getApiClient().listChatSessions(...args),
  listChatMessages: (...args) => getApiClient().listChatMessages(...args),
  sendMessageStream: (...args) => getApiClient().sendMessageStream(...args),
}

export * from './types'
export * from './errors'
export * from './mock'
export * from './client'
export * from './fixtures/repositories'
export * from './fixtures/files'
export * from './fixtures/graph'
export * from './fixtures/chat'
