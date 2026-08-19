import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils/cn'

export const spinnerVariants = cva(
  'inline-block animate-spin rounded-full border-solid border-current border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]',
  {
    variants: {
      size: {
        sm: 'h-4 w-4 border-2',
        md: 'h-6 w-6 border-2',
        lg: 'h-8 w-8 border-3',
        xl: 'h-12 w-12 border-4',
      },
      color: {
        current: 'text-current',
        primary: 'text-indigo-500',
        muted: 'text-slate-400',
        white: 'text-white',
      },
    },
    defaultVariants: {
      size: 'md',
      color: 'current',
    },
  }
)

export interface SpinnerProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, 'color'>,
    VariantProps<typeof spinnerVariants> {
  label?: string
}

export const Spinner = React.forwardRef<HTMLDivElement, SpinnerProps>(
  ({ className, size, color, label = 'Loading...', ...props }, ref) => {
    return (
      <div
        ref={ref}
        role="status"
        aria-label={label}
        className={cn(spinnerVariants({ size, color, className }))}
        {...props}
      >
        <span className="sr-only">{label}</span>
      </div>
    )
  }
)

Spinner.displayName = 'Spinner'
