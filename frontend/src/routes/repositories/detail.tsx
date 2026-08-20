import { Outlet, useParams, useRouterState, Link } from '@tanstack/react-router'
import { ArrowLeft, FolderGit2 } from 'lucide-react'
import { useRepository } from '@/features/repositories/hooks/use-repository'
import { RepositoryOverview } from '@/features/repositories/components/repository-overview'
import { RepositoryTabs } from '@/features/repositories/components/repository-tabs'
import { useRepositoryProgress } from '@/features/processing/hooks/use-repository-progress'
import { ProcessingStepper } from '@/features/processing/components/processing-stepper'
import { Skeleton } from '@/components/ui/skeleton'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ErrorState } from '@/components/ui/error-state'
import { Button } from '@/components/ui/button'

export function RepositoryDetailPage() {
  const { repoId } = useParams({ strict: false })
  const routerState = useRouterState()
  const currentPath = routerState.location.pathname

  const {
    data: repository,
    isLoading,
    isError,
    error,
    refetch,
  } = useRepository(repoId)

  // Live pipeline progress — only active when not yet ready/error
  const progress = useRepositoryProgress(repoId, repository?.status ?? null)

  if (isLoading) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto" data-testid="repository-detail-skeleton">
        <div className="flex items-center justify-between pb-5 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <Skeleton className="h-9 w-9 rounded-lg" />
            <div className="space-y-2">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-32" />
            </div>
          </div>
          <Skeleton className="h-9 w-32 rounded-lg" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="h-28 bg-slate-900/40 border-slate-800 p-4 space-y-3">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-6 w-16" />
            </Card>
          ))}
        </div>

        <Card className="h-64 bg-slate-900/40 border-slate-800 p-6 space-y-4">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </Card>
      </div>
    )
  }

  if (isError || !repository) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-4">
        <ErrorState
          title="Repository not found"
          message={
            error?.message ||
            `Could not find repository with ID "${repoId}". It may have been deleted or the ID is invalid.`
          }
          onRetry={() => refetch()}
          retryText="Retry Loading"
        />
        <div className="pt-2">
          <Link to="/">
            <Button variant="secondary" size="sm" leftIcon={<ArrowLeft className="h-4 w-4" />}>
              Back to Repositories
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  // Live status from the SSE/polling hook takes precedence over the cached value
  const effectiveStatus = progress.status ?? repository.status
  const isProcessing = effectiveStatus !== 'ready' && effectiveStatus !== 'error'

  const isOverviewRoute =
    currentPath === `/repositories/${repoId}` || currentPath === `/repositories/${repoId}/`

  // While processing: show a focused processing view with header + stepper
  if (isProcessing) {
    return (
      <div className="space-y-6 max-w-3xl mx-auto">
        {/* Compact processing header */}
        <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
          <Link
            to="/"
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-900 hover:text-slate-100 transition-colors border border-slate-800"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600/15 border border-indigo-500/30 text-indigo-400">
            <FolderGit2 className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-100">{repository.name}</h1>
              <Badge variant="info" className="capitalize">
                {effectiveStatus}
              </Badge>
            </div>
            <p className="text-xs text-slate-400 font-mono">{repository.slug}</p>
          </div>
        </div>

        {/* Processing stepper */}
        <Card className="p-6 bg-slate-900/50 border-slate-800">
          <h2 className="text-sm font-semibold text-slate-200 mb-5">
            Pipeline Progress
          </h2>
          <ProcessingStepper
            status={effectiveStatus}
            progress={progress.progress}
            phase={progress.phase}
            errorMessage={progress.errorMessage}
          />
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto h-full flex flex-col">
      {/* Subnavigation Tabs */}
      <RepositoryTabs repository={{ ...repository, status: effectiveStatus }} />

      {/* Main Outlet / Overview Body */}
      <div className="flex-1 min-h-[400px]">
        {isOverviewRoute ? (
          <RepositoryOverview repository={repository} />
        ) : (
          <Outlet />
        )}
      </div>
    </div>
  )
}
