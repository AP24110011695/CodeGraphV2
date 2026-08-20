import * as React from 'react'
import { Bot, User } from 'lucide-react'
import { CodeBlock } from '@/components/ui/code-block'
import type { ChatMessageResponse } from '@/lib/api/types'
import { cn } from '@/lib/utils/cn'

export interface MessageBubbleProps {
  message: ChatMessageResponse
  className?: string
}

/**
 * Lightweight markdown parser that extracts code fences and renders formatted text,
 * lists, bold, italic, and inline code without requiring heavy external dependencies.
 */
export function MarkdownContent({ content }: { content: string }) {
  // Split on code fences: ```[lang]\n[code]\n```
  const fenceRegex = /```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g
  const parts: React.ReactNode[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = fenceRegex.exec(content)) !== null) {
    const textBefore = content.slice(lastIndex, match.index)
    if (textBefore) {
      parts.push(<FormattedText key={`text-${lastIndex}`} text={textBefore} />)
    }

    const language = match[1] || 'text'
    const code = match[2].trimEnd()
    parts.push(
      <div key={`code-${match.index}`} className="my-2.5 rounded-lg overflow-hidden border border-slate-800">
        <CodeBlock
          code={code}
          language={language}
          showLineNumbers={code.split('\n').length > 1}
          className="rounded-none border-0 text-xs"
        />
      </div>
    )

    lastIndex = match.index + match[0].length
  }

  const textAfter = content.slice(lastIndex)
  if (textAfter) {
    parts.push(<FormattedText key={`text-${lastIndex}`} text={textAfter} />)
  }

  return <div className="space-y-2 text-sm leading-relaxed">{parts}</div>
}

function FormattedText({ text }: { text: string }) {
  const paragraphs = text.split(/\n\n+/)

  return (
    <>
      {paragraphs.map((p, pIdx) => {
        const lines = p.split('\n')
        // Check if paragraph is a list
        const isList = lines.every((l) => l.trim().startsWith('- ') || l.trim().startsWith('* ') || /^\d+\.\s/.test(l.trim()))

        if (isList) {
          return (
            <ul key={pIdx} className="list-disc list-inside space-y-1 pl-1 text-slate-200">
              {lines.map((item, iIdx) => {
                const cleaned = item.replace(/^[-*]\s+|\d+\.\s+/, '')
                return <li key={iIdx}>{renderInlineFormatting(cleaned)}</li>
              })}
            </ul>
          )
        }

        return (
          <p key={pIdx} className="text-slate-200">
            {lines.map((line, lIdx) => (
              <React.Fragment key={lIdx}>
                {renderInlineFormatting(line)}
                {lIdx < lines.length - 1 && <br />}
              </React.Fragment>
            ))}
          </p>
        )
      })}
    </>
  )
}

function renderInlineFormatting(str: string): React.ReactNode[] {
  // Regex to match inline code (`code`), bold (**text**), or italic (*text*)
  const regex = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g
  const tokens: React.ReactNode[] = []
  let lastIdx = 0
  let m: RegExpExecArray | null

  while ((m = regex.exec(str)) !== null) {
    if (m.index > lastIdx) {
      tokens.push(str.substring(lastIdx, m.index))
    }

    const token = m[0]
    if (token.startsWith('`') && token.endsWith('`')) {
      tokens.push(
        <code
          key={`code-${m.index}`}
          className="rounded bg-slate-800/90 border border-slate-700/60 px-1.5 py-0.5 font-mono text-xs text-indigo-300"
        >
          {token.slice(1, -1)}
        </code>
      )
    } else if (token.startsWith('**') && token.endsWith('**')) {
      tokens.push(<strong key={`bold-${m.index}`} className="font-semibold text-slate-100">{token.slice(2, -2)}</strong>)
    } else if (token.startsWith('*') && token.endsWith('*')) {
      tokens.push(<em key={`italic-${m.index}`}>{token.slice(1, -1)}</em>)
    }

    lastIdx = m.index + token.length
  }

  if (lastIdx < str.length) {
    tokens.push(str.substring(lastIdx))
  }

  return tokens
}

export function MessageBubble({ message, className }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div
      data-testid="message-bubble"
      className={cn(
        'flex gap-3 max-w-3xl',
        isUser ? 'ml-auto flex-row-reverse' : 'mr-auto',
        className
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border text-xs shadow-sm',
          isUser
            ? 'bg-indigo-600 border-indigo-500 text-white'
            : 'bg-slate-800 border-slate-700 text-indigo-400'
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Bubble Content */}
      <div
        className={cn(
          'rounded-2xl px-4 py-3 text-sm shadow-sm',
          isUser
            ? 'bg-indigo-600/90 text-white border border-indigo-500/60 rounded-tr-none'
            : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none'
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <MarkdownContent content={message.content} />
        )}

        {/* Timestamp */}
        {message.created_at && (
          <div
            className={cn(
              'mt-1.5 text-[10px]',
              isUser ? 'text-indigo-200/70 text-right' : 'text-slate-500 text-left'
            )}
          >
            {new Date(message.created_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>
        )}
      </div>
    </div>
  )
}
