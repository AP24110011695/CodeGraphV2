import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { SearchRequest, SearchResponse } from '@/lib/api/types'

/**
 * Hook for executing semantic vector search across a repository.
 * Uses useMutation since search is user-triggered with parameters.
 */
export function useSearch(repoId: string | undefined) {
  return useMutation<SearchResponse, Error, SearchRequest>({
    mutationFn: (request) => {
      if (!repoId) throw new Error('Repository ID is required')
      return apiClient.search(repoId, request)
    },
  })
}
