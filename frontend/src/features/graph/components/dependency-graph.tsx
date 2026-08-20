/* eslint-disable react-refresh/only-export-components */
import * as React from 'react'
import { DirectedGraph } from 'graphology'
import Sigma from 'sigma'
import type { GraphResponse } from '@/lib/api/types'
import { cn } from '@/lib/utils/cn'

export interface DependencyGraphProps {
  data: GraphResponse
  selectedNodeId?: string | null
  onSelectNode?: (nodeId: string | null) => void
  selectedLanguages?: string[]
  onlyEntryPoints?: boolean
  className?: string
  onGraphReady?: (graph: DirectedGraph, sigma: Sigma) => void
}

export const LANGUAGE_COLORS: Record<string, string> = {
  python: '#818cf8', // indigo-400
  typescript: '#38bdf8', // sky-400
  javascript: '#facc15', // amber-400
  go: '#34d399', // emerald-400
  rust: '#fb923c', // orange-400
  java: '#f43f5e', // rose-500
  cpp: '#a855f7', // purple-500
  c: '#6366f1', // indigo-500
  markdown: '#94a3b8', // slate-400
  default: '#64748b', // slate-500
}

export function getLanguageColor(lang?: string | null): string {
  if (!lang) return LANGUAGE_COLORS.default
  const lower = lang.toLowerCase()
  return LANGUAGE_COLORS[lower] || LANGUAGE_COLORS.default
}

/**
 * Builds a Graphology DirectedGraph instance from API GraphResponse data.
 */
export function buildGraphologyInstance(
  data: GraphResponse,
  filter?: {
    languages?: string[]
    onlyEntryPoints?: boolean
  }
): DirectedGraph {
  const graph = new DirectedGraph()

  const activeLanguages = filter?.languages && filter.languages.length > 0
    ? new Set(filter.languages.map((l) => l.toLowerCase()))
    : null
  const onlyEntryPoints = filter?.onlyEntryPoints ?? false

  // Filter nodes based on criteria
  const validNodes = data.nodes.filter((node) => {
    if (onlyEntryPoints && !node.metrics.is_entry_point) {
      return false
    }
    if (activeLanguages) {
      const nodeLang = (node.language || '').toLowerCase()
      if (!activeLanguages.has(nodeLang)) {
        return false
      }
    }
    return true
  })

  const nodeCount = validNodes.length
  const validNodeIds = new Set(validNodes.map((n) => n.id))

  // Position nodes in a 2D layout (circular or structured by depth)
  validNodes.forEach((node, i) => {
    // Arrange in concentric circles/spiral
    const angle = (2 * Math.PI * i) / Math.max(1, nodeCount)
    const radius = 100 + (i % 3) * 50
    const x = Math.cos(angle) * radius + (Math.sin(i * 1.5) * 20)
    const y = Math.sin(angle) * radius + (Math.cos(i * 1.5) * 20)

    // Node size based on pagerank
    const baseSize = 6
    const prBonus = Math.min(18, Math.round((node.metrics.pagerank || 0) * 80))
    const size = baseSize + prBonus + (node.metrics.is_entry_point ? 3 : 0)

    const color = getLanguageColor(node.language)
    const label = node.path.split('/').pop() || node.path

    graph.addNode(node.id, {
      id: node.id,
      label,
      path: node.path,
      language: node.language,
      size,
      color,
      x,
      y,
      isEntryPoint: node.metrics.is_entry_point,
      pagerank: node.metrics.pagerank,
      symbolCount: node.symbol_count,
    })
  })

  // Add edges if both nodes exist in filtered graph
  data.edges.forEach((edge, i) => {
    if (validNodeIds.has(edge.from_file_id) && validNodeIds.has(edge.to_file_id)) {
      if (!graph.hasEdge(edge.from_file_id, edge.to_file_id)) {
        graph.addEdgeWithKey(`e-${i}`, edge.from_file_id, edge.to_file_id, {
          size: 1.5,
          color: '#334155',
          importName: edge.import_name,
        })
      }
    }
  })

  return graph
}

