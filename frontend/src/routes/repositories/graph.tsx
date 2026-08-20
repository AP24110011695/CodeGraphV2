import * as React from 'react'
import { useParams } from '@tanstack/react-router'
import { ErrorState } from '@/components/ui/error-state'
import { Skeleton } from '@/components/ui/skeleton'
import { DependencyGraph } from '@/features/graph/components/dependency-graph'
import { GraphControls } from '@/features/graph/components/graph-controls'
import { NodeDetailPanel } from '@/features/graph/components/node-detail-panel'
import { useRepositoryGraph } from '@/features/graph/hooks/use-repository-graph'
import type Sigma from 'sigma'

export function RepositoryGraphPage() {
  const { repoId } = useParams({ strict: false })
  const [selectedNodeId, setSelectedNodeId] = React.useState<string | null>(null)
  const [selectedLanguages, setSelectedLanguages] = React.useState<string[]>([])
  const [onlyEntryPoints, setOnlyEntryPoints] = React.useState(false)
  const sigmaInstanceRef = React.useRef<Sigma | null>(null)

  const {
    data: graphData,
    isLoading,
    isError,
    error,
    refetch,
  } = useRepositoryGraph(repoId)

  const availableLanguages = React.useMemo(() => {
    if (!graphData?.nodes) return []
    const set = new Set<string>()
    graphData.nodes.forEach((n) => {
      if (n.language) set.add(n.language)
    })
    return Array.from(set).sort()
  }, [graphData])

  const handleToggleLanguage = (lang: string) => {
    setSelectedLanguages((prev) => {
      const lower = lang.toLowerCase()
      const exists = prev.some((l) => l.toLowerCase() === lower)
      if (exists) {
        return prev.filter((l) => l.toLowerCase() !== lower)
      } else {
        return [...prev, lang]
      }
    })
  }

  const handleResetView = () => {
    if (sigmaInstanceRef.current) {
      const camera = sigmaInstanceRef.current.getCamera()
      camera.animatedReset({ duration: 500 })
    }
  }

  if (!repoId) return null

  if (isLoading) {
    return (
      <div className="flex flex-col h-full min-h-[600px] gap-3">
        <Skeleton className="h-14 w-full" />
        <Skeleton className="flex-1 w-full rounded-lg min-h-[500px]" />
      </div>
    )
  }

  if (isError || !graphData) {
    return (
      <div className="flex items-center justify-center h-full min-h-[500px] p-8">
        <ErrorState
          title="Failed to load dependency graph"
          message={error?.message ?? 'Could not fetch the graph data for this repository.'}
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full min-h-[600px] space-y-3">
      {/* Top Controls Bar */}
      <GraphControls
        metrics={graphData.metrics}
        availableLanguages={availableLanguages}
        selectedLanguages={selectedLanguages}
        onToggleLanguage={handleToggleLanguage}
        onlyEntryPoints={onlyEntryPoints}
        onToggleEntryPoints={setOnlyEntryPoints}
        onResetView={handleResetView}
      />

      {/* Main Canvas & Detail Panel */}
      <div className="relative flex flex-1 min-h-[520px] rounded-lg overflow-hidden border border-slate-800 bg-slate-950">
        <div className="flex-1 relative h-full">
          <DependencyGraph
            data={graphData}
            selectedNodeId={selectedNodeId}
            onSelectNode={setSelectedNodeId}
            selectedLanguages={selectedLanguages}
            onlyEntryPoints={onlyEntryPoints}
            className="w-full h-full"
            onGraphReady={(_, sigma) => {
              sigmaInstanceRef.current = sigma
            }}
          />
        </div>

        {/* Side Panel on node selection */}
        {selectedNodeId && (
          <div className="absolute top-0 right-0 bottom-0 z-10 shadow-2xl">
            <NodeDetailPanel
              repoId={repoId}
              nodeId={selectedNodeId}
              onClose={() => setSelectedNodeId(null)}
            />
          </div>
        )}
      </div>
    </div>
  )
}
