import * as React from 'react'
import { useParams } from '@tanstack/react-router'
import { ChatLayout } from '@/features/chat/components/chat-layout'
import { useChatSessions } from '@/features/chat/hooks/use-chat-session'
import { useChatHistory } from '@/features/chat/hooks/use-chat-history'
import type { ChatMessageResponse } from '@/lib/api/types'

export function RepositoryChatPage() {
  const { repoId } = useParams({ strict: false })
  const [activeSessionId, setActiveSessionId] = React.useState<string | null>(null)
  const [localMessages, setLocalMessages] = React.useState<ChatMessageResponse[]>([])
  const [isSending, setIsSending] = React.useState(false)

  const {
    sessions,
    isLoading: sessionsLoading,
    createSession,
  } = useChatSessions(repoId)

  // Auto-select or create session on initial mount
  React.useEffect(() => {
    if (!activeSessionId && sessions.length > 0) {
      setActiveSessionId(sessions[0].id)
    } else if (!activeSessionId && !sessionsLoading && repoId && sessions.length === 0) {
      createSession({ title: 'General Conversation' }).then((res) => {
        setActiveSessionId(res.session_id)
      })
    }
  }, [activeSessionId, sessions, sessionsLoading, repoId, createSession])

  const {
    data: fetchedMessages = [],
    isLoading: historyLoading,
    isError: historyError,
  } = useChatHistory(repoId, activeSessionId)

  // Sync fetched history into local display messages
  React.useEffect(() => {
    if (fetchedMessages.length > 0) {
      setLocalMessages(fetchedMessages)
    }
  }, [fetchedMessages])

  const handleNewSession = async () => {
    if (!repoId) return
    const res = await createSession({
      title: `Conversation ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`,
    })
    setActiveSessionId(res.session_id)
    setLocalMessages([])
  }

  const handleSendMessage = (content: string) => {
    if (!content.trim() || !activeSessionId) return

    const userMessage: ChatMessageResponse = {
      id: crypto.randomUUID(),
      session_id: activeSessionId,
      role: 'user',
      content: content.trim(),
      created_at: new Date().toISOString(),
    }

    // Append user message immediately
    setLocalMessages((prev) => [...prev, userMessage])
    setIsSending(true)

    // Phase 14 static placeholder reply simulation (Phase 15 connects token streaming)
    setTimeout(() => {
      const assistantMessage: ChatMessageResponse = {
        id: crypto.randomUUID(),
        session_id: activeSessionId,
        role: 'assistant',
        content: `I analyzed your request about "${content}". Here is the architectural summary based on the indexed codebase.\n\n\`\`\`typescript\n// Relevant function implementation\nexport function handleAuth() {\n  return { authenticated: true }\n}\n\`\`\`\n\n- Verified authentication handlers in \`app/services/auth.py\`\n- Traced route definitions in \`app/api/routes.py\``,
        created_at: new Date().toISOString(),
      }
      setLocalMessages((prev) => [...prev, assistantMessage])
      setIsSending(false)
    }, 400)
  }

  if (!repoId) return null

  return (
    <div className="h-full min-h-[650px] flex flex-col">
      <ChatLayout
        repoId={repoId}
        sessions={sessions}
        activeSessionId={activeSessionId}
        messages={localMessages}
        isLoadingHistory={historyLoading && localMessages.length === 0}
        isHistoryError={historyError}
        onSelectSession={setActiveSessionId}
        onNewSession={handleNewSession}
        onSendMessage={handleSendMessage}
        isSending={isSending}
      />
    </div>
  )
}
