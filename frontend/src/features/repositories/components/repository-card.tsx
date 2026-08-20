import { Link } from '@tanstack/react-router'
import { FolderGit2, UploadCloud, GitBranch, FileCode, Calendar } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { RepositoryListItem, RepositoryStatus } from '@/lib/api/types'

export interface RepositoryCardProps {
  repository: RepositoryListItem & { primary_language?: string | null }
}

function getStatusBadgeVariant(status: RepositoryStatus): 'success' | 'warning' | 'error' | 'info' | 'secondary' {
  switch (status) {
    case 'ready':
      return 'success'
    case 'ingesting':
    case 'parsing':
    case 'indexing':
      return 'info'
    case 'pending':
      return 'warning'
    case 'error':
      return 'error'
    default:
      return 'secondary'
  }
}

export function RepositoryCard({ repository }: RepositoryCardProps) {
  const formattedDate = new Date(repository.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

  return (
    <Link
      to="/repositories/$repoId"
      params={{ repoId: repository.id }}
      className="block group focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded-xl"
    >
      <Card className="h-full hover:border-slate-700 transition-all duration-200 hover:shadow-lg hover:shadow-indigo-500/5 bg-slate-900/60 backdrop-blur-sm border-slate-800">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 group-hover:border-indigo-500/40 group-hover:bg-indigo-600/20 transition-colors">
                <FolderGit2 className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <CardTitle className="text-base truncate group-hover:text-indigo-400 transition-colors">
                  {repository.name}
                </CardTitle>
                <CardDescription className="text-xs truncate font-mono">
                  {repository.slug}
                </CardDescription>
              </div>
            </div>
            <Badge variant={getStatusBadgeVariant(repository.status)} size="sm" className="capitalize shrink-0">
              {repository.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 pt-0">
          <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
            <div className="flex items-center gap-1.5">
              <FileCode className="h-3.5 w-3.5 text-slate-500" />
              <span>{repository.file_count} {repository.file_count === 1 ? 'file' : 'files'}</span>
            </div>
            <div className="flex items-center gap-1.5">
              {repository.source === 'upload' ? (
                <span className="flex items-center gap-1 text-slate-400" title="Source: ZIP Upload">
                  <UploadCloud className="h-3.5 w-3.5 text-slate-500" />
                  ZIP
                </span>
              ) : (
                <span className="flex items-center gap-1 text-slate-400" title="Source: Git Clone">
                  <GitBranch className="h-3.5 w-3.5 text-slate-500" />
                  Git
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-500">
            <span>{repository.primary_language || 'Polyglot'}</span>
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3 text-slate-600" />
              {formattedDate}
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
