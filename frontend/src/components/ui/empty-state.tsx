import * as React from 'react'
import { FolderOpen } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
}

export function EmptyState({
  icon = <FolderOpen className="h-10 w-10 text-slate-500" />,
  title,
  description,
  action,
  className,
  ...props
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-8 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/40',
        className
      )}
      {...props}
    >
      <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-slate-800/80 border border-slate-700/60 text-slate-400">
        {icon}
      </div>
      <h3 className="text-base font-semibold text-slate-200">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-slate-400 max-w-sm">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
