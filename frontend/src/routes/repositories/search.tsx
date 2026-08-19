import { useParams } from '@tanstack/react-router'
import { Search as SearchIcon } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { mockSearchResults } from '@/lib/api'

export function RepositorySearchPage() {
  const { repoId } = useParams({ strict: false })

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
          <SearchIcon className="h-5 w-5 text-indigo-400" /> Semantic Code Search
        </h3>
        <p className="text-xs text-slate-400">
          Search code semantically across repository <code className="text-slate-300">{repoId}</code>
        </p>
      </div>

      <Input
        placeholder="Search functions, classes, or natural language concepts..."
        leftIcon={<SearchIcon className="h-4 w-4" />}
        defaultValue="login authentication"
      />

      <div className="space-y-3">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Results (2 matches)
        </div>
        {mockSearchResults.map((result) => (
          <Card key={result.chunk_id} className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-indigo-300 font-semibold">
                {result.path}:{result.start_line}-{result.end_line}
              </span>
              <Badge variant="info">Score: {result.score}</Badge>
            </div>
            <pre className="text-xs font-mono bg-slate-950 p-2.5 rounded border border-slate-800 text-slate-300 overflow-x-auto">
              <code>{result.content}</code>
            </pre>
          </Card>
        ))}
      </div>
    </div>
  )
}
