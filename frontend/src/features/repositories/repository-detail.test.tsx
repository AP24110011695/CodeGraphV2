import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '@/components/ui/toast'
import { RepositoryOverview } from './components/repository-overview'
import { RepositoryTabs } from './components/repository-tabs'
import { apiClient } from '@/lib/api'
import type { RepositoryResponse } from '@/lib/api/types'

const mockNavigate = vi.fn()
let currentMockPath = '/repositories/repo-123'

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('@tanstack/react-router')
  return {
    ...actual,
    Link: ({
      to,
      params,
      children,
      className,
      role,
      'aria-selected': ariaSelected,
    }: {
      to: string
      params?: Record<string, unknown>
      children?: React.ReactNode
      className?: string
      role?: string
      'aria-selected'?: boolean
    }) => (
      <a
        href={to}
        className={className}
        role={role}
        aria-selected={ariaSelected}
        data-params={JSON.stringify(params)}
      >
        {children}
      </a>
    ),
    useNavigate: () => mockNavigate,
    useRouterState: () => ({
      location: {
        pathname: currentMockPath,
      },
    }),
  }
})

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>{ui}</ToastProvider>
    </QueryClientProvider>
  )
}

describe('Repository Detail & Overview Features', () => {
  const mockRepo: RepositoryResponse = {
    id: 'repo-123',
    name: 'Sample Backend Service',
    slug: 'sample-backend-service',
    status: 'ready',
    source: 'upload',
    size_bytes: 1048576, // 1MB
    file_count: 24,
    primary_language: 'Python',
    detected_languages: {
      Python: 80,
      SQL: 15,
      Dockerfile: 5,
    },
    frameworks: ['FastAPI', 'SQLAlchemy', 'Pydantic'],
    created_at: '2026-08-01T10:00:00Z',
  }

  beforeEach(() => {
    vi.restoreAllMocks()
    mockNavigate.mockReset()
    currentMockPath = '/repositories/repo-123'
  })

  describe('RepositoryOverview', () => {
    it('renders repository metadata, stats, languages, and frameworks', () => {
      renderWithProviders(<RepositoryOverview repository={mockRepo} />)

      expect(screen.getByText('Sample Backend Service')).toBeInTheDocument()
      expect(screen.getByText(/sample-backend-service • ID: repo-123/i)).toBeInTheDocument()
      expect(screen.getByText('1 MB')).toBeInTheDocument()
      expect(screen.getByText('24')).toBeInTheDocument()
      expect(screen.getAllByText('Python').length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText('FastAPI')).toBeInTheDocument()
      expect(screen.getByText('SQLAlchemy')).toBeInTheDocument()
      expect(screen.getByText('Pydantic')).toBeInTheDocument()
      expect(screen.getByText('80%')).toBeInTheDocument()
    })

    it('opens delete confirmation modal and executes delete mutation', async () => {
      const user = userEvent.setup()
      const deleteSpy = vi.spyOn(apiClient, 'deleteRepository').mockResolvedValue(undefined)

      renderWithProviders(<RepositoryOverview repository={mockRepo} />)

      const deleteBtn = screen.getByRole('button', { name: /delete repository/i })
      await user.click(deleteBtn)

      // Confirm modal is visible
      expect(screen.getByText(/are you sure you want to permanently delete repository/i)).toBeInTheDocument()

      const confirmBtn = screen.getByRole('button', { name: /confirm delete/i })
      await user.click(confirmBtn)

      await waitFor(() => {
        expect(deleteSpy).toHaveBeenCalledWith('repo-123')
        expect(mockNavigate).toHaveBeenCalledWith({ to: '/' })
      })
    })

    it('closes delete modal on cancel without triggering deletion', async () => {
      const user = userEvent.setup()
      const deleteSpy = vi.spyOn(apiClient, 'deleteRepository').mockResolvedValue(undefined)

      renderWithProviders(<RepositoryOverview repository={mockRepo} />)

      const deleteBtn = screen.getByRole('button', { name: /delete repository/i })
      await user.click(deleteBtn)

      const cancelBtn = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelBtn)

      await waitFor(() => {
        expect(deleteSpy).not.toHaveBeenCalled()
      })
    })
  })

  describe('RepositoryTabs', () => {
    it('enables all navigation tabs when repository status is ready', () => {
      renderWithProviders(<RepositoryTabs repository={mockRepo} />)

      expect(screen.getByRole('tab', { name: /overview/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /files & code/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /dependency graph/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /semantic search/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /ai assistant/i })).toBeInTheDocument()
    })

    it('disables Graph, Search, and Chat tabs when repository is still parsing', () => {
      const pendingRepo: RepositoryResponse = {
        ...mockRepo,
        status: 'parsing',
      }

      renderWithProviders(<RepositoryTabs repository={pendingRepo} />)

      expect(screen.getByRole('tab', { name: /overview/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /files & code/i })).toBeInTheDocument()

      // The other tabs should have aria-disabled="true"
      const graphTab = screen.getByText(/dependency graph/i).closest('[role="tab"]')
      const searchTab = screen.getByText(/semantic search/i).closest('[role="tab"]')
      const chatTab = screen.getByText(/ai assistant/i).closest('[role="tab"]')

      expect(graphTab).toHaveAttribute('aria-disabled', 'true')
      expect(searchTab).toHaveAttribute('aria-disabled', 'true')
      expect(chatTab).toHaveAttribute('aria-disabled', 'true')
    })
  })
})
