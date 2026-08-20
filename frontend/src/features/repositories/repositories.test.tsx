import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '@/components/ui/toast'
import { RepositoryList } from './components/repository-list'
import { UploadDropzone } from './components/upload-dropzone'
import { CloneForm } from './components/clone-form'
import { AddRepositoryModal } from './components/add-repository-modal'
import { apiClient } from '@/lib/api'
import type { RepositoryResponse } from '@/lib/api/types'

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

describe('Repository Features', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  describe('RepositoryList', () => {
    it('renders repository items when query succeeds', async () => {
      vi.spyOn(apiClient, 'listRepositories').mockResolvedValue({
        items: [
          {
            id: 'repo-abc',
            name: 'FastAPI Backend',
            slug: 'fastapi-backend',
            status: 'ready',
            source: 'upload',
            file_count: 14,
            created_at: '2026-08-01T12:00:00Z',
          },
        ],
        total: 1,
        page: 1,
        page_size: 12,
      })

      renderWithProviders(<RepositoryList />)

      await waitFor(() => {
        expect(screen.getByText('FastAPI Backend')).toBeInTheDocument()
        expect(screen.getByText('fastapi-backend')).toBeInTheDocument()
        expect(screen.getByText('14 files')).toBeInTheDocument()
      })
    })

    it('renders EmptyState when no repositories exist', async () => {
      vi.spyOn(apiClient, 'listRepositories').mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 12,
      })

      const onAdd = vi.fn()
      renderWithProviders(<RepositoryList onAddRepository={onAdd} />)

      await waitFor(() => {
        expect(screen.getByText(/no repositories ingested yet/i)).toBeInTheDocument()
      })

      const addBtn = screen.getByRole('button', { name: /add your first repository/i })
      fireEvent.click(addBtn)
      expect(onAdd).toHaveBeenCalled()
    })

    it('renders ErrorState when fetching fails', async () => {
      vi.spyOn(apiClient, 'listRepositories').mockRejectedValue(new Error('Network error'))

      renderWithProviders(<RepositoryList />)

      await waitFor(() => {
        expect(screen.getByText(/failed to load repositories/i)).toBeInTheDocument()
        expect(screen.getByText(/network error/i)).toBeInTheDocument()
      })
    })
  })

  describe('UploadDropzone', () => {
    it('validates zip file extension and rejects other file types', async () => {
      renderWithProviders(<UploadDropzone />)

      const fileInput = document.getElementById('zip-file-input') as HTMLInputElement
      const textFile = new File(['hello'], 'notes.txt', { type: 'text/plain' })

      fireEvent.change(fileInput, { target: { files: [textFile] } })

      await waitFor(() => {
        expect(screen.getByText(/invalid file type/i)).toBeInTheDocument()
      })
    })

    it('rejects oversized files exceeding 500MB', async () => {
      renderWithProviders(<UploadDropzone />)

      const fileInput = document.getElementById('zip-file-input') as HTMLInputElement
      const bigFile = new File(['x'.repeat(100)], 'huge.zip', { type: 'application/zip' })
      Object.defineProperty(bigFile, 'size', { value: 600 * 1024 * 1024 })

      fireEvent.change(fileInput, { target: { files: [bigFile] } })

      await waitFor(() => {
        expect(screen.getByText(/file size exceeds the 500mb limit/i)).toBeInTheDocument()
      })
    })

    it('accepts valid zip and calls upload mutation', async () => {
      const user = userEvent.setup()
      const mockResult: RepositoryResponse = {
        id: 'new-repo-1',
        name: 'sample-project',
        slug: 'sample-project',
        status: 'pending',
        source: 'upload',
        size_bytes: 5000,
        file_count: 8,
        primary_language: 'Python',
        detected_languages: { Python: 8 },
        frameworks: ['FastAPI'],
        created_at: '2026-08-01T00:00:00Z',
      }

      const uploadSpy = vi.spyOn(apiClient, 'uploadRepository').mockResolvedValue(mockResult)
      const onSuccess = vi.fn()

      renderWithProviders(<UploadDropzone onSuccess={onSuccess} />)

      const fileInput = document.getElementById('zip-file-input') as HTMLInputElement
      const validZip = new File(['mock content'], 'sample-project.zip', { type: 'application/zip' })

      fireEvent.change(fileInput, { target: { files: [validZip] } })

      await waitFor(() => {
        expect(screen.getByText('sample-project.zip')).toBeInTheDocument()
      })

      const submitBtn = screen.getByRole('button', { name: /upload & ingest/i })
      await user.click(submitBtn)

      await waitFor(() => {
        expect(uploadSpy).toHaveBeenCalledWith(validZip, 'sample-project')
        expect(onSuccess).toHaveBeenCalledWith(mockResult)
      })
    })
  })

  describe('CloneForm', () => {
    it('validates HTTPS git URL', async () => {
      const user = userEvent.setup()
      renderWithProviders(<CloneForm />)

      const input = screen.getByLabelText(/git repository https url/i)
      const submitBtn = screen.getByRole('button', { name: /clone & ingest/i })

      await user.type(input, 'ftp://invalid-url')
      await user.click(submitBtn)

      await waitFor(() => {
        expect(screen.getByText(/must be a valid https git url/i)).toBeInTheDocument()
      })
    })

    it('submits valid git URL and triggers clone mutation', async () => {
      const user = userEvent.setup()
      const mockResult: RepositoryResponse = {
        id: 'clone-repo-1',
        name: 'react',
        slug: 'react',
        status: 'pending',
        source: 'clone',
        size_bytes: 12000,
        file_count: 50,
        primary_language: 'TypeScript',
        detected_languages: { TypeScript: 50 },
        frameworks: ['React'],
        created_at: '2026-08-01T00:00:00Z',
      }

      const cloneSpy = vi.spyOn(apiClient, 'cloneRepository').mockResolvedValue(mockResult)
      const onSuccess = vi.fn()

      renderWithProviders(<CloneForm onSuccess={onSuccess} />)

      const input = screen.getByLabelText(/git repository https url/i)
      const submitBtn = screen.getByRole('button', { name: /clone & ingest/i })

      await user.type(input, 'https://github.com/facebook/react.git')
      await user.click(submitBtn)

      await waitFor(() => {
        expect(cloneSpy).toHaveBeenCalledWith('https://github.com/facebook/react.git')
        expect(onSuccess).toHaveBeenCalledWith(mockResult)
      })
    })
  })

  describe('AddRepositoryModal', () => {
    it('renders tabs and allows switching between Upload and Clone', async () => {
      const user = userEvent.setup()
      renderWithProviders(<AddRepositoryModal isOpen={true} onClose={vi.fn()} />)

      expect(screen.getByText(/add new repository/i)).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /upload zip archive/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /clone git repository/i })).toBeInTheDocument()

      // Default tab is upload
      expect(screen.getByText(/click to browse or drag and drop your repository zip/i)).toBeInTheDocument()

      // Switch to clone tab
      const cloneTab = screen.getByRole('tab', { name: /clone git repository/i })
      await user.click(cloneTab)

      expect(screen.getByLabelText(/git repository https url/i)).toBeInTheDocument()
    })
  })
})
