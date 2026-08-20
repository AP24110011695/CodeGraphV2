import { describe, it, expect, beforeEach } from 'vitest'
import { useConnectionStore } from './connection-store'
import { useUiStore } from './ui-store'

describe('useConnectionStore', () => {
  beforeEach(() => {
    localStorage.clear()
    useConnectionStore.getState().resetSettings()
  })

  it('initializes with default values', () => {
    const state = useConnectionStore.getState()
    expect(state.apiBaseUrl).toBe('http://localhost:8000')
    expect(state.apiKey).toBeNull()
    expect(state.rememberApiKey).toBe(false)
    expect(state.useMockApi).toBe(true)
  })

  it('updates base URL, API key, and mock settings', () => {
    useConnectionStore.getState().setApiBaseUrl('https://api.codegraph.dev/')
    expect(useConnectionStore.getState().apiBaseUrl).toBe('https://api.codegraph.dev')

    useConnectionStore.getState().setApiKey('cg_test_12345')
    expect(useConnectionStore.getState().apiKey).toBe('cg_test_12345')

    useConnectionStore.getState().setUseMockApi(false)
    expect(useConnectionStore.getState().useMockApi).toBe(false)
  })

  it('excludes apiKey from localStorage persistence when rememberApiKey is false', () => {
    useConnectionStore.getState().setApiKey('secret-key')
    useConnectionStore.getState().setRememberApiKey(false)

    // Trigger state persist
    const stored = JSON.parse(localStorage.getItem('codegraph-connection-storage') || '{}')
    expect(stored.state?.apiKey).toBeUndefined()
    expect(stored.state?.rememberApiKey).toBe(false)
  })

  it('includes apiKey in localStorage persistence when rememberApiKey is true', () => {
    useConnectionStore.getState().setRememberApiKey(true)
    useConnectionStore.getState().setApiKey('secret-key-saved')

    const stored = JSON.parse(localStorage.getItem('codegraph-connection-storage') || '{}')
    expect(stored.state?.apiKey).toBe('secret-key-saved')
    expect(stored.state?.rememberApiKey).toBe(true)
  })
})

describe('useUiStore', () => {
  beforeEach(() => {
    localStorage.clear()
    useUiStore.setState({
      isSidebarCollapsed: false,
      theme: 'dark',
      authPromptOpen: false,
    })
  })

  it('toggles sidebar collapse state', () => {
    expect(useUiStore.getState().isSidebarCollapsed).toBe(false)
    useUiStore.getState().toggleSidebar()
    expect(useUiStore.getState().isSidebarCollapsed).toBe(true)
    useUiStore.getState().setSidebarCollapsed(false)
    expect(useUiStore.getState().isSidebarCollapsed).toBe(false)
  })

  it('updates theme mode', () => {
    useUiStore.getState().setTheme('light')
    expect(useUiStore.getState().theme).toBe('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('updates authPromptOpen state', () => {
    expect(useUiStore.getState().authPromptOpen).toBe(false)
    useUiStore.getState().setAuthPromptOpen(true)
    expect(useUiStore.getState().authPromptOpen).toBe(true)
  })
})
