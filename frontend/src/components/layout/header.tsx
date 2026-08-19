import * as React from 'react'
import { Link, useRouterState } from '@tanstack/react-router'
import {
  ChevronRight,
  Sun,
  Moon,
  FolderGit2,
  GitBranch,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export interface HeaderProps {
  currentRepoName?: string
  currentRepoStatus?: string
}

export function Header({
  currentRepoName,
  currentRepoStatus,
}: HeaderProps) {
  const routerState = useRouterState()
  const currentPath = routerState.location.pathname
  const [theme, setTheme] = React.useState<'dark' | 'light'>('dark')

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(nextTheme)
    document.documentElement.setAttribute('data-theme', nextTheme)
  }

  // Parse path segments for breadcrumbs
  const segments = currentPath.split('/').filter(Boolean)
  const isRepoDetail = segments[0] === 'repositories' && segments.length >= 2
  const repoId = isRepoDetail ? segments[1] : null
  const subTab = isRepoDetail && segments.length >= 3 ? segments[2] : null

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-800 bg-slate-950/70 px-6 backdrop-blur-md sticky top-0 z-10 select-none">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumbs" className="flex items-center gap-2 text-sm text-slate-400">
        <Link
          to="/"
          className="flex items-center gap-1.5 hover:text-slate-200 transition-colors font-medium"
        >
          <FolderGit2 className="h-4 w-4" />
          <span>Repositories</span>
        </Link>

        {isRepoDetail && (
          <>
            <ChevronRight className="h-3.5 w-3.5 text-slate-600" />
            <Link
              to="/repositories/$repoId"
              params={{ repoId: repoId || '' }}
              className="flex items-center gap-1.5 hover:text-slate-200 transition-colors font-medium text-slate-200"
            >
              <GitBranch className="h-3.5 w-3.5 text-indigo-400" />
              <span className="truncate max-w-[200px]">{currentRepoName || repoId}</span>
            </Link>
          </>
        )}

        {subTab && (
          <>
            <ChevronRight className="h-3.5 w-3.5 text-slate-600" />
            <span className="font-semibold text-slate-100 capitalize">
              {subTab}
            </span>
          </>
        )}

        {currentPath === '/settings' && (
          <>
            <ChevronRight className="h-3.5 w-3.5 text-slate-600" />
            <span className="font-semibold text-slate-100">Settings</span>
          </>
        )}

        {currentPath === '/dev/kitchen-sink' && (
          <>
            <ChevronRight className="h-3.5 w-3.5 text-slate-600" />
            <span className="font-semibold text-amber-400">Kitchen Sink</span>
          </>
        )}
      </nav>

      {/* Header Actions */}
      <div className="flex items-center gap-3">
        {currentRepoStatus && (
          <Badge
            variant={
              currentRepoStatus === 'ready'
                ? 'success'
                : currentRepoStatus === 'error'
                  ? 'error'
                  : 'warning'
            }
            size="sm"
          >
            {currentRepoStatus.toUpperCase()}
          </Badge>
        )}

        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          className="text-slate-400 hover:text-slate-100"
        >
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </div>
    </header>
  )
}
