import * as React from 'react'
import { MessageSquare } from 'lucide-react'
import { EmptyState } from '@/components/ui/empty-state'
import type { ChatMessageResponse } from '@/lib/api/types'
import { MessageBubble } from './message-bubble'
import { cn } from '@/lib/utils/cn'

export interface MessageListProps {
  messages: ChatMessageResponse[]
  isLoading?: boolean
  className?: string
}

export function MessageList({
  messages,
  isLoading = false,
  className,
}: MessageListProps) {
  const bottomRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-16">
        <EmptyState
          icon={<MessageSquare className="h-10 w-10 text-indigo-400/80" />}
          title="CodeGraph AI Assistant"
          description="Ask questions grounded in the repository's source code, symbols, and architecture. Responses cite exact file lines and module relationships."
        />
      </div>
    )
  }

  return (
    <div
      data-testid="message-list"
      className={cn('flex-1 overflow-y-auto p-4 space-y-4', className)}
    >
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
