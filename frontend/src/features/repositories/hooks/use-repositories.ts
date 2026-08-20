import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { PaginationParams, RepositoryListResponse } from '@/lib/api/types'

export function useRepositories(params?: PaginationParams) {
  return useQuery<RepositoryListResponse>({
    queryKey: ['repositories', params],
    queryFn: () => apiClient.listRepositories(params),
  })
}
