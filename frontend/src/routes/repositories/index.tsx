import * as React from 'react'
import { FolderGit2, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { RepositoryList } from '@/features/repositories/components/repository-list'
import { AddRepositoryModal } from '@/features/repositories/components/add-repository-modal'

export function RepositoriesIndexPage() {
  const [isAddModalOpen, setIsAddModalOpen] = React.useState(false)

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <FolderGit2 className="h-6 w-6 text-indigo-400" /> Repositories
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Ingest and analyze your codebases with AI-powered code graph intelligence
          </p>
        </div>
        <Button
          variant="primary"
          onClick={() => setIsAddModalOpen(true)}
          leftIcon={<Plus className="h-4 w-4" />}
        >
          Add Repository
        </Button>
      </div>

      {/* Main Repository List View */}
      <RepositoryList onAddRepository={() => setIsAddModalOpen(true)} />

      {/* Add Repository Modal (Upload / Git Clone) */}
      <AddRepositoryModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
      />
    </div>
  )
}