export function DependencyGraph({
  data,
  selectedNodeId,
  onSelectNode,
  selectedLanguages = [],
  onlyEntryPoints = false,
  className,
  onGraphReady,
}: DependencyGraphProps) {
  const containerRef = React.useRef<HTMLDivElement>(null)
  const sigmaRef = React.useRef<Sigma | null>(null)
  const graphRef = React.useRef<DirectedGraph | null>(null)
  const [hoveredNode, setHoveredNode] = React.useState<string | null>(null)

  const hoveredNodeRef = React.useRef<string | null>(null)
  const selectedNodeIdRef = React.useRef<string | null>(selectedNodeId ?? null)

  React.useEffect(() => {
    hoveredNodeRef.current = hoveredNode
    selectedNodeIdRef.current = selectedNodeId ?? null
    if (sigmaRef.current) {
      sigmaRef.current.refresh()
    }
  }, [hoveredNode, selectedNodeId])

  // Build/rebuild graph when data or filters change
  React.useEffect(() => {
    if (!containerRef.current) return

    const graph = buildGraphologyInstance(data, {
      languages: selectedLanguages,
      onlyEntryPoints,
    })
    graphRef.current = graph

    // Cleanup previous sigma instance
    if (sigmaRef.current) {
      sigmaRef.current.kill()
      sigmaRef.current = null
    }

    // In non-canvas test environments (like jsdom), Sigma instantiation can be gracefully handled
    try {
      const sigma = new Sigma(graph, containerRef.current, {
        renderEdgeLabels: false,
        allowInvalidContainer: true,
        labelFont: 'ui-monospace, SFMono-Regular, monospace',
        labelSize: 11,
        labelColor: { color: '#cbd5e1' },
        defaultEdgeType: 'arrow',
        defaultEdgeColor: '#334155',
        stagePadding: 40,
        nodeReducer: (node, attrs) => {
          const res = { ...attrs }
          const currentHovered = hoveredNodeRef.current
          const currentSelected = selectedNodeIdRef.current

          if (currentHovered) {
            const isHovered = node === currentHovered
            const isNeighbor =
              graph.hasEdge(node, currentHovered) || graph.hasEdge(currentHovered, node)

            if (!isHovered && !isNeighbor) {
              res.color = '#1e293b'
              res.label = ''
            } else if (isHovered) {
              res.highlighted = true
              res.size = (attrs.size || 6) * 1.3
            }
          }

          if (currentSelected && node === currentSelected) {
            res.highlighted = true
            res.color = '#6366f1' // highlighted indigo
          }

          return res
        },
        edgeReducer: (edge, attrs) => {
          const res = { ...attrs }
          const currentHovered = hoveredNodeRef.current

          if (currentHovered) {
            const source = graph.source(edge)
            const target = graph.target(edge)
            const isConnected = source === currentHovered || target === currentHovered

            if (!isConnected) {
              res.hidden = true
            } else {
              res.color = '#818cf8'
              res.size = 2.5
            }
          }
          return res
        },
      })

      sigma.on('enterNode', ({ node }) => {
        setHoveredNode(node)
      })

      sigma.on('leaveNode', () => {
        setHoveredNode(null)
      })

      sigma.on('clickNode', ({ node }) => {
        onSelectNode?.(node)
      })

      sigma.on('clickStage', () => {
        onSelectNode?.(null)
      })

      sigmaRef.current = sigma
      onGraphReady?.(graph, sigma)
    } catch {
      // In jsdom tests without WebGL/Canvas context, still report graph ready
      onGraphReady?.(graph, null as unknown as Sigma)
    }

    return () => {
      if (sigmaRef.current) {
        sigmaRef.current.kill()
        sigmaRef.current = null
      }
    }
  }, [data, selectedLanguages, onlyEntryPoints, onSelectNode, onGraphReady])


  return (
    <div
      data-testid="dependency-graph-container"
      ref={containerRef}
      className={cn(
        'relative w-full h-full min-h-[400px] bg-slate-950 rounded-lg overflow-hidden border border-slate-800',
        className
      )}
    />
  )
}
