import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { RepositoryResponse } from '@/lib/api/types'

export function useRepository(repoId?: string) {
  return useQuery<RepositoryResponse>({
    queryKey: ['repository', repoId],
    queryFn: () => {
      if (!repoId) throw new Error('Repository ID is required')
      return apiClient.getRepository(repoId)
    },
    enabled: Boolean(repoId),
  })
}
