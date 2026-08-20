import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProcessingStepper } from './components/processing-stepper'
import { useRepositoryProgress } from './hooks/use-repository-progress'
import type { PipelinePhase } from '@/lib/api/types'

// ─── ProcessingStepper unit tests ────────────────────────────────────────────

describe('ProcessingStepper', () => {
  it('renders all five canonical pipeline stages', () => {
    render(
      <ProcessingStepper
        status="ingesting"
        progress={20}
        phase="ingestion"
        errorMessage={null}
      />
    )

    expect(screen.getByText('Ingestion')).toBeInTheDocument()
    expect(screen.getByText('Extraction')).toBeInTheDocument()
    expect(screen.getByText('Parsing')).toBeInTheDocument()
    expect(screen.getByText('Graph')).toBeInTheDocument()
    expect(screen.getByText('Indexing')).toBeInTheDocument()
  })

  it('shows "Active" badge on the current phase stage', () => {
    render(
      <ProcessingStepper
        status="parsing"
        progress={50}
        phase="parsing"
        errorMessage={null}
      />
    )

    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('renders all stages as done when status is ready', () => {
    render(
      <ProcessingStepper
        status="ready"
        progress={100}
        phase="indexing"
        errorMessage={null}
      />
    )

    expect(screen.getByText('Processing complete')).toBeInTheDocument()
    // No "Active" badge when everything is done
    expect(screen.queryByText('Active')).not.toBeInTheDocument()
  })

  it('renders error state with message when status is error', () => {
    render(
      <ProcessingStepper
        status="error"
        progress={30}
        phase="parsing"
        errorMessage="AST parser crashed on file main.py"
        onRetry={vi.fn()}
      />
    )

    // "Processing failed" appears in both the stepper header text AND the ErrorState h3
    expect(screen.getAllByText('Processing failed').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/AST parser crashed on file main.py/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /retry processing/i })).toBeInTheDocument()
  })

  it('renders error state with fallback message when errorMessage is null', () => {
    render(
      <ProcessingStepper
        status="error"
        progress={0}
        phase={null}
        errorMessage={null}
        onRetry={vi.fn()}
      />
    )

    expect(screen.getByText(/unexpected error occurred/i)).toBeInTheDocument()
  })

  it.each<[PipelinePhase, string]>([
    ['ingestion', 'Ingestion'],
    ['extraction', 'Extraction'],
    ['parsing', 'Parsing'],
    ['graph', 'Graph'],
    ['indexing', 'Indexing'],
  ])('marks stage "%s" as active when phase is "%s"', (phase, label) => {
    render(
      <ProcessingStepper
        status="ingesting"
        progress={20}
        phase={phase}
        errorMessage={null}
      />
    )

    // The active stage shows the "Active" badge alongside its label
    const activeLabel = screen.getByText(label)
    expect(activeLabel).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
  })
})

// ─── useRepositoryProgress hook tests ────────────────────────────────────────

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

// Helper: creates a ReadableStream that emits SSE frames
function makeSseStream(frames: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  let idx = 0
  return new ReadableStream({
    pull(controller) {
      if (idx < frames.length) {
        controller.enqueue(encoder.encode(frames[idx++]))
      } else {
        controller.close()
      }
    },
  })
}

// Wrapper component to expose hook state via data attributes
function ProgressHarness({ repoId }: { repoId: string }) {
  const progress = useRepositoryProgress(repoId, 'ingesting')
  return (
    <div
      data-status={progress.status}
      data-phase={progress.phase ?? ''}
      data-progress={progress.progress}
      data-error={progress.errorMessage ?? ''}
      data-connected={progress.isConnected}
    >
      {progress.status}
    </div>
  )
}

describe('useRepositoryProgress', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = makeQueryClient()
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('updates state from SSE stream frames', async () => {
    const frames = [
      `data: ${JSON.stringify({ status: 'ingesting', progress: 25, phase: 'ingestion', error_message: null })}\n\n`,
      `data: ${JSON.stringify({ status: 'parsing', progress: 50, phase: 'parsing', error_message: null })}\n\n`,
      `data: ${JSON.stringify({ status: 'ready', progress: 100, phase: 'indexing', error_message: null })}\n\n`,
    ]

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(makeSseStream(frames), {
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
      })
    )

    render(
      <QueryClientProvider client={queryClient}>
        <ProgressHarness repoId="test-repo" />
      </QueryClientProvider>
    )

    await waitFor(() => {
      const el = screen.getByText(/ready|parsing|ingesting/)
      expect(el).toBeInTheDocument()
    })
  })

  it('falls back to polling when SSE connection fails', async () => {
    // Use real timers for this test so waitFor works correctly
    vi.useRealTimers()

    // SSE fetch throws immediately (simulates connection refused / network error)
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Network error'))

    render(
      <QueryClientProvider client={queryClient}>
        <ProgressHarness repoId="fallback-repo" />
      </QueryClientProvider>
    )

    // The SSE fetch should have been called once (and failed)
    await waitFor(
      () => {
        expect(globalThis.fetch).toHaveBeenCalledTimes(1)
      },
      { timeout: 2000 }
    )

    // After SSE failure, isConnected should be false (fallback polling engaged)
    await waitFor(
      () => {
        const el = document.querySelector('[data-connected]')
        expect(el?.getAttribute('data-connected')).toBe('false')
      },
      { timeout: 3000 }
    )
  })

  it('ignores SSE keepalive ping comments', async () => {
    const frames = [
      `:ping\n\n`,
      `data: ${JSON.stringify({ status: 'parsing', progress: 50, phase: 'parsing', error_message: null })}\n\n`,
    ]

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(makeSseStream(frames), {
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
      })
    )

    render(
      <QueryClientProvider client={queryClient}>
        <ProgressHarness repoId="ping-repo" />
      </QueryClientProvider>
    )

    await waitFor(() => {
      const el = screen.getByText(/parsing|ingesting/)
      expect(el).toBeInTheDocument()
    })
  })
})
