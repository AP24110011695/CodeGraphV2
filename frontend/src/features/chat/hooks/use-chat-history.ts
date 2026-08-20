import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { ChatMessageResponse } from '@/lib/api/types'

/**
 * Hook for fetching message history for a given chat session.
 */
export function useChatHistory(
  repoId: string | undefined,
  sessionId: string | null | undefined
) {
  return useQuery<ChatMessageResponse[]>({
    queryKey: ['chat-messages', repoId, sessionId],
    queryFn: () => {
      if (!repoId || !sessionId) throw new Error('Repository ID and Session ID are required')
      return apiClient.listChatMessages(repoId, sessionId)
    },
    enabled: Boolean(repoId) && Boolean(sessionId),
    staleTime: 10 * 1000,
  })
}
