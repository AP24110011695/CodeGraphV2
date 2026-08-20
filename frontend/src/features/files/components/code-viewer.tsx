import * as React from 'react'
import { BinaryIcon, AlertTriangle } from 'lucide-react'
import { CodeBlock } from '@/components/ui/code-block'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils/cn'
import type { FileDetail } from '@/lib/api/types'

export interface CodeViewerProps {
  file: FileDetail | null
  isLoading?: boolean
  error?: Error | null
  highlightLines?: number[]
  scrollToLine?: number | null
  className?: string
}

export interface CodeViewerHandle {
  scrollToLine: (line: number) => void
}

/**
 * CodeViewer renders syntax-highlighted source via Phase 4's CodeBlock.
 * Handles:
 *   - Loading skeleton
 *   - Binary-file placeholder (no crash)
 *   - Error state
 *   - `scrollToLine` prop for SymbolPanel scroll-and-highlight (Phase 11)
 */
export const CodeViewer = React.forwardRef<CodeViewerHandle, CodeViewerProps>(
  function CodeViewer(
    { file, isLoading = false, error = null, highlightLines = [], scrollToLine, className },
    ref
  ) {
    const containerRef = React.useRef<HTMLDivElement>(null)
    const [activeHighlightLines, setActiveHighlightLines] = React.useState<number[]>(
      highlightLines
    )

    // Expose an imperative handle so SymbolPanel can trigger scroll-to-line
    React.useImperativeHandle(ref, () => ({
      scrollToLine(line: number) {
        if (!containerRef.current) return

        // Approximate: each line renders at ~20px
        const approxLineHeight = 20
        containerRef.current.scrollTo({
          top: (line - 1) * approxLineHeight - 80,
          behavior: 'smooth',
        })
        // Flash-highlight the line for 2 seconds
        setActiveHighlightLines([line])
        setTimeout(() => setActiveHighlightLines([]), 2000)
      },
    }))

    // Sync external highlightLines prop
    React.useEffect(() => {
      setActiveHighlightLines(highlightLines)
    }, [highlightLines])

    // Scroll when scrollToLine prop changes
    React.useEffect(() => {
      if (scrollToLine && scrollToLine > 0 && containerRef.current) {
        const approxLineHeight = 20
        containerRef.current.scrollTo({
          top: (scrollToLine - 1) * approxLineHeight - 80,
          behavior: 'smooth',
        })
        setActiveHighlightLines([scrollToLine])
        setTimeout(() => setActiveHighlightLines([]), 2000)
      }
    }, [scrollToLine])

    if (isLoading) {
      return (
        <div className={cn('space-y-2 p-4', className)}>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
        </div>
      )
    }

    if (error) {
      return (
        <div
          className={cn(
            'flex flex-col items-center justify-center h-full p-8 text-center space-y-2',
            className
          )}
        >
          <AlertTriangle className="h-8 w-8 text-rose-400" />
          <p className="text-sm font-medium text-rose-300">Failed to load file</p>
          <p className="text-xs text-slate-500">{error.message}</p>
        </div>
      )
    }

    if (!file) {
      return (
        <div
          className={cn(
            'flex flex-col items-center justify-center h-full p-8 text-center text-slate-500 space-y-2',
            className
          )}
        >
          <p className="text-sm">Select a file from the tree to view its contents.</p>
        </div>
      )
    }

    // Binary file — render a clear placeholder, not a crash
    if (file.is_binary || file.content === null) {
      return (
        <div
          className={cn(
            'flex flex-col items-center justify-center h-full p-8 text-center space-y-3',
            className
          )}
          data-testid="binary-placeholder"
        >
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-slate-800 border border-slate-700">
            <BinaryIcon className="h-7 w-7 text-slate-400" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-300">Binary file</p>
            <p className="text-xs text-slate-500 mt-1">
              <code className="font-mono">{file.path}</code>
            </p>
            <p className="text-xs text-slate-500 mt-0.5">
              {file.size_bytes.toLocaleString()} bytes · content preview not available
            </p>
          </div>
        </div>
      )
    }

    return (
      <div ref={containerRef} className={cn('overflow-auto h-full', className)}>
        <CodeBlock
          code={file.content}
          language={file.language}
          filename={file.path}
          showLineNumbers
          highlightLines={activeHighlightLines}
          className="rounded-none border-0 min-h-full"
        />
      </div>
    )
  }
)
