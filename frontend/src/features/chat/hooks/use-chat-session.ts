import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { ChatSessionResponse, CreateSessionRequest } from '@/lib/api/types'

/**
 * Hook for managing chat sessions for a repository.
 * Lists available sessions and auto-creates or activates a session.
 */
export function useChatSessions(repoId: string | undefined) {
  const queryClient = useQueryClient()

  const {
    data: sessions = [],
    isLoading,
    refetch,
  } = useQuery<ChatSessionResponse[]>({
    queryKey: ['chat-sessions', repoId],
    queryFn: () => {
      if (!repoId) throw new Error('Repository ID is required')
      return apiClient.listChatSessions(repoId)
    },
    enabled: Boolean(repoId),
    staleTime: 60 * 1000,
  })

  const createSessionMutation = useMutation({
    mutationFn: (request?: CreateSessionRequest) => {
      if (!repoId) throw new Error('Repository ID is required')
      return apiClient.createChatSession(repoId, request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions', repoId] })
    },
  })

  return {
    sessions,
    isLoading,
    refetch,
    createSession: createSessionMutation.mutateAsync,
    isCreating: createSessionMutation.isPending,
  }
}
