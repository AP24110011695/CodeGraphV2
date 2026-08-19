import { Link, useRouterState } from '@tanstack/react-router'
import {
  FolderGit2,
  Settings,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  GitGraph,
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'

export interface SidebarProps {
  collapsed?: boolean
  onToggleCollapse?: () => void
}

export function Sidebar({
  collapsed = false,
  onToggleCollapse,
}: SidebarProps) {
  const routerState = useRouterState()
  const currentPath = routerState.location.pathname

  const isDev = typeof import.meta !== 'undefined' && import.meta.env?.DEV

  const navItems = [
    {
      label: 'Repositories',
      href: '/',
      icon: <FolderGit2 className="h-5 w-5 shrink-0" />,
      active: currentPath === '/' || currentPath.startsWith('/repositories'),
    },
    {
      label: 'Settings',
      href: '/settings',
      icon: <Settings className="h-5 w-5 shrink-0" />,
      active: currentPath.startsWith('/settings'),
    },
    ...(isDev
      ? [
          {
            label: 'Kitchen Sink',
            href: '/dev/kitchen-sink',
            icon: <Sparkles className="h-5 w-5 shrink-0 text-amber-400" />,
            active: currentPath === '/dev/kitchen-sink',
          },
        ]
      : []),
  ]

  return (
    <aside
      aria-label="Main Navigation"
      className={cn(
        'relative flex flex-col border-r border-slate-800 bg-slate-950/90 text-slate-200 transition-all duration-300 ease-in-out shrink-0 select-none z-20',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-slate-800/80">
        <Link
          to="/"
          className="flex items-center gap-3 overflow-hidden text-slate-100 font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded-md p-1"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 shrink-0 shadow-sm">
            <GitGraph className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col truncate">
              <span className="text-sm font-bold tracking-tight text-slate-100">
                CodeGraph <span className="text-indigo-400">v2</span>
              </span>
              <span className="text-[10px] font-normal text-slate-400 truncate">
                AI Code Intelligence
              </span>
            </div>
          )}
        </Link>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1.5 p-3">
        {navItems.map((item) => (
          <Link
            key={item.href}
            to={item.href}
            className={cn(
              'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500',
              item.active
                ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/20 shadow-sm font-semibold'
                : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
            )}
            title={collapsed ? item.label : undefined}
          >
            {item.icon}
            {!collapsed && <span className="truncate">{item.label}</span>}
          </Link>
        ))}
      </nav>

      {/* Collapse Toggle Button */}
      {onToggleCollapse && (
        <div className="p-3 border-t border-slate-800/80">
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="flex w-full items-center justify-center gap-2 rounded-lg p-2 text-xs text-slate-400 hover:bg-slate-900 hover:text-slate-200 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="h-4 w-4" />
                <span>Collapse Sidebar</span>
              </>
            )}
          </button>
        </div>
      )}
    </aside>
  )
}
