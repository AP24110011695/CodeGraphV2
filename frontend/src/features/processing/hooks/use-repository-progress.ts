import * as React from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useConnectionStore } from '@/stores/connection-store'
import { ApiClientError } from '@/lib/api/errors'
import { apiClient } from '@/lib/api'
import type { PipelinePhase, RepositoryStatus, RepositoryStatusResponse } from '@/lib/api/types'

export interface RepositoryProgressState {
  status: RepositoryStatus | null
  progress: number
  phase: PipelinePhase | null
  errorMessage: string | null
  isConnected: boolean
}

const POLL_INTERVAL_MS = 2000
const SSE_RECONNECT_DELAY_MS = 1000

/**
 * useRepositoryProgress connects to the backend SSE stream for live pipeline
 * progress updates. Uses fetch + ReadableStream (not EventSource) so that
 * the X-API-Key header can be included.
 *
 * Fallback: if the SSE connection fails or drops, the hook automatically
 * switches to polling GET /repositories/{id}/status every 2 seconds.
 *
 * Auto-stops once status reaches "ready" or "error".
 * Writes updates directly into the ['repository', repoId] TanStack Query
 * cache so useRepository() reflects live state without a separate refetch.
 */
export function useRepositoryProgress(
  repoId: string | undefined,
  initialStatus: RepositoryStatus | null = null
): RepositoryProgressState {
  const queryClient = useQueryClient()

  const [state, setState] = React.useState<RepositoryProgressState>({
    status: initialStatus,
    progress: 0,
    phase: null,
    errorMessage: null,
    isConnected: false,
  })

  // Track whether we're done so effects can bail out
  const isDoneRef = React.useRef(false)
  const abortRef = React.useRef<AbortController | null>(null)
  const pollTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null)

  const applyStatusUpdate = React.useCallback(
    (update: RepositoryStatusResponse) => {
      const phase = update.phase as PipelinePhase | null

      setState({
        status: update.status,
        progress: update.progress,
        phase,
        errorMessage: update.error_message ?? null,
        isConnected: true,
      })

      // Write into the repository query cache so RepositoryOverview stays in sync
      if (repoId) {
        queryClient.setQueryData<{ status: RepositoryStatus; [key: string]: unknown }>(
          ['repository', repoId],
          (old) => {
            if (!old) return old
            return { ...old, status: update.status }
          }
        )
      }

      if (update.status === 'ready' || update.status === 'error') {
        isDoneRef.current = true
        // Invalidate so full repository data is refreshed from server
        if (repoId) {
          queryClient.invalidateQueries({ queryKey: ['repository', repoId] })
        }
      }
    },
    [repoId, queryClient]
  )

  // ─── Polling fallback ────────────────────────────────────────────────────────
  const startPolling = React.useCallback(() => {
    if (!repoId) return

    const poll = async () => {
      if (isDoneRef.current) return
      try {
        const statusResp = await apiClient.getRepositoryStatus(repoId)
        applyStatusUpdate(statusResp)
      } catch (err) {
        console.warn('[useRepositoryProgress] poll error:', err)
      }

      if (!isDoneRef.current) {
        pollTimerRef.current = setTimeout(poll, POLL_INTERVAL_MS)
      }
    }

    poll()
  }, [repoId, applyStatusUpdate])

  const stopPolling = React.useCallback(() => {
    if (pollTimerRef.current !== null) {
      clearTimeout(pollTimerRef.current)
      pollTimerRef.current = null
    }
  }, [])

  // ─── SSE connection ──────────────────────────────────────────────────────────
  const connectSSE = React.useCallback(async () => {
    if (!repoId || isDoneRef.current) return

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    // Build the SSE URL using the store's baseUrl
    const baseUrl = (
      useConnectionStore.getState().apiBaseUrl || 'http://localhost:8000'
    ).replace(/\/$/, '')
    const apiKey = useConnectionStore.getState().apiKey
    const url = `${baseUrl}/api/v1/repositories/${repoId}/events`

    const headers: HeadersInit = { Accept: 'text/event-stream' }
    if (apiKey) headers['X-API-Key'] = apiKey

    let sseSucceeded = false

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers,
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new ApiClientError(
          `SSE endpoint returned ${response.status}`,
          response.status
        )
      }

      if (!response.body) {
        throw new ApiClientError('SSE response has no body', 500)
      }

      sseSucceeded = true
      setState((prev) => ({ ...prev, isConnected: true }))

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      // SSE parse loop
      while (!isDoneRef.current) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        // SSE messages are separated by double newlines
        const parts = buffer.split('\n\n')
        buffer = parts.pop() ?? ''

        for (const part of parts) {
          const lines = part.split('\n')
          for (const line of lines) {
            // Ignore keep-alive comments (":ping" etc.)
            if (line.startsWith(':')) continue

            if (line.startsWith('data:')) {
              const dataContent = line.startsWith('data: ')
                ? line.slice(6)
                : line.slice(5)

              if (!dataContent) continue

              try {
                const parsed = JSON.parse(dataContent) as RepositoryStatusResponse
                applyStatusUpdate(parsed)
              } catch {
                // Not JSON — ignore malformed frames
              }
            }
          }
        }
      }
    } catch (err) {
      if (controller.signal.aborted) return

      if (!sseSucceeded) {
        // SSE failed to open — fall back to polling after a brief delay
        console.warn('[useRepositoryProgress] SSE failed, falling back to polling:', err)
        setState((prev) => ({ ...prev, isConnected: false }))
        await new Promise((r) => setTimeout(r, SSE_RECONNECT_DELAY_MS))
        if (!isDoneRef.current) {
          startPolling()
        }
      } else {
        // Stream dropped mid-way — fall back to polling
        console.warn('[useRepositoryProgress] SSE stream dropped, switching to polling:', err)
        setState((prev) => ({ ...prev, isConnected: false }))
        if (!isDoneRef.current) {
          startPolling()
        }
      }
    }
  }, [repoId, applyStatusUpdate, startPolling])

  React.useEffect(() => {
    if (!repoId) return
    if (initialStatus === 'ready' || initialStatus === 'error') {
      // Already terminal — nothing to track
      return
    }

    isDoneRef.current = false

    // Kick off SSE; it falls back to polling automatically on failure
    connectSSE()

    return () => {
      isDoneRef.current = true
      abortRef.current?.abort()
      stopPolling()
    }
  }, [repoId, initialStatus, connectSSE, stopPolling])

  return state
}
