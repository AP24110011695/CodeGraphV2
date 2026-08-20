import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SearchBar } from './components/search-bar'
import { SearchResults } from './components/search-results'
import { SearchResultCard } from './components/search-result-card'
import type { SearchResult } from '@/lib/api/types'

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

const mockResults: SearchResult[] = [
  {
    chunk_id: 'c1',
    file_id: 'f1',
    path: 'app/services/auth.py',
    content: 'def verify_token(token: str):\n    return jwt.decode(token)',
    start_line: 10,
    end_line: 11,
    score: 0.95,
    chunk_type: 'function',
    symbol_id: 's1',
  },
  {
    chunk_id: 'c2',
    file_id: 'f2',
    path: 'app/api/auth_routes.py',
    content: '@router.post("/login")\ndef login(creds: Credentials):\n    return auth.login(creds)',
    start_line: 20,
    end_line: 22,
    score: 0.85,
    chunk_type: 'endpoint',
    symbol_id: 's2',
  },
]

describe('Search Feature Components', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  describe('SearchBar', () => {
    it('submits query and calls onSearch callback', async () => {
      const user = userEvent.setup()
      const onSearch = vi.fn()

      render(<SearchBar onSearch={onSearch} />)

      const input = screen.getByRole('textbox', { name: /semantic search query/i })
      await user.type(input, 'JWT auth')

      const submitButton = screen.getByRole('button', { name: /^search$/i })
      await user.click(submitButton)

      expect(onSearch).toHaveBeenCalledWith('JWT auth')
    })

    it('populates and clicks recent query pill', async () => {
      const user = userEvent.setup()
      const onSearch = vi.fn()

      render(<SearchBar onSearch={onSearch} />)

      const input = screen.getByRole('textbox', { name: /semantic search query/i })
      await user.type(input, 'first query')
      await user.click(screen.getByRole('button', { name: /^search$/i }))

      expect(screen.getByText('first query')).toBeInTheDocument()

      // Click the recent pill
      await user.click(screen.getByText('first query'))
      expect(onSearch).toHaveBeenCalledWith('first query')
    })

    it('clears query input when X button is clicked', async () => {
      const user = userEvent.setup()
      render(<SearchBar onSearch={vi.fn()} initialQuery="something" />)

      const clearBtn = screen.getByRole('button', { name: /clear search input/i })
      await user.click(clearBtn)

      const input = screen.getByRole('textbox', { name: /semantic search query/i })
      expect(input).toHaveValue('')
    })
  })

  describe('SearchResultCard', () => {
    it('renders file path, score match percentage, and line range', () => {
      render(
        <SearchResultCard
          result={mockResults[0]}
          repoId="repo-123"
          rank={1}
        />
      )

      expect(screen.getAllByText('app/services/auth.py').length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText('95% match')).toBeInTheDocument()
      expect(screen.getByText('L10–11')).toBeInTheDocument()
      expect(screen.getByText('function')).toBeInTheDocument()
    })
  })

  describe('SearchResults', () => {
    it('renders initial empty state before first search', () => {
      render(
        <SearchResults
          results={null}
          query=""
          hasSearched={false}
          isLoading={false}
          repoId="repo-123"
        />
      )

      expect(screen.getByText('Semantic Code Search')).toBeInTheDocument()
    })

    it('renders no results empty state when query returns empty list', () => {
      render(
        <SearchResults
          results={[]}
          query="nonexistent query"
          hasSearched={true}
          isLoading={false}
          repoId="repo-123"
        />
      )

      expect(screen.getByText('No results found')).toBeInTheDocument()
      expect(screen.getByText(/nonexistent query/i)).toBeInTheDocument()
    })

    it('renders list of search result cards on successful search', () => {
      render(
        <SearchResults
          results={mockResults}
          query="JWT auth"
          hasSearched={true}
          isLoading={false}
          repoId="repo-123"
        />
      )

      expect(screen.getAllByTestId('search-result-card')).toHaveLength(2)
      expect(screen.getAllByText('app/services/auth.py').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('app/api/auth_routes.py').length).toBeGreaterThanOrEqual(1)
    })

    it('renders error state on search failure', () => {
      const onRetry = vi.fn()
      render(
        <SearchResults
          results={null}
          query="failing query"
          hasSearched={true}
          isLoading={false}
          error={new Error('Vector index connection failed')}
          repoId="repo-123"
          onRetry={onRetry}
        />
      )

      expect(screen.getByText('Search request failed')).toBeInTheDocument()
      expect(screen.getByText('Vector index connection failed')).toBeInTheDocument()
    })
  })
})
