import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { RepositoryResponse } from '@/lib/api/types'

export interface UploadRepositoryVariables {
  file: File
  name?: string
}

export function useUploadRepository() {
  const queryClient = useQueryClient()

  return useMutation<RepositoryResponse, Error, UploadRepositoryVariables>({
    mutationFn: ({ file, name }) => apiClient.uploadRepository(file, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
    },
  })
}
