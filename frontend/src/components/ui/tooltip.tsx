import * as React from 'react'
import { cn } from '@/lib/utils/cn'

export interface TooltipProps {
  content: React.ReactNode
  children: React.ReactElement<React.HTMLAttributes<HTMLElement>>
  side?: 'top' | 'bottom' | 'left' | 'right'
  delayDuration?: number
  className?: string
}

export function Tooltip({
  content,
  children,
  side = 'top',
  delayDuration = 200,
  className,
}: TooltipProps) {
  const [isVisible, setIsVisible] = React.useState(false)
  const timerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null)

  const show = () => {
    timerRef.current = setTimeout(() => setIsVisible(true), delayDuration)
  }

  const hide = () => {
    if (timerRef.current) clearTimeout(timerRef.current)
    setIsVisible(false)
  }

  const sideClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  }

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {React.cloneElement(children, {
        'aria-label': typeof content === 'string' ? content : undefined,
      } as React.HTMLAttributes<HTMLElement>)}
      {isVisible && (
        <div
          role="tooltip"
          className={cn(
            'pointer-events-none absolute z-50 whitespace-nowrap rounded-md bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-100 shadow-lg border border-slate-700 animate-in fade-in-0 zoom-in-95 duration-100',
            sideClasses[side],
            className
          )}
        >
          {content}
        </div>
      )}
    </div>
  )
}
