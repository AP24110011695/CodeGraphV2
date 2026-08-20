import * as React from 'react'
import { Search, X, Clock, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils/cn'

export interface SearchBarProps {
  onSearch: (query: string) => void
  isLoading?: boolean
  initialQuery?: string
  placeholder?: string
  className?: string
}

const STORAGE_KEY = 'codegraph:recent-searches'

export function SearchBar({
  onSearch,
  isLoading = false,
  initialQuery = '',
  placeholder = 'Search code, functions, classes, and logic (e.g. "JWT token validation")...',
  className,
}: SearchBarProps) {
  const [query, setQuery] = React.useState(initialQuery)
  const [recentQueries, setRecentQueries] = React.useState<string[]>(() => {
    try {
      const saved = sessionStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed)) return parsed
      }
    } catch {
      // Ignore parse error
    }
    return []
  })

  const saveRecentQuery = (q: string) => {
    const trimmed = q.trim()
    if (!trimmed) return
    setRecentQueries((prev) => {
      const next = [trimmed, ...prev.filter((item) => item !== trimmed)].slice(0, 6)
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      } catch {
        // Ignore storage error
      }
      return next
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || isLoading) return
    saveRecentQuery(query)
    onSearch(query.trim())
  }

  const handleSelectRecent = (q: string) => {
    setQuery(q)
    saveRecentQuery(q)
    onSearch(q)
  }

  const handleClear = () => {
    setQuery('')
  }

  return (
    <div className={cn('space-y-2', className)}>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            className="pl-10 pr-10 h-11 bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500 rounded-lg focus-visible:ring-indigo-500"
            disabled={isLoading}
            aria-label="Semantic search query"
          />
          {query && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 p-1"
              aria-label="Clear search input"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        <Button
          type="submit"
          variant="primary"
          disabled={!query.trim() || isLoading}
          className="h-11 px-5 flex items-center gap-1.5 shrink-0"
        >
          <span>Search</span>
          <ArrowRight className="h-4 w-4" />
        </Button>
      </form>

      {/* Recent queries */}
      {recentQueries.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto py-1 text-xs text-slate-400">
          <span className="flex items-center gap-1 text-[11px] text-slate-500 shrink-0">
            <Clock className="h-3 w-3" /> Recent:
          </span>
          <div className="flex items-center gap-1.5 flex-wrap">
            {recentQueries.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelectRecent(q)}
                className="px-2.5 py-0.5 rounded-full bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-slate-300 text-[11px] truncate max-w-xs transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
