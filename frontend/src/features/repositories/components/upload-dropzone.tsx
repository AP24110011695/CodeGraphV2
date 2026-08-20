import * as React from 'react'
import { UploadCloud, FileArchive, X, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ProgressBar } from '@/components/ui/progress-bar'
import { useUploadRepository } from '../hooks/use-upload-repository'
import type { RepositoryResponse } from '@/lib/api/types'

const MAX_REPO_SIZE_MB = 500
const MAX_REPO_SIZE_BYTES = MAX_REPO_SIZE_MB * 1024 * 1024

export interface UploadDropzoneProps {
  onSuccess?: (repository: RepositoryResponse) => void
  onCancel?: () => void
}

export function UploadDropzone({ onSuccess, onCancel }: UploadDropzoneProps) {
  const [file, setFile] = React.useState<File | null>(null)
  const [repoName, setRepoName] = React.useState('')
  const [validationError, setValidationError] = React.useState<string | null>(null)
  const [isDragOver, setIsDragOver] = React.useState(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const uploadMutation = useUploadRepository()

  const validateFile = (selectedFile: File): boolean => {
    setValidationError(null)

    // Check extension or mime
    const isZip =
      selectedFile.name.toLowerCase().endsWith('.zip') ||
      selectedFile.type === 'application/zip' ||
      selectedFile.type === 'application/x-zip-compressed'

    if (!isZip) {
      setValidationError('Invalid file type. Please upload a .zip repository archive.')
      return false
    }

    if (selectedFile.size > MAX_REPO_SIZE_BYTES) {
      setValidationError(
        `File size exceeds the ${MAX_REPO_SIZE_MB}MB limit (actual: ${(selectedFile.size / (1024 * 1024)).toFixed(1)}MB).`
      )
      return false
    }

    return true
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (selected) {
      if (validateFile(selected)) {
        setFile(selected)
        if (!repoName) {
          // Default repository name from zip file name
          const nameWithoutExt = selected.name.replace(/\.zip$/i, '')
          setRepoName(nameWithoutExt)
        }
      } else {
        setFile(null)
      }
    }
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile) {
      if (validateFile(droppedFile)) {
        setFile(droppedFile)
        if (!repoName) {
          const nameWithoutExt = droppedFile.name.replace(/\.zip$/i, '')
          setRepoName(nameWithoutExt)
        }
      } else {
        setFile(null)
      }
    }
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setValidationError('Please select a zip archive to upload.')
      return
    }

    try {
      const result = await uploadMutation.mutateAsync({
        file,
        name: repoName.trim() || undefined,
      })
      onSuccess?.(result)
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error ? err.message : 'Failed to upload repository.'
      setValidationError(errorMsg)
    }
  }

  const removeFile = () => {
    setFile(null)
    setValidationError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <input
        ref={fileInputRef}
        type="file"
        accept=".zip,application/zip,application/x-zip-compressed"
        onChange={handleFileChange}
        className="hidden"
        id="zip-file-input"
      />

      {!file ? (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              fileInputRef.current?.click()
            }
          }}
          className={`flex flex-col items-center justify-center p-8 rounded-xl border-2 border-dashed transition-all cursor-pointer select-none text-center ${
            isDragOver
              ? 'border-indigo-500 bg-indigo-600/10'
              : 'border-slate-700 hover:border-indigo-500/60 bg-slate-900/40 hover:bg-slate-900/60'
          }`}
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-600/10 border border-indigo-500/30 text-indigo-400 mb-3 shadow-inner">
            <UploadCloud className="h-6 w-6" />
          </div>
          <p className="text-sm font-semibold text-slate-200">
            Click to browse or drag and drop your repository ZIP
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Standard .zip archive (up to {MAX_REPO_SIZE_MB}MB)
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600/20 text-indigo-400 shrink-0">
                <FileArchive className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-slate-200 truncate">
                  {file.name}
                </p>
                <p className="text-xs text-slate-400">
                  {formatFileSize(file.size)}
                </p>
              </div>
            </div>
            {!uploadMutation.isPending && (
              <button
                type="button"
                onClick={removeFile}
                className="p-1 rounded-md text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
                aria-label="Remove selected file"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <div>
            <Input
              label="Repository Name"
              value={repoName}
              onChange={(e) => setRepoName(e.target.value)}
              placeholder="e.g. backend-service"
              helperText="Optional: override the auto-generated name"
              disabled={uploadMutation.isPending}
            />
          </div>

          {uploadMutation.isPending && (
            <div className="space-y-1.5 pt-2">
              <ProgressBar
                value={75}
                label="Uploading and initiating ingestion pipeline..."
                size="sm"
              />
            </div>
          )}
        </div>
      )}

      {validationError && (
        <div className="flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{validationError}</span>
        </div>
      )}

      <div className="flex items-center justify-end gap-2 pt-2">
        {onCancel && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onCancel}
            disabled={uploadMutation.isPending}
          >
            Cancel
          </Button>
        )}
        <Button
          type="submit"
          variant="primary"
          size="sm"
          disabled={!file || uploadMutation.isPending}
          isLoading={uploadMutation.isPending}
          leftIcon={<UploadCloud className="h-4 w-4" />}
        >
          {uploadMutation.isPending ? 'Uploading...' : 'Upload & Ingest'}
        </Button>
      </div>
    </form>
  )
}
