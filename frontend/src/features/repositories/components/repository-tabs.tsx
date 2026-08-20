import { Link, useRouterState } from '@tanstack/react-router'
import {
  FileCode2,
  GitGraph,
  Search,
  MessageSquare,
  LayoutDashboard,
  Lock,
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import { Tooltip } from '@/components/ui/tooltip'
import type { RepositoryResponse } from '@/lib/api/types'

export interface RepositoryTabsProps {
  repository: RepositoryResponse
}

export function RepositoryTabs({ repository }: RepositoryTabsProps) {
  const routerState = useRouterState()
  const currentPath = routerState.location.pathname
  const repoId = repository.id
  const isReady = repository.status === 'ready'

  const tabs = [
    {
      id: 'overview',
      label: 'Overview',
      icon: <LayoutDashboard className="h-4 w-4" />,
      href: `/repositories/${repoId}`,
      exact: true,
      requiresReady: false,
    },
    {
      id: 'files',
      label: 'Files & Code',
      icon: <FileCode2 className="h-4 w-4" />,
      href: `/repositories/${repoId}/files`,
      exact: false,
      requiresReady: false,
    },
    {
      id: 'graph',
      label: 'Dependency Graph',
      icon: <GitGraph className="h-4 w-4" />,
      href: `/repositories/${repoId}/graph`,
      exact: false,
      requiresReady: true,
    },
    {
      id: 'search',
      label: 'Semantic Search',
      icon: <Search className="h-4 w-4" />,
      href: `/repositories/${repoId}/search`,
      exact: false,
      requiresReady: true,
    },
    {
      id: 'chat',
      label: 'AI Assistant',
      icon: <MessageSquare className="h-4 w-4" />,
      href: `/repositories/${repoId}/chat`,
      exact: false,
      requiresReady: true,
    },
  ]

  return (
    <div
      role="tablist"
      aria-label="Repository navigation tabs"
      className="flex items-center gap-1 border-b border-slate-800/80 overflow-x-auto select-none"
    >
      {tabs.map((tab) => {
        const isActive = tab.exact
          ? currentPath === tab.href
          : currentPath.startsWith(tab.href)

        const isDisabled = tab.requiresReady && !isReady

        if (isDisabled) {
          return (
            <Tooltip
              key={tab.id}
              content={`Unlocked once processing is complete (currently: ${repository.status})`}
            >
              <div
                role="tab"
                aria-disabled="true"
                className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 border-transparent text-slate-600 cursor-not-allowed opacity-60"
              >
                {tab.icon}
                <span>{tab.label}</span>
                <Lock className="h-3 w-3 ml-0.5 text-slate-600" />
              </div>
            </Tooltip>
          )
        }

        return (
          <Link
            key={tab.id}
            to={tab.href}
            role="tab"
            aria-selected={isActive}
            className={cn(
              'flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded-t-md',
              isActive
                ? 'border-indigo-500 text-indigo-400 font-semibold bg-indigo-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
            )}
          >
            {tab.icon}
            <span>{tab.label}</span>
          </Link>
        )
      })}
    </div>
  )
}
