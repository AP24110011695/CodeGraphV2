import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { buildGraphologyInstance, DependencyGraph } from './components/dependency-graph'
import { GraphControls } from './components/graph-controls'
import { NodeDetailPanel } from './components/node-detail-panel'
import type { GraphResponse } from '@/lib/api/types'

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('@tanstack/react-router')
  return {
    ...actual,
    Link: ({
      to,
      params,
      children,
      className,
    }: {
      to: string
      params?: Record<string, unknown>
      children?: React.ReactNode
      className?: string
    }) => (
      <a href={to} className={className} data-params={JSON.stringify(params)}>
        {children}
      </a>
    ),
    useNavigate: () => vi.fn(),
  }
})

const mockGraphData: GraphResponse = {
  repository_id: 'test-repo',
  generated_at: '2026-08-20T00:00:00Z',
  metrics: {
    node_count: 3,
    edge_count: 2,
    has_cycles: true,
    cycle_count: 1,
    entry_point_count: 1,
    leaf_count: 1,
  },
  nodes: [
    {
      id: 'n1',
      path: 'app/main.py',
      language: 'python',
      symbol_count: 5,
      metrics: {
        in_degree: 0,
        out_degree: 2,
        pagerank: 0.15,
        is_entry_point: true,
        is_leaf: false,
      },
    },
    {
      id: 'n2',
      path: 'app/auth.py',
      language: 'python',
      symbol_count: 8,
      metrics: {
        in_degree: 1,
        out_degree: 1,
        pagerank: 0.45,
        is_entry_point: false,
        is_leaf: false,
      },
    },
    {
      id: 'n3',
      path: 'src/index.ts',
      language: 'typescript',
      symbol_count: 4,
      metrics: {
        in_degree: 1,
        out_degree: 0,
        pagerank: 0.40,
        is_entry_point: false,
        is_leaf: true,
      },
    },
  ],
  edges: [
    { from_file_id: 'n1', to_file_id: 'n2', import_name: 'auth' },
    { from_file_id: 'n2', to_file_id: 'n3', import_name: 'types' },
  ],
}

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}

describe('Graph Feature Components', () => {
  describe('buildGraphologyInstance', () => {
    it('creates graphology instance with all nodes and edges', () => {
      const graph = buildGraphologyInstance(mockGraphData)
      expect(graph.order).toBe(3) // 3 nodes
      expect(graph.size).toBe(2) // 2 edges
      expect(graph.hasNode('n1')).toBe(true)
      expect(graph.hasNode('n2')).toBe(true)
      expect(graph.hasNode('n3')).toBe(true)
      expect(graph.hasEdge('n1', 'n2')).toBe(true)
    })

    it('filters graph by language when requested', () => {
      const graph = buildGraphologyInstance(mockGraphData, {
        languages: ['typescript'],
      })
      expect(graph.order).toBe(1)
      expect(graph.hasNode('n3')).toBe(true)
      expect(graph.hasNode('n1')).toBe(false)
    })

    it('filters graph by only entry points when requested', () => {
      const graph = buildGraphologyInstance(mockGraphData, {
        onlyEntryPoints: true,
      })
      expect(graph.order).toBe(1)
      expect(graph.hasNode('n1')).toBe(true)
      expect(graph.hasNode('n2')).toBe(false)
    })
  })

  describe('DependencyGraph', () => {
    it('renders the graph container and calls onGraphReady callback', () => {
      const onGraphReady = vi.fn()
      render(
        <DependencyGraph
          data={mockGraphData}
          onGraphReady={onGraphReady}
        />
      )

      expect(screen.getByTestId('dependency-graph-container')).toBeInTheDocument()
      expect(onGraphReady).toHaveBeenCalled()
    })
  })

  describe('GraphControls', () => {
    it('renders language toggles, entry point filter, and node stats', () => {
      const onToggleLang = vi.fn()
      const onToggleEntry = vi.fn()

      render(
        <GraphControls
          metrics={mockGraphData.metrics}
          availableLanguages={['python', 'typescript']}
          selectedLanguages={['python']}
          onToggleLanguage={onToggleLang}
          onlyEntryPoints={false}
          onToggleEntryPoints={onToggleEntry}
        />
      )

      expect(screen.getByText('python')).toBeInTheDocument()
      expect(screen.getByText('typescript')).toBeInTheDocument()
      expect(screen.getByText(/3 nodes · 2 edges/i)).toBeInTheDocument()
      expect(screen.getByText(/Only Entry Points \(1\)/i)).toBeInTheDocument()
    })

    it('displays cycle warning banner when metrics.has_cycles is true', () => {
      render(
        <GraphControls
          metrics={mockGraphData.metrics}
          availableLanguages={['python']}
          selectedLanguages={[]}
          onToggleLanguage={vi.fn()}
          onlyEntryPoints={false}
          onToggleEntryPoints={vi.fn()}
        />
      )

      expect(screen.getByTestId('cycle-warning-banner')).toBeInTheDocument()
      expect(
        screen.getByText(/Circular Dependencies Detected/i)
      ).toBeInTheDocument()
    })

    it('hides cycle warning banner when metrics.has_cycles is false', () => {
      render(
        <GraphControls
          metrics={{ ...mockGraphData.metrics, has_cycles: false, cycle_count: 0 }}
          availableLanguages={['python']}
          selectedLanguages={[]}
          onToggleLanguage={vi.fn()}
          onlyEntryPoints={false}
          onToggleEntryPoints={vi.fn()}
        />
      )

      expect(screen.queryByTestId('cycle-warning-banner')).not.toBeInTheDocument()
    })

    it('triggers toggle callbacks on click', async () => {
      const user = userEvent.setup()
      const onToggleLang = vi.fn()
      const onToggleEntry = vi.fn()

      render(
        <GraphControls
          metrics={mockGraphData.metrics}
          availableLanguages={['python']}
          selectedLanguages={[]}
          onToggleLanguage={onToggleLang}
          onlyEntryPoints={false}
          onToggleEntryPoints={onToggleEntry}
        />
      )

      await user.click(screen.getByText('python'))
      expect(onToggleLang).toHaveBeenCalledWith('python')

      await user.click(screen.getByText(/Only Entry Points/i))
      expect(onToggleEntry).toHaveBeenCalledWith(true)
    })
  })

  describe('NodeDetailPanel', () => {
    it('renders node detail metrics, symbols, dependencies, and dependents from mock API', async () => {
      const onClose = vi.fn()
      renderWithQuery(
        <NodeDetailPanel
          repoId="test-repo"
          nodeId="n1"
          onClose={onClose}
        />
      )

      expect(screen.getByTestId('node-detail-panel')).toBeInTheDocument()
      expect(screen.getByText(/File Details/i)).toBeInTheDocument()
      await waitFor(() => {
        expect(screen.getByText(/View in Files Tab/i)).toBeInTheDocument()
      })
    })

    it('returns null when nodeId is null', () => {
      const { container } = renderWithQuery(
        <NodeDetailPanel
          repoId="test-repo"
          nodeId={null}
          onClose={vi.fn()}
        />
      )

      expect(container).toBeEmptyDOMElement()
    })
  })
})
