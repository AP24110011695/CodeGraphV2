import { Link } from '@tanstack/react-router'
import {
  X,
  FileCode,
  ArrowRight,
  ArrowLeft,
  Braces,
  ExternalLink,
  Sparkles,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useGraphNode } from '../hooks/use-graph-node'

export interface NodeDetailPanelProps {
  repoId: string
  nodeId: string | null
  onClose: () => void
  className?: string
}

export function NodeDetailPanel({
  repoId,
  nodeId,
  onClose,
  className,
}: NodeDetailPanelProps) {
  const { data: detail, isLoading, error } = useGraphNode(repoId, nodeId)

  if (!nodeId) return null

  return (
    <div
      data-testid="node-detail-panel"
      className={`flex flex-col h-full bg-slate-900 border-l border-slate-800 p-4 overflow-y-auto text-slate-200 ${
        className || 'w-80 sm:w-96'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 pb-3 border-b border-slate-800 shrink-0">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 text-xs text-indigo-400 font-semibold uppercase tracking-wider mb-1">
            <FileCode className="h-3.5 w-3.5" />
            <span>File Details</span>
            {detail?.metrics.is_entry_point && (
              <span className="flex items-center gap-1 text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30 px-1.5 py-0.5 rounded ml-auto">
                <Sparkles className="h-2.5 w-2.5" /> Entry Point
              </span>
            )}
          </div>
          <h3
            className="font-mono text-sm font-semibold text-slate-100 break-all"
            title={detail?.path}
          >
            {detail?.path || nodeId}
          </h3>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="h-7 w-7 p-0 shrink-0 text-slate-400 hover:text-slate-100"
          aria-label="Close detail panel"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {isLoading && (
        <div className="space-y-4 py-4">
          <Skeleton className="h-5 w-32" />
          <div className="grid grid-cols-2 gap-2">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      )}

      {error && (
        <div className="py-6 text-center text-xs text-rose-400">
          Failed to load details for this node.
        </div>
      )}

      {detail && (
        <div className="space-y-4 pt-3 text-xs">
          {/* Quick Metrics */}
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-slate-950/60 border border-slate-800 rounded p-2 text-center">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">
                Imports (Out)
              </span>
              <span className="font-mono text-sm font-semibold text-slate-200">
                {detail.metrics.out_degree}
              </span>
            </div>
            <div className="bg-slate-950/60 border border-slate-800 rounded p-2 text-center">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">
                Imported By (In)
              </span>
              <span className="font-mono text-sm font-semibold text-slate-200">
                {detail.metrics.in_degree}
              </span>
            </div>
            <div className="bg-slate-950/60 border border-slate-800 rounded p-2 text-center">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">
                PageRank
              </span>
              <span className="font-mono text-sm font-semibold text-indigo-400">
                {detail.metrics.pagerank?.toFixed(3) ?? '0.000'}
              </span>
            </div>
          </div>

          {/* Jump to Files Tab action */}
          <div>
            <Link
              to="/repositories/$repoId/files"
              params={{ repoId }}
              className="flex items-center justify-center gap-1.5 w-full py-1.5 px-3 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition-colors shadow-sm"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              <span>View in Files Tab</span>
            </Link>
          </div>

          {/* Symbols */}
          {detail.symbols && detail.symbols.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 font-semibold text-slate-300 pb-1.5 border-b border-slate-800/80">
                <Braces className="h-3.5 w-3.5 text-indigo-400" />
                <span>Defined Symbols ({detail.symbols.length})</span>
              </div>
              <ul className="mt-2 space-y-1.5 max-h-36 overflow-y-auto pr-1">
                {detail.symbols.map((sym) => (
                  <li
                    key={sym.id}
                    className="flex items-center justify-between gap-2 p-1.5 rounded bg-slate-950/40 border border-slate-800/60 font-mono text-[11px]"
                  >
                    <span className="text-slate-200 truncate">{sym.name}</span>
                    <Badge variant="default" className="text-[9px] uppercase px-1 py-0">
                      {sym.kind}
                    </Badge>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Dependencies (Imports) */}
          <div>
            <div className="flex items-center gap-1.5 font-semibold text-slate-300 pb-1.5 border-b border-slate-800/80">
              <ArrowRight className="h-3.5 w-3.5 text-sky-400" />
              <span>Dependencies ({detail.dependencies.length})</span>
            </div>
            {detail.dependencies.length === 0 ? (
              <p className="text-[11px] text-slate-500 italic mt-1.5">
                No outbound imports.
              </p>
            ) : (
              <ul className="mt-2 space-y-1.5 max-h-36 overflow-y-auto pr-1">
                {detail.dependencies.map((dep, idx) => (
                  <li
                    key={idx}
                    className="p-1.5 rounded bg-slate-950/40 border border-slate-800/60 text-[11px]"
                  >
                    <div className="font-mono text-slate-200 truncate">{dep.path}</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      imported <code className="text-sky-300 font-mono">{dep.import_name}</code>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Dependents (Imported by) */}
          <div>
            <div className="flex items-center gap-1.5 font-semibold text-slate-300 pb-1.5 border-b border-slate-800/80">
              <ArrowLeft className="h-3.5 w-3.5 text-emerald-400" />
              <span>Dependents ({detail.dependents.length})</span>
            </div>
            {detail.dependents.length === 0 ? (
              <p className="text-[11px] text-slate-500 italic mt-1.5">
                No other modules import this file.
              </p>
            ) : (
              <ul className="mt-2 space-y-1.5 max-h-36 overflow-y-auto pr-1">
                {detail.dependents.map((dep, idx) => (
                  <li
                    key={idx}
                    className="p-1.5 rounded bg-slate-950/40 border border-slate-800/60 text-[11px]"
                  >
                    <div className="font-mono text-slate-200 truncate">{dep.path}</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      via <code className="text-emerald-300 font-mono">{dep.import_name}</code>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
