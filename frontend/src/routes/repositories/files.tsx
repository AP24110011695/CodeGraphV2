import { useParams } from '@tanstack/react-router'
import { FileCode2 } from 'lucide-react'
import { CodeBlock } from '@/components/ui/code-block'
import { mockFileAuthPy } from '@/lib/api'

export function RepositoryFilesPage() {
  const { repoId } = useParams({ strict: false })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <FileCode2 className="h-4 w-4 text-indigo-400" /> File Explorer & Code Viewer
        </h3>
        <span className="text-xs text-slate-500 font-mono">Repo: {repoId}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="md:col-span-1 p-3 rounded-lg border border-slate-800 bg-slate-900/60 space-y-2">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Files
          </div>
          <div className="space-y-1 text-xs font-mono">
            <div className="px-2 py-1.5 rounded bg-indigo-600/20 text-indigo-300 font-medium">
              app/services/auth.py
            </div>
            <div className="px-2 py-1.5 rounded text-slate-400 hover:bg-slate-800 hover:text-slate-200 cursor-pointer">
              app/api/v1/auth.py
            </div>
            <div className="px-2 py-1.5 rounded text-slate-400 hover:bg-slate-800 hover:text-slate-200 cursor-pointer">
              app/config.py
            </div>
          </div>
        </div>

        <div className="md:col-span-3">
          <CodeBlock
            code={mockFileAuthPy.content || ''}
            language="python"
            filename="app/services/auth.py"
          />
        </div>
      </div>
    </div>
  )
}
