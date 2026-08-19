import * as React from 'react'
import {
  Search,
  Mail,
  Sun,
  Moon,
  Sparkles,
  Layers,
} from 'lucide-react'
import { Button } from '../button'
import { Input } from '../input'
import { Badge } from '../badge'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '../card'
import { Spinner } from '../spinner'
import { Tooltip } from '../tooltip'
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
  ModalFooter,
} from '../modal'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../tabs'
import { ProgressBar } from '../progress-bar'
import { CodeBlock } from '../code-block'
import { EmptyState } from '../empty-state'
import { ErrorState } from '../error-state'
import { Skeleton } from '../skeleton'
import { useToast } from '../toast'

export function KitchenSink() {
  const [theme, setTheme] = React.useState<'dark' | 'light'>('dark')
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [progressVal, setProgressVal] = React.useState(65)
  const toast = useToast()

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(nextTheme)
    document.documentElement.setAttribute('data-theme', nextTheme)
  }

  const samplePython = `def calculate_pagerank(graph: DependencyGraph, alpha: float = 0.85) -> dict[str, float]:
    """Calculate PageRank score for dependency graph nodes."""
    nodes = list(graph.nodes.keys())
    scores = {node: 1.0 / len(nodes) for node in nodes}
    for _ in range(100):
        new_scores = {}
        for node in nodes:
            incoming = graph.incoming_edges(node)
            rank = (1 - alpha) / len(nodes)
            rank += alpha * sum(scores[src] / len(graph.outgoing_edges(src)) for src in incoming)
            new_scores[node] = rank
        scores = new_scores
    return scores`

  const sampleTs = `interface CodeGraphNode {
  id: string
  path: string
  language: 'python' | 'typescript'
  metrics: {
    pagerank: number
    isEntryPoint: boolean
  }
}

export function renderGraph(nodes: CodeGraphNode[]): void {
  console.log(\`Rendering \${nodes.length} nodes in 3D force layout\`)
}`

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 space-y-12 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold text-indigo-400 flex items-center gap-2">
            <Sparkles className="h-7 w-7 text-indigo-400" /> Design System Kitchen Sink
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Visual verification suite for all CodeGraph v2 UI primitives & composite components
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={toggleTheme}
          leftIcon={theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        >
          {theme === 'dark' ? 'Light Theme' : 'Dark Theme'}
        </Button>
      </div>

      {/* 1. Buttons */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-slate-200 border-b border-slate-800 pb-2">
          1. Buttons
        </h2>
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Destructive</Button>
          <Button variant="primary" isLoading>Loading</Button>
          <Button variant="secondary" disabled>Disabled</Button>
          <Button variant="primary" size="sm">Small</Button>
          <Button variant="primary" size="lg">Large</Button>
          <Button variant="outline" size="icon" aria-label="Search icon">
            <Search className="h-4 w-4" />
          </Button>
        </div>
      </section>

      {/* 2. Inputs */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-slate-200 border-b border-slate-800 pb-2">
          2. Inputs
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Input
            label="Standard Input"
            placeholder="e.g. repo name"
            helperText="Enter a unique repository name"
          />
          <Input
            label="With Icon"
            placeholder="Search code or symbols..."
            leftIcon={<Search className="h-4 w-4" />}
          />
          <Input
            label="With Error State"
            defaultValue="invalid https url"
            error="Git URL must start with https://"
            leftIcon={<Mail className="h-4 w-4" />}
          />
        </div>
      </section>

      {/* 3. Badges */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-slate-200 border-b border-slate-800 pb-2">
          3. Badges
        </h2>
        <div className="flex flex-wrap gap-3 items-center">
          <Badge variant="default">Default / Primary</Badge>
          <Badge variant="secondary">Secondary</Badge>
          <Badge variant="success">Ready (Success)</Badge>
          <Badge variant="warning">Parsing (Warning)</Badge>
          <Badge variant="error">Error</Badge>
          <Badge variant="info">Python 85%</Badge>
          <Badge variant="outline">Outline</Badge>
          <Badge variant="success" size="sm">Small</Badge>
          <Badge variant="info" size="lg">Large</Badge>
        </div>
      </section>

      {/* 4. Cards & Spinners & Tooltips */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-slate-200 border-b border-slate-800 pb-2">
          4. Cards, Spinners & Tooltips
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>fastapi-backend</CardTitle>
                  <CardDescription>Python codebase with FastAPI & SQLAlchemy</CardDescription>
                </div>
                <Badge variant="success">Ready</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-300">
                18 files parsed, 340 dependency edges generated. Ready for semantic search and AI chat.
              </p>
            </CardContent>
            <CardFooter className="flex justify-between">
              <span className="text-xs text-slate-400">Created 2 days ago</span>
              <Tooltip content="Explore dependency graph" side="top">
                <Button size="sm" variant="secondary" leftIcon={<Layers className="h-3.5 w-3.5" />}>
                  Explore
                </Button>
              </Tooltip>
            </CardFooter>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Spinner Sizes & Tooltip Directions</CardTitle>
              <CardDescription>Hover on buttons to see tooltip positions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <Spinner size="sm" />
                <Spinner size="md" color="primary" />
                <Spinner size="lg" color="white" />
              </div>
              <div className="flex gap-2">
                <Tooltip content="Top tooltip" side="top">
                  <Button size="sm" variant="outline">Top</Button>
                </Tooltip>
                <Tooltip content="Bottom tooltip" side="bottom">
                  <Button size="sm" variant="outline">Bottom</Button>
                </Tooltip>
                <Tooltip content="Left tooltip" side="left">
                  <Button size="sm" variant="outline">Left</Button>
                </Tooltip>
                <Tooltip content="Right tooltip" side="right">
                  <Button size="sm" variant="outline">Right</Button>
                </Tooltip>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* 5. Modals & Toasts */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-slate-200 border-b border-slate-800 pb-2">
          5. Modal Dialog & Toasts
        </h2>
        <div className="flex flex-wrap gap-3">
          <Button variant="primary" onClick={() => setIsModalOpen(true)}>
            Open Sample Modal
          </Button>
          <Button
            variant="secondary"
            onClick={() => toast.success('Repository uploaded successfully!', 'Upload Complete')}
          >
            Trigger Success Toast
          </Button>
          <Button
            variant="secondary"
            onClick={() => toast.error('Failed to parse AST in auth.py', 'Parsing Error')}
          >
            Trigger Error Toast
          </Button>
          <Button
            variant="secondary"
            onClick={() => toast.info('Indexing 45 files in the background...', 'Indexing')}
          >
            Trigger Info Toast
          </Button>
          <Button
            variant="secondary"
            onClick={() => toast.warning('API Key is missing for this repository', 'Auth Notice')}
          >
            Trigger Warning Toast
          </Button>
        </div>

        <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)}>
          <ModalHeader>
            <ModalTitle>Add Repository</ModalTitle>
            <ModalDescription>
              Upload a zip archive or enter a Git clone URL to ingest a new codebase.
            </ModalDescription>
          </ModalHeader>
          <ModalContent>
            <Input label="Git Repository URL" placeholder="https://github.com/owner/repo.git" />
          </ModalContent>
          <ModalFooter>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                setIsModalOpen(false)
                toast.success('Cloning repository started')
              }}
            >
              Start Clone
            </Button>
          </ModalFooter>
        </Modal>
      </section>

      {/* 6. Tabs & ProgressBar */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-slate-200 border-b border-slate-800 pb-2">
          6. Tabs & Progress Bar
        </h2>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <ProgressBar
              value={progressVal}
              showPercentage
              label="Pipeline Progress (Extraction -> Parsing)"
              variant="primary"
            />
            <Button
              size="sm"
              variant="outline"
              onClick={() => setProgressVal((p) => (p >= 100 ? 10 : p + 20))}
            >
              Step
            </Button>
          </div>

          <Tabs defaultValue="python">
            <TabsList>
              <TabsTrigger value="python">Python (PageRank)</TabsTrigger>
              <TabsTrigger value="typescript">TypeScript (Graph)</TabsTrigger>
              <TabsTrigger value="bash">Bash Script</TabsTrigger>
            </TabsList>
            <TabsContent value="python">
              <CodeBlock code={samplePython} language="python" filename="graph/pagerank.py" />
            </TabsContent>
            <TabsContent value="typescript">
              <CodeBlock code={sampleTs} language="typescript" filename="src/render.ts" />
            </TabsContent>
            <TabsContent value="bash">
              <CodeBlock
                code={`# Ingest repository via CLI\ncurl -X POST http://localhost:8000/api/v1/repositories/clone \\\n  -H "Content-Type: application/json" \\\n  -d '{"git_url": "https://github.com/fastapi/fastapi.git"}'`}
                language="bash"
              />
            </TabsContent>
          </Tabs>
        </div>
      </section>

      {/* 7. Empty & Error States, Skeletons */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-slate-200 border-b border-slate-800 pb-2">
          7. Empty State, Error State & Skeletons
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <EmptyState
            title="No repositories found"
            description="You haven't uploaded or cloned any repositories yet."
            action={<Button size="sm">Upload Repo</Button>}
          />
          <ErrorState
            title="Graph computation failed"
            message="Cyclic dependency detected in circular import chain."
            onRetry={() => toast.info('Retrying graph layout...')}
          />
          <div className="space-y-3 p-4 rounded-xl border border-slate-800 bg-slate-900/60">
            <div className="flex items-center gap-3">
              <Skeleton variant="circular" className="h-10 w-10 shrink-0" />
              <div className="space-y-2 flex-1">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
            <Skeleton className="h-20 w-full" />
          </div>
        </div>
      </section>
    </div>
  )
}

export default KitchenSink
