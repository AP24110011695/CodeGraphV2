import * as React from 'react'
import {
  Braces,
  FunctionSquare,
  Box,
  Variable,
  Layers,
  Tag,
  ListTree,
  ChevronDown,
  ChevronRight,
  Hash,
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import { Skeleton } from '@/components/ui/skeleton'
import type { SymbolKind, SymbolResponse } from '@/lib/api/types'

// ─── Kind icon/label map ──────────────────────────────────────────────────────

const KIND_META: Record<
  SymbolKind,
  { label: string; icon: React.ReactNode; color: string }
> = {
  class: { label: 'Classes', icon: <Box className="h-3.5 w-3.5" />, color: 'text-amber-400' },
  function: {
    label: 'Functions',
    icon: <FunctionSquare className="h-3.5 w-3.5" />,
    color: 'text-indigo-400',
  },
  method: { label: 'Methods', icon: <Braces className="h-3.5 w-3.5" />, color: 'text-sky-400' },
  variable: {
    label: 'Variables',
    icon: <Variable className="h-3.5 w-3.5" />,
    color: 'text-emerald-400',
  },
  interface: {
    label: 'Interfaces',
    icon: <Layers className="h-3.5 w-3.5" />,
    color: 'text-purple-400',
  },
  type_alias: { label: 'Type Aliases', icon: <Tag className="h-3.5 w-3.5" />, color: 'text-rose-400' },
  enum: { label: 'Enums', icon: <ListTree className="h-3.5 w-3.5" />, color: 'text-orange-400' },
  constant: { label: 'Constants', icon: <Hash className="h-3.5 w-3.5" />, color: 'text-teal-400' },
}

function getKindMeta(kind: string) {
  return KIND_META[kind as SymbolKind] ?? {
    label: kind,
    icon: <Braces className="h-3.5 w-3.5" />,
    color: 'text-slate-400',
  }
}

// ─── SymbolPanel ──────────────────────────────────────────────────────────────

export interface SymbolPanelProps {
  symbols: SymbolResponse[]
  isLoading?: boolean
  onScrollToLine: (line: number) => void
  className?: string
}

interface SymbolGroupProps {
  kind: string
  symbols: SymbolResponse[]
  onScrollToLine: (line: number) => void
}

function SymbolGroup({ kind, symbols, onScrollToLine }: SymbolGroupProps) {
  const [open, setOpen] = React.useState(true)
  const meta = getKindMeta(kind)

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition-colors"
        aria-expanded={open}
      >
        <span className={meta.color}>{meta.icon}</span>
        <span>{meta.label}</span>
        <span className="ml-auto text-slate-600 text-[10px]">{symbols.length}</span>
        {open ? (
          <ChevronDown className="h-3 w-3 text-slate-600" />
        ) : (
          <ChevronRight className="h-3 w-3 text-slate-600" />
        )}
      </button>

      {open && (
        <ul className="pb-1">
          {symbols.map((sym) => (
            <li key={sym.id}>
              <button
                type="button"
                onClick={() => onScrollToLine(sym.start_line)}
                title={sym.docstring ?? sym.name}
                className="flex w-full items-start gap-2 px-4 py-1.5 text-xs text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors text-left group"
              >
                <span className={cn('shrink-0 mt-0.5', meta.color)}>{meta.icon}</span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono truncate group-hover:text-slate-100 text-slate-300">
                      {sym.name}
                    </span>
                    {sym.is_exported && (
                      <span className="shrink-0 text-[9px] font-semibold text-slate-600 uppercase tracking-wider border border-slate-700 px-1 rounded">
                        exp
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-slate-600 tabular-nums">
                    L{sym.start_line}–{sym.end_line}
                  </div>
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function SymbolPanel({
  symbols,
  isLoading = false,
  onScrollToLine,
  className,
}: SymbolPanelProps) {
  if (isLoading) {
    return (
      <div className={cn('p-3 space-y-3', className)}>
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-28" />
          </div>
        ))}
      </div>
    )
  }

  if (symbols.length === 0) {
    return (
      <div className={cn('p-4 text-center', className)}>
        <p className="text-xs text-slate-500 italic">No symbols found in this file.</p>
      </div>
    )
  }

  // Group symbols by kind preserving the order they appear in the file
  const grouped = new Map<string, SymbolResponse[]>()
  for (const sym of symbols) {
    if (!grouped.has(sym.kind)) grouped.set(sym.kind, [])
    grouped.get(sym.kind)!.push(sym)
  }

  return (
    <div className={cn('overflow-y-auto', className)}>
      {Array.from(grouped.entries()).map(([kind, syms]) => (
        <SymbolGroup
          key={kind}
          kind={kind}
          symbols={syms}
          onScrollToLine={onScrollToLine}
        />
      ))}
    </div>
  )
}
