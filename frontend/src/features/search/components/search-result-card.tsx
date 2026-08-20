import { Link } from '@tanstack/react-router'
import { FileCode, Sparkles, ExternalLink } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { CodeBlock } from '@/components/ui/code-block'
import type { SearchResult } from '@/lib/api/types'
import { cn } from '@/lib/utils/cn'

export interface SearchResultCardProps {
  result: SearchResult
  repoId: string
  rank?: number
  className?: string
}

function detectLanguage(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase() || ''
  switch (ext) {
    case 'py':
      return 'python'
    case 'ts':
    case 'tsx':
      return 'typescript'
    case 'js':
    case 'jsx':
      return 'javascript'
    case 'go':
      return 'go'
    case 'rs':
      return 'rust'
    case 'java':
      return 'java'
    case 'md':
      return 'markdown'
    case 'json':
      return 'json'
    default:
      return 'text'
  }
}

export function SearchResultCard({
  result,
  repoId,
  rank,
  className,
}: SearchResultCardProps) {
  const language = detectLanguage(result.path)
  const scorePercent = Math.round(result.score * 100)

  // Determine lines to highlight in the snippet
  const highlightLines = Array.from(
    { length: Math.max(1, result.end_line - result.start_line + 1) },
    (_, i) => result.start_line + i
  )

  return (
    <div
      data-testid="search-result-card"
      className={cn(
        'rounded-lg border border-slate-800 bg-slate-900/60 overflow-hidden hover:border-slate-700 transition-colors',
        className
      )}
    >
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 bg-slate-900/90 border-b border-slate-800">
        <div className="flex items-center gap-2 min-w-0">
          {rank !== undefined && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-800 text-[10px] font-mono font-semibold text-slate-400">
              {rank}
            </span>
          )}
          <FileCode className="h-4 w-4 text-indigo-400 shrink-0" />
          <span className="font-mono text-xs font-semibold text-slate-200 truncate">
            {result.path}
          </span>
          <span className="text-[11px] font-mono text-slate-500 shrink-0">
            L{result.start_line}–{result.end_line}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Match relevance badge */}
          <div className="flex items-center gap-1 text-[11px] font-mono font-semibold text-indigo-300 bg-indigo-950/60 border border-indigo-500/30 px-2 py-0.5 rounded">
            <Sparkles className="h-3 w-3 text-indigo-400" />
            <span>{scorePercent}% match</span>
          </div>

          <Badge variant="default" className="text-[10px] uppercase font-sans">
            {result.chunk_type || 'code'}
          </Badge>

          {/* Jump to Files tab link */}
          <Link
            to="/repositories/$repoId/files"
            params={{ repoId }}
            className="flex items-center gap-1 text-xs text-slate-400 hover:text-indigo-300 transition-colors ml-1"
            title="Open file in explorer"
          >
            <span>Open</span>
            <ExternalLink className="h-3 w-3" />
          </Link>
        </div>
      </div>

      {/* Code Snippet */}
      <div className="overflow-x-auto text-xs">
        <CodeBlock
          code={result.content}
          language={language}
          filename={result.path}
          showLineNumbers
          highlightLines={highlightLines}
          className="rounded-none border-0 m-0"
        />
      </div>
    </div>
  )
}
