import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { NodeDetailResponse } from '@/lib/api/types'

/**
 * Fetches node details (symbols, dependencies, dependents) for a selected graph node.
 */
export function useGraphNode(
  repoId: string | undefined,
  fileId: string | null | undefined
) {
  return useQuery<NodeDetailResponse>({
    queryKey: ['graph-node', repoId, fileId],
    queryFn: () => {
      if (!repoId || !fileId) throw new Error('Repository ID and File ID are required')
      return apiClient.getNodeDetail(repoId, fileId)
    },
    enabled: Boolean(repoId) && Boolean(fileId),
    staleTime: 5 * 60 * 1000,
  })
}
