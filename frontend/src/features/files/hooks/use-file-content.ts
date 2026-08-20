import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { FileDetail } from '@/lib/api/types'

/**
 * Fetches full content + symbols for a single file.
 * Only enabled when a fileId is provided (i.e., a file is selected in the tree).
 */
export function useFileContent(
  repoId: string | undefined,
  fileId: string | undefined
) {
  return useQuery<FileDetail>({
    queryKey: ['file', repoId, fileId],
    queryFn: () => {
      if (!repoId || !fileId) throw new Error('Repository ID and File ID are required')
      return apiClient.getFile(repoId, fileId)
    },
    enabled: Boolean(repoId) && Boolean(fileId),
    staleTime: 5 * 60 * 1000,
  })
}
