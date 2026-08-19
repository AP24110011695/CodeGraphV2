import { useParams } from '@tanstack/react-router'
import { MessageSquare, Sparkles, Send } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { mockChatMessages } from '@/lib/api'

export function RepositoryChatPage() {
  const { repoId } = useParams({ strict: false })

  return (
    <div className="h-[600px] flex flex-col rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 p-4 bg-slate-950/60">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-indigo-400" />
          <h3 className="text-sm font-semibold text-slate-200">
            AI Assistant Chat
          </h3>
        </div>
        <Badge variant="success">Grounded RAG</Badge>
      </div>

      {/* Messages Feed */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {mockChatMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.role === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            <div
              className={`max-w-xl rounded-xl p-3.5 text-xs leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-none'
                  : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-bl-none'
              }`}
            >
              <p>{msg.content}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2.5 pt-2 border-t border-slate-700/60 flex flex-wrap gap-1.5">
                  <span className="text-[10px] text-slate-400 font-semibold">Sources:</span>
                  {msg.sources.map((src, i) => (
                    <span
                      key={i}
                      className="text-[10px] font-mono bg-slate-900/80 px-1.5 py-0.5 rounded border border-slate-700 text-indigo-300"
                    >
                      {src.path}:{src.start_line}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Input Form */}
      <div className="border-t border-slate-800 p-4 bg-slate-950/80 flex items-center gap-2">
        <div className="flex-1">
          <Input
            placeholder={`Ask a question about repository ${repoId}...`}
            leftIcon={<MessageSquare className="h-4 w-4" />}
          />
        </div>
        <Button size="md" leftIcon={<Send className="h-4 w-4" />}>
          Send
        </Button>
      </div>
    </div>
  )
}
