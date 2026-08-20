import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { FileListResponse } from '@/lib/api/types'

/**
 * Fetches all files for a repository.
 * Fetches in pages of 200 to ensure we get all files in one round-trip
 * for repos of typical size. The tree is built client-side from the flat path list.
 */
export function useFiles(repoId: string | undefined) {
  return useQuery<FileListResponse>({
    queryKey: ['files', repoId],
    queryFn: () => {
      if (!repoId) throw new Error('Repository ID is required')
      return apiClient.listFiles(repoId, { page: 1, page_size: 200 })
    },
    enabled: Boolean(repoId),
    staleTime: 2 * 60 * 1000,
  })
}
