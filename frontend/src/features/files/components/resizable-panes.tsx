import * as React from 'react'
import { cn } from '@/lib/utils/cn'

export interface PaneConfig {
  id: string
  minWidth: number   // px
  defaultWidth: number // px — initial flex-basis
}

export interface ResizablePanesProps {
  panes: PaneConfig[]
  storageKey?: string
  children: React.ReactNode[]
  className?: string
}

/**
 * ResizablePanes — a simple drag-handle resize implementation using
 * pointer-events and CSS flex-basis. No extra library needed.
 *
 * Width state is persisted to localStorage (keyed by storageKey) so the
 * layout survives navigation and page refresh.
 */
export function ResizablePanes({
  panes,
  storageKey = 'codegraph:pane-widths',
  children,
  className,
}: ResizablePanesProps) {
  // Load persisted widths or fall back to defaults
  const [widths, setWidths] = React.useState<number[]>(() => {
    try {
      const saved = localStorage.getItem(storageKey)
      if (saved) {
        const parsed: number[] = JSON.parse(saved)
        if (Array.isArray(parsed) && parsed.length === panes.length) return parsed
      }
    } catch {
      // Ignore parse errors
    }
    return panes.map((p) => p.defaultWidth)
  })

  // Persist widths when they change
  React.useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(widths))
    } catch {
      // Ignore storage errors
    }
  }, [widths, storageKey])

  const containerRef = React.useRef<HTMLDivElement>(null)
  const dragState = React.useRef<{
    index: number
    startX: number
    startLeftWidth: number
    startRightWidth: number
  } | null>(null)

  const onPointerDown = React.useCallback(
    (e: React.PointerEvent<HTMLDivElement>, handleIndex: number) => {
      e.preventDefault()
      e.currentTarget.setPointerCapture?.(e.pointerId)

      const leftIdx = handleIndex
      const rightIdx = handleIndex + 1
      const clientX = e.clientX ?? (e.nativeEvent as MouseEvent)?.clientX ?? 0

      dragState.current = {
        index: handleIndex,
        startX: clientX,
        startLeftWidth: widths[leftIdx] ?? panes[leftIdx].defaultWidth,
        startRightWidth: widths[rightIdx] ?? panes[rightIdx].defaultWidth,
      }
    },
    [widths, panes]
  )

  const onPointerMove = React.useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragState.current) return

    const { index, startX, startLeftWidth, startRightWidth } = dragState.current
    const clientX = e.clientX ?? (e.nativeEvent as MouseEvent)?.clientX ?? 0
    const delta = clientX - startX
    const leftIdx = index
    const rightIdx = index + 1

    const minL = panes[leftIdx].minWidth
    const minR = panes[rightIdx].minWidth

    let newLeft = startLeftWidth + delta
    let newRight = startRightWidth - delta

    // Clamp to min widths
    if (newLeft < minL) {
      const overflow = minL - newLeft
      newLeft = minL
      newRight -= overflow
    }
    if (newRight < minR) {
      const overflow = minR - newRight
      newRight = minR
      newLeft -= overflow
    }

    setWidths((prev) => {
      const next = [...prev]
      next[leftIdx] = newLeft
      next[rightIdx] = newRight
      return next
    })
  }, [panes])

  const onPointerUp = React.useCallback(() => {
    dragState.current = null
  }, [])

  return (
    <div
      ref={containerRef}
      className={cn('flex overflow-hidden h-full', className)}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerLeave={onPointerUp}
    >
      {React.Children.toArray(children).map((child, idx) => (
        <React.Fragment key={panes[idx]?.id ?? idx}>
          <div
            style={{ flexBasis: `${widths[idx]}px`, flexShrink: 0, flexGrow: 0, minWidth: panes[idx]?.minWidth ?? 0 }}
            className="overflow-hidden"
          >
            {child}
          </div>

          {/* Drag handle between panes */}
          {idx < React.Children.count(children) - 1 && (
            <div
              role="separator"
              aria-label={`Resize pane ${idx + 1}`}
              className="w-1 shrink-0 bg-slate-800 hover:bg-indigo-500/60 active:bg-indigo-500 cursor-col-resize transition-colors"
              onPointerDown={(e) => onPointerDown(e, idx)}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  )
}
