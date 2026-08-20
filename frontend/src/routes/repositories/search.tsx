import * as React from 'react'
import { useParams } from '@tanstack/react-router'
import { SearchBar } from '@/features/search/components/search-bar'
import { SearchResults } from '@/features/search/components/search-results'
import { useSearch } from '@/features/search/hooks/use-search'

export function RepositorySearchPage() {
  const { repoId } = useParams({ strict: false })
  const [currentQuery, setCurrentQuery] = React.useState('')
  const [hasSearched, setHasSearched] = React.useState(false)

  const {
    mutate: executeSearch,
    data: searchResponse,
    isPending,
    error,
  } = useSearch(repoId)

  const handleSearch = (query: string) => {
    if (!query.trim()) return
    setCurrentQuery(query)
    setHasSearched(true)
    executeSearch({ query, limit: 15 })
  }

  const handleRetry = () => {
    if (currentQuery) {
      executeSearch({ query: currentQuery, limit: 15 })
    }
  }

  if (!repoId) return null

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Search Input Bar */}
      <SearchBar
        onSearch={handleSearch}
        isLoading={isPending}
        initialQuery={currentQuery}
      />

      {/* Results or Empty/Loading/Error states */}
      <SearchResults
        results={searchResponse?.results ?? null}
        query={currentQuery}
        hasSearched={hasSearched}
        isLoading={isPending}
        error={error}
        repoId={repoId}
        onRetry={handleRetry}
      />
    </div>
  )
}
