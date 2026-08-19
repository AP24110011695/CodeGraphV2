import * as React from 'react'
import { cn } from '@/lib/utils/cn'

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'rectangular' | 'rounded' | 'circular'
}

export function Skeleton({
  className,
  variant = 'rounded',
  ...props
}: SkeletonProps) {
  const variantClasses = {
    rectangular: 'rounded-none',
    rounded: 'rounded-md',
    circular: 'rounded-full',
  }

  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn(
        'animate-pulse bg-slate-800/80 border border-slate-700/20',
        variantClasses[variant],
        className
      )}
      {...props}
    >
      <span className="sr-only">Loading...</span>
    </div>
  )
}
