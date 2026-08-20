import * as React from 'react'
import { useNavigate } from '@tanstack/react-router'
import { UploadCloud, GitBranch, FolderPlus } from 'lucide-react'
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
} from '@/components/ui/modal'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { useToast } from '@/components/ui/toast'
import { UploadDropzone } from './upload-dropzone'
import { CloneForm } from './clone-form'
import type { RepositoryResponse } from '@/lib/api/types'

export interface AddRepositoryModalProps {
  isOpen: boolean
  onClose: () => void
}

export function AddRepositoryModal({ isOpen, onClose }: AddRepositoryModalProps) {
  const navigate = useNavigate()
  const toast = useToast()
  const [activeTab, setActiveTab] = React.useState('upload')

  const handleSuccess = (repo: RepositoryResponse) => {
    toast.success(
      `Repository "${repo.name}" has been queued for ingestion.`,
      'Repository Added'
    )
    onClose()
    navigate({
      to: '/repositories/$repoId',
      params: { repoId: repo.id },
    })
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-xl">
      <ModalHeader>
        <ModalTitle className="flex items-center gap-2">
          <FolderPlus className="h-5 w-5 text-indigo-400" />
          Add New Repository
        </ModalTitle>
        <ModalDescription>
          Ingest codebase archives or clone from remote Git providers to build intelligent dependency graphs.
        </ModalDescription>
      </ModalHeader>
      <ModalContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2 mb-4">
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <UploadCloud className="h-4 w-4" />
              Upload ZIP Archive
            </TabsTrigger>
            <TabsTrigger value="clone" className="flex items-center gap-2">
              <GitBranch className="h-4 w-4" />
              Clone Git Repository
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload">
            <UploadDropzone onSuccess={handleSuccess} onCancel={onClose} />
          </TabsContent>

          <TabsContent value="clone">
            <CloneForm onSuccess={handleSuccess} onCancel={onClose} />
          </TabsContent>
        </Tabs>
      </ModalContent>
    </Modal>
  )
}
