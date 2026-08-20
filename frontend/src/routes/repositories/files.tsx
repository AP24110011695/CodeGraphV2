import { useParams } from '@tanstack/react-router'
import { FileExplorer } from '@/features/files/components/file-explorer'

export function RepositoryFilesPage() {
  const { repoId } = useParams({ strict: false })

  if (!repoId) return null

  return (
    <div className="h-full min-h-[600px] flex flex-col">
      <FileExplorer repoId={repoId} />
    </div>
  )
}
