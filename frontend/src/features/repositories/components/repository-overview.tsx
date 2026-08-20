import * as React from 'react'
import { useNavigate, Link } from '@tanstack/react-router'
import {
  FolderGit2,
  Trash2,
  FileCode,
  Layers,
  Calendar,
  UploadCloud,
  GitBranch,
  HardDrive,
  Code2,
  AlertTriangle,
  ArrowLeft,
} from 'lucide-react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
  ModalFooter,
} from '@/components/ui/modal'
import { useToast } from '@/components/ui/toast'
import { useDeleteRepository } from '../hooks/use-delete-repository'
import type { RepositoryResponse, RepositoryStatus } from '@/lib/api/types'

export interface RepositoryOverviewProps {
  repository: RepositoryResponse
}

function getStatusBadgeVariant(
  status: RepositoryStatus
): 'success' | 'warning' | 'error' | 'info' | 'secondary' {
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

function formatBytes(bytes: number): string {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export function RepositoryOverview({ repository }: RepositoryOverviewProps) {
  const navigate = useNavigate()
  const toast = useToast()
  const [isDeleteModalOpen, setIsDeleteModalOpen] = React.useState(false)

  const deleteMutation = useDeleteRepository()

  const formattedDate = new Date(repository.created_at).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(repository.id)
      toast.success(
        `Repository "${repository.name}" has been deleted.`,
        'Repository Deleted'
      )
      setIsDeleteModalOpen(false)
      navigate({ to: '/' })
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error ? err.message : 'Failed to delete repository.'
      toast.error(errorMsg, 'Deletion Failed')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="flex items-center gap-3.5">
          <Link
            to="/"
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-900 hover:text-slate-100 transition-colors border border-slate-800"
            title="Back to repositories list"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-600/15 border border-indigo-500/30 text-indigo-400 shadow-sm">
            <FolderGit2 className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-2xl font-bold text-slate-100">{repository.name}</h1>
              <Badge variant={getStatusBadgeVariant(repository.status)} className="capitalize">
                {repository.status}
              </Badge>
              <Badge variant="outline" className="text-slate-400">
                {repository.source === 'upload' ? (
                  <span className="flex items-center gap-1">
                    <UploadCloud className="h-3 w-3" /> ZIP Archive
                  </span>
                ) : (
                  <span className="flex items-center gap-1">
                    <GitBranch className="h-3 w-3" /> Git Remote
                  </span>
                )}
              </Badge>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              {repository.slug} • ID: {repository.id}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setIsDeleteModalOpen(true)}
            leftIcon={<Trash2 className="h-4 w-4" />}
          >
            Delete Repository
          </Button>
        </div>
      </div>

      {/* Overview Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1.5 text-xs">
              <Code2 className="h-4 w-4 text-indigo-400" />
              Primary Language
            </CardDescription>
            <CardTitle className="text-xl font-bold text-slate-100">
              {repository.primary_language || 'Polyglot'}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-400 pt-0">
            {repository.detected_languages && Object.keys(repository.detected_languages).length > 0
              ? `${Object.keys(repository.detected_languages).length} languages detected`
              : 'Single language'}
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1.5 text-xs">
              <FileCode className="h-4 w-4 text-sky-400" />
              Total Source Files
            </CardDescription>
            <CardTitle className="text-xl font-bold text-slate-100">
              {repository.file_count}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-400 pt-0">
            Source files analyzed & parsed
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1.5 text-xs">
              <HardDrive className="h-4 w-4 text-amber-400" />
              Repository Size
            </CardDescription>
            <CardTitle className="text-xl font-bold text-slate-100">
              {formatBytes(repository.size_bytes)}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-400 pt-0">
            Extracted source tree size
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1.5 text-xs">
              <Calendar className="h-4 w-4 text-emerald-400" />
              Created At
            </CardDescription>
            <CardTitle className="text-sm font-semibold text-slate-100 truncate">
              {formattedDate}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-400 pt-0">
            Ingestion timestamp
          </CardContent>
        </Card>
      </div>

      {/* Language Breakdown & Frameworks */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Detected Languages */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Layers className="h-4 w-4 text-indigo-400" />
              Language Breakdown
            </CardTitle>
            <CardDescription>
              Distribution of programming languages across this codebase
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {repository.detected_languages && Object.keys(repository.detected_languages).length > 0 ? (
              <div className="space-y-2.5">
                {Object.entries(repository.detected_languages).map(([lang, percentage]) => (
                  <div key={lang} className="space-y-1">
                    <div className="flex justify-between text-xs font-medium text-slate-300">
                      <span>{lang}</span>
                      <span>{percentage}%</span>
                    </div>
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-indigo-500 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No language breakdown available</p>
            )}
          </CardContent>
        </Card>

        {/* Frameworks & Ecosystem */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Code2 className="h-4 w-4 text-sky-400" />
              Detected Frameworks & Libraries
            </CardTitle>
            <CardDescription>
              Frameworks and ecosystem tools detected during AST parsing
            </CardDescription>
          </CardHeader>
          <CardContent>
            {repository.frameworks && repository.frameworks.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {repository.frameworks.map((fw) => (
                  <Badge key={fw} variant="secondary" size="md">
                    {fw}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No specific frameworks detected</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)}>
        <ModalHeader>
          <ModalTitle className="flex items-center gap-2 text-rose-400">
            <AlertTriangle className="h-5 w-5" />
            Delete Repository
          </ModalTitle>
          <ModalDescription>
            Are you sure you want to permanently delete repository <strong className="text-slate-100">{repository.name}</strong>?
          </ModalDescription>
        </ModalHeader>
        <ModalContent>
          <div className="rounded-lg border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-300 space-y-1.5">
            <p className="font-semibold">This action cannot be undone.</p>
            <p className="text-rose-300/80">
              All parsed source files, symbol indexes, graph relationships, semantic embeddings, and chat history associated with this repository will be removed from the system.
            </p>
          </div>
        </ModalContent>
        <ModalFooter>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setIsDeleteModalOpen(false)}
            disabled={deleteMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            size="sm"
            onClick={handleDelete}
            isLoading={deleteMutation.isPending}
            leftIcon={<Trash2 className="h-4 w-4" />}
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Confirm Delete'}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  )
}
