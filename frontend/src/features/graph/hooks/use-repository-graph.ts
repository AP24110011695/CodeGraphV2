import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { GraphResponse } from '@/lib/api/types'

/**
 * Fetches the dependency graph (nodes, edges, metrics) for a repository.
 */
export function useRepositoryGraph(repoId: string | undefined) {
  return useQuery<GraphResponse>({
    queryKey: ['graph', repoId],
    queryFn: () => {
      if (!repoId) throw new Error('Repository ID is required')
      return apiClient.getGraph(repoId)
    },
    enabled: Boolean(repoId),
    staleTime: 5 * 60 * 1000,
  })
}
