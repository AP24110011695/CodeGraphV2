import * as React from 'react'
import { FolderGit2, Plus, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react'
import { RepositoryCard } from './repository-card'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { EmptyState } from '@/components/ui/empty-state'
import { ErrorState } from '@/components/ui/error-state'
import { Button } from '@/components/ui/button'
import { useRepositories } from '../hooks/use-repositories'

export interface RepositoryListProps {
  onAddRepository?: () => void
}

export function RepositoryList({ onAddRepository }: RepositoryListProps) {
  const [page, setPage] = React.useState(1)
  const pageSize = 12

  const { data, isLoading, isError, error, refetch, isFetching } = useRepositories({
    page,
    page_size: pageSize,
  })

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" data-testid="repository-skeletons">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i} className="h-44 border-slate-800 bg-slate-900/40 p-5 space-y-4">
            <CardHeader className="p-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Skeleton className="h-9 w-9 rounded-lg" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                </div>
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
            </CardHeader>
            <CardContent className="p-0 pt-4 space-y-3 border-t border-slate-800">
              <div className="flex justify-between">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-3 w-12" />
              </div>
              <div className="flex justify-between">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-3 w-24" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="py-12">
        <ErrorState
          title="Failed to load repositories"
          message={error?.message || 'An error occurred while fetching your repositories.'}
          onRetry={() => refetch()}
          retryText="Retry Request"
        />
      </div>
    )
  }

  const items = data?.items || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / pageSize)

  if (items.length === 0) {
    return (
      <div className="py-12">
        <EmptyState
          icon={<FolderGit2 className="h-10 w-10 text-indigo-400" />}
          title="No repositories ingested yet"
          description="Upload a zip file or clone from a Git repository to start analyzing code structure, dependencies, and generating graph intelligence."
          action={
            onAddRepository ? (
              <Button
                variant="primary"
                onClick={onAddRepository}
                leftIcon={<Plus className="h-4 w-4" />}
              >
                Add Your First Repository
              </Button>
            ) : undefined
          }
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Action Bar / Status */}
      <div className="flex items-center justify-between text-xs text-slate-400">
        <div>
          Showing <span className="font-semibold text-slate-200">{items.length}</span> of{' '}
          <span className="font-semibold text-slate-200">{total}</span> {total === 1 ? 'repository' : 'repositories'}
        </div>
        {isFetching && (
          <div className="flex items-center gap-1.5 text-indigo-400">
            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            <span>Updating...</span>
          </div>
        )}
      </div>

      {/* Grid of Repository Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {items.map((repo) => (
          <RepositoryCard key={repo.id} repository={repo} />
        ))}
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-slate-800 pt-4">
          <p className="text-xs text-slate-400">
            Page {page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              leftIcon={<ChevronLeft className="h-4 w-4" />}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              rightIcon={<ChevronRight className="h-4 w-4" />}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
