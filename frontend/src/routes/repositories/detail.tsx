import { Link, Outlet, useParams, useRouterState } from '@tanstack/react-router'
import { FileCode2, GitGraph, Search, MessageSquare, ArrowLeft } from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import { mockRepositories } from '@/lib/api'

export function RepositoryDetailPage() {
  const { repoId } = useParams({ strict: false })
  const routerState = useRouterState()
  const currentPath = routerState.location.pathname

  const repo = mockRepositories.find((r) => r.id === repoId) || {
    id: repoId,
    name: repoId,
    primary_language: 'Python',
    file_count: 18,
  }

  const tabs = [
    {
      id: 'files',
      label: 'Files & Code',
      icon: <FileCode2 className="h-4 w-4" />,
      href: `/repositories/${repoId}/files`,
    },
    {
      id: 'graph',
      label: 'Dependency Graph',
      icon: <GitGraph className="h-4 w-4" />,
      href: `/repositories/${repoId}/graph`,
    },
    {
      id: 'search',
      label: 'Semantic Search',
      icon: <Search className="h-4 w-4" />,
      href: `/repositories/${repoId}/search`,
    },
    {
      id: 'chat',
      label: 'AI Assistant',
      icon: <MessageSquare className="h-4 w-4" />,
      href: `/repositories/${repoId}/chat`,
    },
  ]

  const isOverview = currentPath === `/repositories/${repoId}`

  return (
    <div className="space-y-6 max-w-7xl mx-auto h-full flex flex-col">
      {/* Repository Hub Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-900 hover:text-slate-100 transition-colors"
            title="Back to repositories"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-slate-100">{repo.name}</h1>
            <p className="text-xs text-slate-400">
              Repository ID: <code className="text-slate-300 font-mono">{repoId}</code>
            </p>
          </div>
        </div>
      </div>

      {/* Subnavigation Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-800/80">
        {tabs.map((tab) => {
          const isActive = currentPath.startsWith(tab.href)
          return (
            <Link
              key={tab.id}
              to={tab.href}
              className={cn(
                'flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all',
                isActive
                  ? 'border-indigo-500 text-indigo-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
              )}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </Link>
          )
        })}
      </div>

      {/* Tab Content Area */}
      <div className="flex-1 min-h-[400px]">
        {isOverview ? (
          <div className="p-6 rounded-xl border border-slate-800 bg-slate-900/40 text-center space-y-3">
            <h3 className="text-lg font-semibold text-slate-200">Repository Overview</h3>
            <p className="text-sm text-slate-400 max-w-md mx-auto">
              Select a tab above to explore files, visualize the dependency architecture, perform semantic code search, or chat with the AI assistant.
            </p>
          </div>
        ) : (
          <Outlet />
        )}
      </div>
    </div>
  )
}
