import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export interface ConnectionState {
  apiBaseUrl: string
  apiKey: string | null
  rememberApiKey: boolean
  useMockApi: boolean
  setApiBaseUrl: (url: string) => void
  setApiKey: (key: string | null) => void
  setRememberApiKey: (remember: boolean) => void
  setUseMockApi: (useMock: boolean) => void
  resetSettings: () => void
}

const DEFAULT_BASE_URL =
  (typeof import.meta !== 'undefined' &&
    import.meta.env?.VITE_API_BASE_URL) ||
  'http://localhost:8000'

const DEFAULT_USE_MOCK =
  typeof import.meta !== 'undefined'
    ? import.meta.env?.VITE_USE_MOCK_API !== 'false'
    : true

export const useConnectionStore = create<ConnectionState>()(
  persist(
    (set) => ({
      apiBaseUrl: DEFAULT_BASE_URL,
      apiKey: null,
      rememberApiKey: false,
      useMockApi: DEFAULT_USE_MOCK,
      setApiBaseUrl: (url: string) => set({ apiBaseUrl: url.trim().replace(/\/$/, '') }),
      setApiKey: (key: string | null) => set({ apiKey: key ? key.trim() : null }),
      setRememberApiKey: (remember: boolean) =>
        set(() => ({ rememberApiKey: remember })),
      setUseMockApi: (useMock: boolean) => set({ useMockApi: useMock }),
      resetSettings: () =>
        set({
          apiBaseUrl: DEFAULT_BASE_URL,
          apiKey: null,
          rememberApiKey: false,
          useMockApi: DEFAULT_USE_MOCK,
        }),
    }),
    {
      name: 'codegraph-connection-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        apiBaseUrl: state.apiBaseUrl,
        rememberApiKey: state.rememberApiKey,
        useMockApi: state.useMockApi,
        // Only persist apiKey if rememberApiKey is true
        ...(state.rememberApiKey && state.apiKey ? { apiKey: state.apiKey } : {}),
      }),
    }
  )
)
