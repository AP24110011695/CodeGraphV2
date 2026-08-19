import * as React from 'react'
import { codeToHtml } from 'shiki'
import { Check, Copy } from 'lucide-react'
import { cn } from '@/lib/utils/cn'

export interface CodeBlockProps extends React.HTMLAttributes<HTMLDivElement> {
  code: string
  language?: string
  filename?: string
  showLineNumbers?: boolean
  highlightLines?: number[]
}

export function CodeBlock({
  code,
  language = 'typescript',
  filename,
  showLineNumbers = true,
  highlightLines = [],
  className,
  ...props
}: CodeBlockProps) {
  const [highlightedHtml, setHighlightedHtml] = React.useState<string | null>(null)
  const [copied, setCopied] = React.useState(false)

  React.useEffect(() => {
    let isMounted = true

    async function highlight() {
      try {
        const langNormalized = language.toLowerCase()
        const lang = ['py', 'python'].includes(langNormalized)
          ? 'python'
          : ['ts', 'typescript'].includes(langNormalized)
            ? 'typescript'
            : ['js', 'javascript'].includes(langNormalized)
              ? 'javascript'
              : ['json'].includes(langNormalized)
                ? 'json'
                : ['css'].includes(langNormalized)
                  ? 'css'
                  : ['sh', 'bash', 'shell'].includes(langNormalized)
                    ? 'bash'
                    : 'text'

        const html = await codeToHtml(code, {
          lang,
          theme: 'github-dark-default',
        })
        if (isMounted) {
          setHighlightedHtml(html)
        }
      } catch (err) {
        console.warn('Shiki highlighting fallback to plain text', err)
        if (isMounted) {
          setHighlightedHtml(null)
        }
      }
    }

    highlight()
    return () => {
      isMounted = false
    }
  }, [code, language])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback
    }
  }

  const lines = code.split('\n')

  return (
    <div
      className={cn(
        'relative rounded-lg border border-slate-800 bg-slate-950 font-mono text-xs overflow-hidden shadow-md text-slate-200',
        className
      )}
      {...props}
    >
      {(filename || language) && (
        <div className="flex items-center justify-between border-b border-slate-800/80 bg-slate-900/90 px-4 py-2 text-slate-400">
          <span className="font-medium text-slate-300">
            {filename || language}
          </span>
          <button
            type="button"
            onClick={handleCopy}
            aria-label={copied ? 'Copied code' : 'Copy code to clipboard'}
            className="flex items-center gap-1 text-[11px] font-sans font-medium text-slate-400 hover:text-slate-100 hover:bg-slate-800 px-2 py-1 rounded transition-colors"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      )}

      {!filename && !language && (
        <button
          type="button"
          onClick={handleCopy}
          aria-label={copied ? 'Copied code' : 'Copy code to clipboard'}
          className="absolute right-3 top-3 z-10 flex items-center gap-1 bg-slate-800/80 border border-slate-700/60 text-[11px] font-sans font-medium text-slate-300 hover:text-white px-2 py-1 rounded shadow backdrop-blur-sm transition-colors"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      )}

      <div className="overflow-x-auto p-4 flex leading-relaxed">
        {showLineNumbers && (
          <div className="select-none pr-4 text-right text-slate-600 font-mono flex flex-col shrink-0 border-r border-slate-800/60 mr-4">
            {lines.map((_, i) => {
              const lineNum = i + 1
              const isHighlighted = highlightLines.includes(lineNum)
              return (
                <span
                  key={lineNum}
                  className={cn(
                    'leading-relaxed px-1',
                    isHighlighted && 'text-indigo-400 font-semibold'
                  )}
                >
                  {lineNum}
                </span>
              )
            })}
          </div>
        )}

        {highlightedHtml ? (
          <div
            className="flex-1 shiki-container [&_pre]:bg-transparent! [&_pre]:m-0! [&_pre]:p-0! [&_code]:leading-relaxed"
            dangerouslySetInnerHTML={{ __html: highlightedHtml }}
          />
        ) : (
          <pre className="flex-1 bg-transparent m-0 p-0 leading-relaxed font-mono">
            <code>{code}</code>
          </pre>
        )}
      </div>
    </div>
  )
}
