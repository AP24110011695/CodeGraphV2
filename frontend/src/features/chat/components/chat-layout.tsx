import { Plus, Bot, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ErrorState } from '@/components/ui/error-state'
import type { ChatMessageResponse, ChatSessionResponse } from '@/lib/api/types'
import { MessageList } from './message-list'
import { ChatInput } from './chat-input'
import { cn } from '@/lib/utils/cn'

export interface ChatLayoutProps {
  repoId: string
  sessions: ChatSessionResponse[]
  activeSessionId: string | null
  messages: ChatMessageResponse[]
  isLoadingHistory: boolean
  isHistoryError: boolean
  onSelectSession: (sessionId: string) => void
  onNewSession: () => void
  onSendMessage: (content: string) => void
  isSending?: boolean
  className?: string
}

export function ChatLayout({
  repoId: _repoId,
  sessions,
  activeSessionId,
  messages,
  isLoadingHistory,
  isHistoryError,
  onSelectSession,
  onNewSession,
  onSendMessage,
  isSending = false,
  className,
}: ChatLayoutProps) {
  return (
    <div
      data-testid="chat-layout"
      className={cn(
        'flex flex-col h-full min-h-[600px] rounded-xl border border-slate-800 bg-slate-950 overflow-hidden shadow-xl',
        className
      )}
    >
      {/* Top Session Bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/80 shrink-0">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
            <Bot className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <h3 className="text-xs font-semibold text-slate-200 truncate flex items-center gap-1.5">
              <span>CodeGraph Chat</span>
              <span className="flex items-center gap-1 text-[10px] text-indigo-300 font-normal bg-indigo-950/60 border border-indigo-500/20 px-1.5 py-0.2 rounded">
                <Sparkles className="h-2.5 w-2.5 text-indigo-400" /> RAG Grounded
              </span>
            </h3>
            {activeSessionId && (
              <span className="text-[10px] font-mono text-slate-500 truncate block">
                Session: {activeSessionId.slice(0, 8)}...
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {sessions.length > 1 && (
            <select
              value={activeSessionId || ''}
              onChange={(e) => onSelectSession(e.target.value)}
              aria-label="Select chat session"
              className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded px-2 py-1 max-w-[140px] truncate"
            >
              {sessions.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title || `Chat ${s.id.slice(0, 6)}`}
                </option>
              ))}
            </select>
          )}

          <Button
            variant="secondary"
            size="sm"
            onClick={onNewSession}
            className="h-8 text-xs flex items-center gap-1.5"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>New Chat</span>
          </Button>
        </div>
      </div>

      {/* Main Message History Area */}
      <div className="flex-1 flex flex-col min-h-0 relative">
        {isLoadingHistory ? (
          <div className="p-6 space-y-4">
            <Skeleton className="h-16 w-3/4 mr-auto" />
            <Skeleton className="h-12 w-1/2 ml-auto" />
            <Skeleton className="h-24 w-4/5 mr-auto" />
          </div>
        ) : isHistoryError ? (
          <div className="flex-1 flex items-center justify-center p-8">
            <ErrorState
              title="Failed to load chat history"
              message="Could not load messages for this conversation."
            />
          </div>
        ) : (
          <MessageList messages={messages} />
        )}
      </div>

      {/* Bottom Input Area */}
      <div className="p-3 bg-slate-900/60 border-t border-slate-800/80 shrink-0">
        <ChatInput
          onSend={onSendMessage}
          disabled={isSending || isLoadingHistory}
          className="max-w-4xl mx-auto"
        />
      </div>
    </div>
  )
}
