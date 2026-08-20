import * as React from 'react'
import { FileCode2, Braces } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { ErrorState } from '@/components/ui/error-state'
import { FileTree, buildTree } from './file-tree'
import { CodeViewer, type CodeViewerHandle } from './code-viewer'
import { SymbolPanel } from './symbol-panel'
import { ResizablePanes } from './resizable-panes'
import { useFiles } from '../hooks/use-files'
import { useFileContent } from '../hooks/use-file-content'
import { useFileSymbols } from '../hooks/use-file-symbols'
import type { TreeFile } from './file-tree'

export interface FileExplorerProps {
  repoId: string
}

/**
 * FileExplorer composes three panes:
 *   [FileTree] | [CodeViewer] | [SymbolPanel]
 *
 * Selected-file state is local (useState) — no global store needed.
 * Pane widths are persisted via ResizablePanes' localStorage integration.
 */
export function FileExplorer({ repoId }: FileExplorerProps) {
  const [selectedFile, setSelectedFile] = React.useState<TreeFile | null>(null)
  const [scrollToLine, setScrollToLine] = React.useState<number | null>(null)
  const codeViewerRef = React.useRef<CodeViewerHandle>(null)

  const {
    data: fileList,
    isLoading: filesLoading,
    isError: filesError,
    error: filesErrorMsg,
    refetch: refetchFiles,
  } = useFiles(repoId)

  const {
    data: fileDetail,
    isLoading: fileContentLoading,
    error: fileContentError,
  } = useFileContent(repoId, selectedFile?.id)

  const { data: symbols = [], isLoading: symbolsLoading } = useFileSymbols(
    repoId,
    selectedFile?.id
  )

  const treeNodes = React.useMemo(
    () => buildTree(fileList?.items ?? []),
    [fileList]
  )

  // Auto-select the first file when the tree loads
  React.useEffect(() => {
    if (!selectedFile && fileList?.items && fileList.items.length > 0) {
      const first = fileList.items[0]
      setSelectedFile({
        type: 'file',
        id: first.id,
        name: first.path.split('/').at(-1) ?? first.path,
        path: first.path,
        language: first.language,
        size_bytes: first.size_bytes,
        line_count: first.line_count,
        is_binary: first.is_binary,
      })
    }
  }, [fileList, selectedFile])

  const handleScrollToLine = React.useCallback((line: number) => {
    // Use the imperative handle if available; also update state as backup
    if (codeViewerRef.current) {
      codeViewerRef.current.scrollToLine(line)
    } else {
      setScrollToLine(line)
    }
  }, [])

  if (filesLoading) {
    return (
      <div className="flex h-full gap-1">
        <div className="w-56 p-3 space-y-2 border-r border-slate-800">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-5" style={{ width: `${60 + (i % 3) * 15}%` }} />
          ))}
        </div>
        <div className="flex-1 p-4 space-y-2">
          <Skeleton className="h-6 w-48" />
          {Array.from({ length: 10 }).map((_, i) => (
            <Skeleton key={i} className="h-4" style={{ width: `${50 + (i % 5) * 10}%` }} />
          ))}
        </div>
      </div>
    )
  }

  if (filesError) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <ErrorState
          title="Could not load files"
          message={filesErrorMsg?.message ?? 'Failed to fetch the file list for this repository.'}
          onRetry={() => refetchFiles()}
        />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full border border-slate-800 rounded-lg overflow-hidden bg-slate-950">
      {/* Top bar */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-slate-800 bg-slate-900/80 shrink-0">
        <FileCode2 className="h-4 w-4 text-indigo-400" />
        <span className="text-xs font-semibold text-slate-300">File Explorer</span>
        {selectedFile && (
          <span className="ml-auto text-[11px] font-mono text-slate-500 truncate max-w-xs">
            {selectedFile.path}
          </span>
        )}
      </div>

      {/* Three-pane resizable layout */}
      <ResizablePanes
        panes={[
          { id: 'tree', minWidth: 140, defaultWidth: 220 },
          { id: 'viewer', minWidth: 300, defaultWidth: 640 },
          { id: 'symbols', minWidth: 140, defaultWidth: 220 },
        ]}
        storageKey="codegraph:file-explorer-panes"
        className="flex-1 min-h-0"
      >
        {/* Pane 1: File Tree */}
        <div className="h-full flex flex-col border-r border-slate-800 bg-slate-900/30">
          <div className="px-3 py-2 border-b border-slate-800/60 shrink-0">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              Files ({fileList?.total ?? 0})
            </span>
          </div>
          <FileTree
            nodes={treeNodes}
            selectedFileId={selectedFile?.id ?? null}
            onSelectFile={(file) => {
              setSelectedFile(file)
              setScrollToLine(null)
            }}
            className="flex-1 min-h-0 py-1"
          />
        </div>

        {/* Pane 2: Code Viewer */}
        <CodeViewer
          ref={codeViewerRef}
          file={fileDetail ?? null}
          isLoading={fileContentLoading}
          error={fileContentError instanceof Error ? fileContentError : null}
          scrollToLine={scrollToLine}
          className="h-full"
        />

        {/* Pane 3: Symbol Panel */}
        <div className="h-full flex flex-col border-l border-slate-800 bg-slate-900/30">
          <div className="px-3 py-2 border-b border-slate-800/60 shrink-0 flex items-center gap-1.5">
            <Braces className="h-3.5 w-3.5 text-indigo-400" />
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              Symbols
            </span>
          </div>
          <SymbolPanel
            symbols={symbols}
            isLoading={symbolsLoading && Boolean(selectedFile)}
            onScrollToLine={handleScrollToLine}
            className="flex-1 min-h-0"
          />
        </div>
      </ResizablePanes>
    </div>
  )
}
