import * as React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { GitBranch, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useCloneRepository } from '../hooks/use-clone-repository'
import type { RepositoryResponse } from '@/lib/api/types'

const cloneSchema = z.object({
  git_url: z
    .string()
    .min(1, 'Git repository URL is required')
    .refine(
      (val) => /^https:\/\/[a-zA-Z0-9_.-]+(\/|:)[a-zA-Z0-9_.-]+/.test(val),
      'Must be a valid HTTPS Git URL (e.g. https://github.com/org/repo.git)'
    ),
})

type CloneFormData = z.infer<typeof cloneSchema>

export interface CloneFormProps {
  onSuccess?: (repository: RepositoryResponse) => void
  onCancel?: () => void
}

export function CloneForm({ onSuccess, onCancel }: CloneFormProps) {
  const [mutationError, setMutationError] = React.useState<string | null>(null)
  const cloneMutation = useCloneRepository()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CloneFormData>({
    resolver: zodResolver(cloneSchema),
    defaultValues: {
      git_url: '',
    },
  })

  const onSubmit = async (data: CloneFormData) => {
    setMutationError(null)
    try {
      const result = await cloneMutation.mutateAsync({
        gitUrl: data.git_url.trim(),
      })
      onSuccess?.(result)
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error ? err.message : 'Failed to clone repository.'
      setMutationError(errorMsg)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <Input
          label="Git Repository HTTPS URL"
          placeholder="https://github.com/owner/repository.git"
          helperText="Public or token-authenticated HTTPS Git URL"
          error={errors.git_url?.message}
          leftIcon={<GitBranch className="h-4 w-4" />}
          disabled={cloneMutation.isPending}
          {...register('git_url')}
        />
      </div>

      {mutationError && (
        <div className="flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{mutationError}</span>
        </div>
      )}

      <div className="flex items-center justify-end gap-2 pt-2">
        {onCancel && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onCancel}
            disabled={cloneMutation.isPending}
          >
            Cancel
          </Button>
        )}
        <Button
          type="submit"
          variant="primary"
          size="sm"
          disabled={cloneMutation.isPending}
          isLoading={cloneMutation.isPending}
          leftIcon={<GitBranch className="h-4 w-4" />}
        >
          {cloneMutation.isPending ? 'Cloning Repository...' : 'Clone & Ingest'}
        </Button>
      </div>
    </form>
  )
}
