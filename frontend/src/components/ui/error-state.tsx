import * as React from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import { Button } from './button'

export interface ErrorStateProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode
  title?: string
  message: string
  onRetry?: () => void
  retryText?: string
  isRetrying?: boolean
}

export function ErrorState({
  icon = <AlertTriangle className="h-8 w-8 text-rose-400" />,
  title = 'Something went wrong',
  message,
  onRetry,
  retryText = 'Try again',
  isRetrying = false,
  className,
  ...props
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        'flex flex-col items-center justify-center p-8 text-center rounded-xl border border-rose-900/40 bg-rose-950/20 text-slate-200',
        className
      )}
      {...props}
    >
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-rose-900/30 border border-rose-800/50">
        {icon}
      </div>
      <h3 className="text-base font-semibold text-rose-200">{title}</h3>
      <p className="mt-1 text-sm text-rose-300/80 max-w-sm">{message}</p>
      {onRetry && (
        <div className="mt-4">
          <Button
            variant="secondary"
            size="sm"
            onClick={onRetry}
            isLoading={isRetrying}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            {retryText}
          </Button>
        </div>
      )}
    </div>
  )
}
