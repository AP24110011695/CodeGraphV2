import { AlertTriangle, Filter, RotateCcw, Sparkles } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { GraphMetrics } from '@/lib/api/types'
import { getLanguageColor } from './dependency-graph'

export interface GraphControlsProps {
  metrics: GraphMetrics
  availableLanguages: string[]
  selectedLanguages: string[]
  onToggleLanguage: (lang: string) => void
  onlyEntryPoints: boolean
  onToggleEntryPoints: (val: boolean) => void
  onResetView?: () => void
  className?: string
}

export function GraphControls({
  metrics,
  availableLanguages,
  selectedLanguages,
  onToggleLanguage,
  onlyEntryPoints,
  onToggleEntryPoints,
  onResetView,
  className,
}: GraphControlsProps) {
  return (
    <div className={className}>
      {/* Cycle warning banner if graph has cycles */}
      {metrics.has_cycles && (
        <div
          data-testid="cycle-warning-banner"
          className="mb-3 flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3.5 py-2 text-xs text-amber-300"
        >
          <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
          <span>
            <strong>Circular Dependencies Detected:</strong> {metrics.cycle_count}{' '}
            cycle{metrics.cycle_count === 1 ? '' : 's'} identified in the module
            import graph.
          </span>
        </div>
      )}

      {/* Control bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-900/70 p-3 backdrop-blur-sm">
        {/* Left: filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400">
            <Filter className="h-3.5 w-3.5" />
            <span>Languages:</span>
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            {availableLanguages.map((lang) => {
              const isSelected =
                selectedLanguages.length === 0 ||
                selectedLanguages.some((l) => l.toLowerCase() === lang.toLowerCase())
              const color = getLanguageColor(lang)

              return (
                <button
                  key={lang}
                  type="button"
                  onClick={() => onToggleLanguage(lang)}
                  className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium transition-all ${
                    isSelected
                      ? 'bg-slate-800 text-slate-200 border border-slate-700 shadow-sm'
                      : 'bg-slate-950 text-slate-500 border border-slate-900 opacity-60 hover:opacity-100'
                  }`}
                >
                  <span
                    className="h-2 w-2 rounded-full shrink-0"
                    style={{ backgroundColor: color }}
                  />
                  <span>{lang}</span>
                </button>
              )
            })}
          </div>

          <div className="h-4 w-px bg-slate-800 hidden sm:block" />

          {/* Entry points toggle */}
          <button
            type="button"
            onClick={() => onToggleEntryPoints(!onlyEntryPoints)}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
              onlyEntryPoints
                ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40'
                : 'bg-slate-800/60 text-slate-400 hover:text-slate-200 border border-slate-700/60'
            }`}
          >
            <Sparkles className="h-3 w-3 text-indigo-400" />
            <span>Only Entry Points ({metrics.entry_point_count})</span>
          </button>
        </div>

        {/* Right: stats & actions */}
        <div className="flex items-center gap-2">
          <Badge variant="default" className="text-[11px] font-mono">
            {metrics.node_count} nodes · {metrics.edge_count} edges
          </Badge>

          {onResetView && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onResetView}
              className="h-7 text-xs flex items-center gap-1"
              title="Reset camera zoom and pan"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Fit View</span>
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
