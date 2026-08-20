import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'

export function useDeleteRepository() {
  const queryClient = useQueryClient()

  return useMutation<void, Error, string>({
    mutationFn: (repoId: string) => apiClient.deleteRepository(repoId),
    onSuccess: (_, repoId) => {
      queryClient.removeQueries({ queryKey: ['repository', repoId] })
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
    },
  })
}
