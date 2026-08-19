import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils/cn'

export const progressBarVariants = cva(
  'h-full w-full flex-1 transition-all duration-300 ease-in-out',
  {
    variants: {
      variant: {
        primary: 'bg-indigo-500',
        success: 'bg-emerald-500',
        warning: 'bg-amber-500',
        error: 'bg-rose-500',
      },
    },
    defaultVariants: {
      variant: 'primary',
    },
  }
)

export interface ProgressBarProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof progressBarVariants> {
  value: number // 0 to 100
  max?: number
  label?: string
  showPercentage?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function ProgressBar({
  value,
  max = 100,
  label,
  showPercentage = false,
  size = 'md',
  variant,
  className,
  ...props
}: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, Math.round((value / max) * 100)))

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  }

  return (
    <div className={cn('w-full space-y-1.5', className)} {...props}>
      {(label || showPercentage) && (
        <div className="flex items-center justify-between text-xs text-slate-300 font-medium">
          {label && <span>{label}</span>}
          {showPercentage && <span>{percentage}%</span>}
        </div>
      )}
      <div
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={label || 'Progress'}
        className={cn(
          'relative w-full overflow-hidden rounded-full bg-slate-800 border border-slate-700/50',
          sizeClasses[size]
        )}
      >
        <div
          className={cn(progressBarVariants({ variant }))}
          style={{ transform: `translateX(-${100 - percentage}%)` }}
        />
      </div>
    </div>
  )
}
