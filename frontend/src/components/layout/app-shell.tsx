import * as React from 'react'
import { Outlet } from '@tanstack/react-router'
import { Sidebar } from './sidebar'
import { Header } from './header'
import { ToastProvider } from '@/components/ui/toast'
import { ErrorState } from '@/components/ui/error-state'

interface ErrorBoundaryProps {
  children: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class RouteErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Route error boundary caught an error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-full min-h-[400px] items-center justify-center p-8">
          <ErrorState
            title="Application encountered an error"
            message={
              this.state.error?.message ||
              'An unexpected error occurred while rendering this page.'
            }
            onRetry={() => this.setState({ hasError: false, error: null })}
            retryText="Reload view"
          />
        </div>
      )
    }

    return this.props.children
  }
}

export interface AppShellProps {
  children?: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false)

  return (
    <ToastProvider>
      <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
        {/* Persistent Sidebar */}
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed((prev) => !prev)}
        />

        {/* Main Content Area */}
        <div className="flex flex-1 flex-col overflow-hidden min-w-0">
          <Header />
          <main className="flex-1 overflow-y-auto overflow-x-hidden bg-slate-950 p-6">
            <RouteErrorBoundary>
              {children || <Outlet />}
            </RouteErrorBoundary>
          </main>
        </div>
      </div>
    </ToastProvider>
  )
}
