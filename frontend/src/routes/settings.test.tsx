import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SettingsPage } from './settings'
import { ToastProvider } from '@/components/ui/toast'
import { useConnectionStore } from '@/stores/connection-store'
import { apiClient } from '@/lib/api'

describe('SettingsPage', () => {
  beforeEach(() => {
    localStorage.clear()
    useConnectionStore.getState().resetSettings()
    vi.restoreAllMocks()
  })

  it('renders settings fields with default values', () => {
    render(
      <ToastProvider>
        <SettingsPage />
      </ToastProvider>
    )

    expect(screen.getByRole('heading', { name: /connection settings/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/backend base url/i)).toHaveValue('http://localhost:8000')
    expect(screen.getByPlaceholderText('cg_live_...')).toHaveValue('')
    expect(screen.getByLabelText(/use in-memory mock api/i)).toBeChecked()
  })

  it('updates store on valid form submission', async () => {
    const user = userEvent.setup()
    render(
      <ToastProvider>
        <SettingsPage />
      </ToastProvider>
    )

    const urlInput = screen.getByLabelText(/backend base url/i)
    const keyInput = screen.getByPlaceholderText('cg_live_...')
    const rememberCheckbox = screen.getByLabelText(/remember this api key/i)
    const submitBtn = screen.getByRole('button', { name: /save changes/i })

    await user.clear(urlInput)
    await user.type(urlInput, 'https://api.mycodegraph.com')
    await user.type(keyInput, 'cg_live_998877')
    await user.click(rememberCheckbox)
    await user.click(submitBtn)

    await waitFor(() => {
      const state = useConnectionStore.getState()
      expect(state.apiBaseUrl).toBe('https://api.mycodegraph.com')
      expect(state.apiKey).toBe('cg_live_998877')
      expect(state.rememberApiKey).toBe(true)
    })
  })

  it('tests connection via apiClient.health and shows feedback', async () => {
    const user = userEvent.setup()
    const healthSpy = vi.spyOn(apiClient, 'health').mockResolvedValue({
      status: 'healthy',
      version: '2.0.0',
      checks: { database: 'ok' },
    })

    render(
      <ToastProvider>
        <SettingsPage />
      </ToastProvider>
    )

    const testBtn = screen.getByRole('button', { name: /test connection/i })
    await user.click(testBtn)

    await waitFor(() => {
      expect(healthSpy).toHaveBeenCalled()
      expect(screen.getByText(/backend service is healthy/i)).toBeInTheDocument()
    })
  })
})
