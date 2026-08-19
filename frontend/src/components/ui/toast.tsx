import * as React from 'react'
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface ToastItem {
  id: string
  type: ToastType
  title?: string
  message: string
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

interface ToastContextValue {
  toasts: ToastItem[]
  addToast: (toast: Omit<ToastItem, 'id'>) => string
  removeToast: (id: string) => void
  success: (message: string, title?: string) => string
  error: (message: string, title?: string) => string
  info: (message: string, title?: string) => string
  warning: (message: string, title?: string) => string
}

const ToastContext = React.createContext<ToastContextValue | null>(null)

export function useToast() {
  const context = React.useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

export interface ToastProviderProps {
  children: React.ReactNode
  defaultDuration?: number
}

export function ToastProvider({
  children,
  defaultDuration = 4000,
}: ToastProviderProps) {
  const [toasts, setToasts] = React.useState<ToastItem[]>([])

  const removeToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const addToast = React.useCallback(
    (toast: Omit<ToastItem, 'id'>) => {
      const id = crypto.randomUUID ? crypto.randomUUID() : String(Date.now() + Math.random())
      const duration = toast.duration ?? defaultDuration

      setToasts((prev) => [...prev, { ...toast, id }])

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id)
        }, duration)
      }

      return id
    },
    [defaultDuration, removeToast]
  )

  const success = React.useCallback(
    (message: string, title?: string) => addToast({ type: 'success', message, title }),
    [addToast]
  )

  const error = React.useCallback(
    (message: string, title?: string) => addToast({ type: 'error', message, title }),
    [addToast]
  )

  const info = React.useCallback(
    (message: string, title?: string) => addToast({ type: 'info', message, title }),
    [addToast]
  )

  const warning = React.useCallback(
    (message: string, title?: string) => addToast({ type: 'warning', message, title }),
    [addToast]
  )

  return (
    <ToastContext.Provider
      value={{
        toasts,
        addToast,
        removeToast,
        success,
        error,
        info,
        warning,
      }}
    >
      {children}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </ToastContext.Provider>
  )
}

interface ToastContainerProps {
  toasts: ToastItem[]
  onDismiss: (id: string) => void
}

function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  if (toasts.length === 0) return null

  return (
    <div
      aria-live="polite"
      aria-atomic="true"
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
    >
      {toasts.map((toast) => (
        <ToastCard key={toast.id} toast={toast} onDismiss={() => onDismiss(toast.id)} />
      ))}
    </div>
  )
}

function ToastCard({
  toast,
  onDismiss,
}: {
  toast: ToastItem
  onDismiss: () => void
}) {
  const icons = {
    success: <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />,
    error: <AlertCircle className="h-5 w-5 text-rose-400 shrink-0" />,
    info: <Info className="h-5 w-5 text-sky-400 shrink-0" />,
    warning: <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />,
  }

  const borderClasses = {
    success: 'border-emerald-500/30 bg-slate-900/95',
    error: 'border-rose-500/30 bg-slate-900/95',
    info: 'border-sky-500/30 bg-slate-900/95',
    warning: 'border-amber-500/30 bg-slate-900/95',
  }

  return (
    <div
      role="status"
      className={cn(
        'pointer-events-auto flex items-start gap-3 rounded-lg border p-4 shadow-xl backdrop-blur-sm animate-in slide-in-from-bottom-2 fade-in-0 duration-200 text-slate-100',
        borderClasses[toast.type]
      )}
    >
      {icons[toast.type]}
      <div className="flex-1 min-w-0">
        {toast.title && (
          <h4 className="text-sm font-semibold text-slate-100">{toast.title}</h4>
        )}
        <p className="text-xs text-slate-300 break-words">{toast.message}</p>
        {toast.action && (
          <button
            type="button"
            onClick={toast.action.onClick}
            className="mt-2 text-xs font-semibold text-indigo-400 hover:text-indigo-300 underline"
          >
            {toast.action.label}
          </button>
        )}
      </div>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss toast"
        className="rounded p-1 text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}
