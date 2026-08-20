import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { SymbolResponse } from '@/lib/api/types'

/**
 * Fetches all symbols for a selected file.
 * Only enabled when both repoId and fileId are provided.
 */
export function useFileSymbols(
  repoId: string | undefined,
  fileId: string | undefined
) {
  return useQuery<SymbolResponse[]>({
    queryKey: ['symbols', repoId, fileId],
    queryFn: () => {
      if (!repoId || !fileId) throw new Error('Repository ID and File ID are required')
      return apiClient.getSymbols(repoId, fileId)
    },
    enabled: Boolean(repoId) && Boolean(fileId),
    staleTime: 5 * 60 * 1000,
  })
}
