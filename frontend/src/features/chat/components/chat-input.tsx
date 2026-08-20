import * as React from 'react'
import { ArrowUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils/cn'

export interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
  className?: string
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Ask a question about the repository (e.g. "How does token validation work?")...',
  className,
}: ChatInputProps) {
  const [text, setText] = React.useState('')
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value)
    // Auto-expand up to 160px
    const el = e.target
    el.style.height = 'auto'
    el.style.height = `${Math.min(160, Math.max(48, el.scrollHeight))}px`
  }

  return (
    <div
      className={cn(
        'relative rounded-xl border border-slate-800 bg-slate-900/90 shadow-lg focus-within:border-indigo-500/70 focus-within:ring-1 focus-within:ring-indigo-500/50 transition-all',
        className
      )}
    >
      <textarea
        ref={textareaRef}
        value={text}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder}
        rows={1}
        aria-label="Chat message input"
        className="w-full resize-none bg-transparent px-4 py-3.5 pr-14 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none disabled:opacity-50 min-h-[48px] max-h-[160px]"
      />

      <div className="absolute right-2.5 bottom-2.5 flex items-center gap-1.5">
        <Button
          type="button"
          size="sm"
          variant="primary"
          onClick={handleSend}
          disabled={!text.trim() || disabled}
          className="h-8 w-8 p-0 rounded-lg flex items-center justify-center shrink-0"
          aria-label="Send message"
        >
          <ArrowUp className="h-4 w-4" />
        </Button>
      </div>

      <div className="px-4 pb-2 pt-0 flex items-center justify-between text-[10px] text-slate-500 select-none">
        <span>Press <kbd className="font-mono bg-slate-800 px-1 py-0.5 rounded text-slate-400">Enter</kbd> to send, <kbd className="font-mono bg-slate-800 px-1 py-0.5 rounded text-slate-400">Shift + Enter</kbd> for new line</span>
      </div>
    </div>
  )
}
