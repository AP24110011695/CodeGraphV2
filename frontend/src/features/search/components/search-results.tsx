import { Search, Sparkles } from 'lucide-react'
import { EmptyState } from '@/components/ui/empty-state'
import { ErrorState } from '@/components/ui/error-state'
import { Skeleton } from '@/components/ui/skeleton'
import type { SearchResult } from '@/lib/api/types'
import { SearchResultCard } from './search-result-card'

export interface SearchResultsProps {
  results: SearchResult[] | null
  query: string
  hasSearched: boolean
  isLoading: boolean
  error?: Error | null
  repoId: string
  onRetry?: () => void
  className?: string
}

export function SearchResults({
  results,
  query,
  hasSearched,
  isLoading,
  error,
  repoId,
  onRetry,
  className,
}: SearchResultsProps) {
  if (isLoading) {
    return (
      <div className={`space-y-4 ${className || ''}`}>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Sparkles className="h-3.5 w-3.5 text-indigo-400 animate-pulse" />
          <span>Searching codebase via embeddings...</span>
        </div>
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 space-y-3"
          >
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-20" />
            </div>
            <Skeleton className="h-20 w-full" />
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className={`py-12 ${className || ''}`}>
        <ErrorState
          title="Search request failed"
          message={error.message || 'An error occurred while executing the search.'}
          onRetry={onRetry}
        />
      </div>
    )
  }

  if (!hasSearched) {
    return (
      <div className={`py-16 ${className || ''}`}>
        <EmptyState
          icon={<Search className="h-10 w-10 text-indigo-400/80" />}
          title="Semantic Code Search"
          description="Type natural language questions or technical queries to discover functions, classes, and architectural components across this entire repository."
        />
      </div>
    )
  }

  if (!results || results.length === 0) {
    return (
      <div className={`py-16 ${className || ''}`}>
        <EmptyState
          icon={<Search className="h-10 w-10 text-slate-500" />}
          title="No results found"
          description={`No matching code chunks were found for "${query}". Try refining your search query.`}
        />
      </div>
    )
  }

  return (
    <div className={`space-y-4 ${className || ''}`}>
      <div className="flex items-center justify-between text-xs text-slate-400 px-1">
        <span>
          Found <strong>{results.length}</strong> matching chunk{results.length === 1 ? '' : 's'} for{' '}
          <code className="font-mono text-indigo-300 font-semibold">"{query}"</code>
        </span>
      </div>

      <div className="space-y-3">
        {results.map((result, idx) => (
          <SearchResultCard
            key={result.chunk_id || idx}
            result={result}
            repoId={repoId}
            rank={idx + 1}
          />
        ))}
      </div>
    </div>
  )
}
