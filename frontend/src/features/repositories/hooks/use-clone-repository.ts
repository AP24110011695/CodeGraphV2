import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { RepositoryResponse } from '@/lib/api/types'

export interface CloneRepositoryVariables {
  gitUrl: string
}

export function useCloneRepository() {
  const queryClient = useQueryClient()

  return useMutation<RepositoryResponse, Error, CloneRepositoryVariables>({
    mutationFn: ({ gitUrl }) => apiClient.cloneRepository(gitUrl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
    },
  })
}
