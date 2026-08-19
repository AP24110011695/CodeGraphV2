import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils/cn'

export const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-indigo-600/20 text-indigo-300 border-indigo-500/30',
        secondary:
          'border-transparent bg-slate-800 text-slate-300 border-slate-700',
        success:
          'border-emerald-500/30 bg-emerald-500/15 text-emerald-300',
        warning:
          'border-amber-500/30 bg-amber-500/15 text-amber-300',
        error:
          'border-rose-500/30 bg-rose-500/15 text-rose-300',
        info:
          'border-sky-500/30 bg-sky-500/15 text-sky-300',
        outline:
          'border-slate-700 text-slate-300 bg-transparent',
      },
      size: {
        sm: 'px-2 py-0.2 text-[10px]',
        md: 'px-2.5 py-0.5 text-xs',
        lg: 'px-3 py-1 text-sm',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(badgeVariants({ variant, size }), className)}
        {...props}
      />
    )
  }
)

Badge.displayName = 'Badge'
