import { useParams } from '@tanstack/react-router'
import { GitGraph } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { mockGraphResponse } from '@/lib/api'

export function RepositoryGraphPage() {
  const { repoId } = useParams({ strict: false })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <GitGraph className="h-4 w-4 text-indigo-400" /> Dependency Graph Visualization
        </h3>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">Nodes: {mockGraphResponse.metrics.node_count}</Badge>
          <Badge variant="secondary">Edges: {mockGraphResponse.metrics.edge_count}</Badge>
        </div>
      </div>

      <div className="h-[450px] flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 bg-slate-900/40 p-6 text-center space-y-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
          <GitGraph className="h-6 w-6" />
        </div>
        <h4 className="text-base font-semibold text-slate-200">Interactive 3D Dependency Graph</h4>
        <p className="text-sm text-slate-400 max-w-md">
          Graph visualization surface for repository <code className="text-indigo-300">{repoId}</code>. Full canvas and metrics panel will land in Phase 12.
        </p>
      </div>
    </div>
  )
}
