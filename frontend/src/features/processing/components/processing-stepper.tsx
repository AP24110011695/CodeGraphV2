import * as React from 'react'
import {
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
  Upload,
  Scissors,
  Code2,
  Share2,
  Search,
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import { ProgressBar } from '@/components/ui/progress-bar'
import { ErrorState } from '@/components/ui/error-state'
import type { PipelinePhase, RepositoryStatus } from '@/lib/api/types'

// Canonical five-stage pipeline — must match BACKEND.md verbatim
const PIPELINE_STAGES: Array<{
  phase: PipelinePhase
  label: string
  description: string
  icon: React.ReactNode
}> = [
  {
    phase: 'ingestion',
    label: 'Ingestion',
    description: 'Receiving and extracting the uploaded archive or cloned repository',
    icon: <Upload className="h-4 w-4" />,
  },
  {
    phase: 'extraction',
    label: 'Extraction',
    description: 'Unpacking file tree and cataloguing source files',
    icon: <Scissors className="h-4 w-4" />,
  },
  {
    phase: 'parsing',
    label: 'Parsing',
    description: 'Running AST parsers to extract symbols and structure',
    icon: <Code2 className="h-4 w-4" />,
  },
  {
    phase: 'graph',
    label: 'Graph',
    description: 'Building the dependency graph from import/export relationships',
    icon: <Share2 className="h-4 w-4" />,
  },
  {
    phase: 'indexing',
    label: 'Indexing',
    description: 'Generating semantic embeddings and building the search index',
    icon: <Search className="h-4 w-4" />,
  },
]

type StageState = 'pending' | 'active' | 'done' | 'error'

function getStageState(
  stagePhase: PipelinePhase,
  currentPhase: PipelinePhase | null,
  overallStatus: RepositoryStatus | null
): StageState {
  if (overallStatus === 'error') {
    // Only the current (or last active) stage is error; prior stages are done
    const currentIdx = PIPELINE_STAGES.findIndex((s) => s.phase === currentPhase)
    const stageIdx = PIPELINE_STAGES.findIndex((s) => s.phase === stagePhase)
    if (stageIdx < currentIdx) return 'done'
    if (stageIdx === currentIdx) return 'error'
    return 'pending'
  }

  if (overallStatus === 'ready') return 'done'

  const currentIdx = PIPELINE_STAGES.findIndex((s) => s.phase === currentPhase)
  const stageIdx = PIPELINE_STAGES.findIndex((s) => s.phase === stagePhase)

  if (currentIdx === -1) return 'pending'
  if (stageIdx < currentIdx) return 'done'
  if (stageIdx === currentIdx) return 'active'
  return 'pending'
}

const stageIconMap: Record<StageState, React.ReactNode> = {
  pending: <Circle className="h-5 w-5 text-slate-600" />,
  active: <Loader2 className="h-5 w-5 text-indigo-400 animate-spin" />,
  done: <CheckCircle2 className="h-5 w-5 text-emerald-400" />,
  error: <XCircle className="h-5 w-5 text-rose-400" />,
}

const stageLabelColor: Record<StageState, string> = {
  pending: 'text-slate-500',
  active: 'text-indigo-300 font-semibold',
  done: 'text-emerald-300',
  error: 'text-rose-300',
}

export interface ProcessingStepperProps {
  status: RepositoryStatus | null
  progress: number
  phase: PipelinePhase | null
  errorMessage: string | null
  onRetry?: () => void
  isRetrying?: boolean
  className?: string
}

export function ProcessingStepper({
  status,
  progress,
  phase,
  errorMessage,
  onRetry,
  isRetrying = false,
  className,
}: ProcessingStepperProps) {
  const isError = status === 'error'
  const isReady = status === 'ready'

  return (
    <div className={cn('space-y-6', className)}>
      {/* Progress header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium text-slate-200">
            {isReady
              ? 'Processing complete'
              : isError
                ? 'Processing failed'
                : 'Processing repository…'}
          </span>
          <span
            className={cn(
              'tabular-nums font-mono text-xs',
              isError ? 'text-rose-400' : isReady ? 'text-emerald-400' : 'text-slate-400'
            )}
          >
            {progress}%
          </span>
        </div>

        <ProgressBar
          value={progress}
          variant={isError ? 'error' : isReady ? 'success' : 'primary'}
          size="md"
          aria-label="Repository processing progress"
        />
      </div>

      {/* Five-stage stepper */}
      <ol className="relative space-y-0" aria-label="Pipeline stages">
        {PIPELINE_STAGES.map((stage, idx) => {
          const stageState = getStageState(stage.phase, phase, status)
          const isLast = idx === PIPELINE_STAGES.length - 1

          return (
            <li key={stage.phase} className="relative flex items-start gap-4 pb-6 last:pb-0">
              {/* Connector line */}
              {!isLast && (
                <div
                  className={cn(
                    'absolute left-[9px] top-6 bottom-0 w-0.5',
                    stageState === 'done' ? 'bg-emerald-700' : 'bg-slate-800'
                  )}
                  aria-hidden="true"
                />
              )}

              {/* Stage icon */}
              <div className="relative z-10 flex shrink-0 items-center justify-center">
                {stageIconMap[stageState]}
              </div>

              {/* Stage content */}
              <div className="flex-1 min-w-0 pt-0.5">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'text-sm',
                      stageLabelColor[stageState]
                    )}
                  >
                    {stage.label}
                  </span>
                  {stageState === 'active' && (
                    <span className="rounded-full bg-indigo-500/15 border border-indigo-500/30 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-300 uppercase tracking-wider">
                      Active
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-0.5">{stage.description}</p>

                {/* Progress bar only for the active stage */}
                {stageState === 'active' && (
                  <div className="mt-2">
                    <ProgressBar
                      value={progress}
                      variant="primary"
                      size="sm"
                      aria-label={`${stage.label} stage progress`}
                    />
                  </div>
                )}
              </div>
            </li>
          )
        })}
      </ol>

      {/* Error state */}
      {isError && (
        <ErrorState
          title="Processing failed"
          message={
            errorMessage ||
            'An unexpected error occurred during repository processing. You can retry or re-upload the repository.'
          }
          onRetry={onRetry}
          retryText="Retry processing"
          isRetrying={isRetrying}
        />
      )}
    </div>
  )
}
