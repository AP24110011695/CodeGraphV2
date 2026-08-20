import * as React from 'react'
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  FileCode,
  FileText,
  FileImage,
  File,
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import type { FileListItem } from '@/lib/api/types'

// ─── Tree data model ─────────────────────────────────────────────────────────

export interface TreeFile {
  type: 'file'
  id: string
  name: string
  path: string
  language: string
  size_bytes: number
  line_count: number
  is_binary: boolean
}

export interface TreeDir {
  type: 'dir'
  name: string
  path: string
  children: TreeNode[]
}

export type TreeNode = TreeFile | TreeDir

/**
 * Converts a flat list of FileListItem (each with a `/`-separated path) into
 * a nested directory tree. Pure client-side — no backend tree endpoint exists.
 */
export function buildTree(files: FileListItem[]): TreeNode[] {
  const root: TreeDir = { type: 'dir', name: '', path: '', children: [] }

  for (const file of files) {
    const parts = file.path.split('/')
    let current = root

    for (let i = 0; i < parts.length - 1; i++) {
      const segment = parts[i]
      const dirPath = parts.slice(0, i + 1).join('/')
      let child = current.children.find(
        (n) => n.type === 'dir' && n.name === segment
      ) as TreeDir | undefined

      if (!child) {
        child = { type: 'dir', name: segment, path: dirPath, children: [] }
        current.children.push(child)
      }
      current = child
    }

    const fileName = parts[parts.length - 1]
    current.children.push({
      type: 'file',
      id: file.id,
      name: fileName,
      path: file.path,
      language: file.language,
      size_bytes: file.size_bytes,
      line_count: file.line_count,
      is_binary: file.is_binary,
    })
  }

  // Sort: dirs first, then files, alphabetically within each group
  function sortChildren(dir: TreeDir): void {
    dir.children.sort((a, b) => {
      if (a.type !== b.type) return a.type === 'dir' ? -1 : 1
      return a.name.localeCompare(b.name)
    })
    dir.children.filter((n): n is TreeDir => n.type === 'dir').forEach(sortChildren)
  }
  sortChildren(root)

  return root.children
}

// ─── File icon helper ─────────────────────────────────────────────────────────

function FileIcon({ language, className }: { language: string; className?: string }) {
  const lang = language.toLowerCase()
  if (['python', 'typescript', 'javascript', 'java', 'go', 'rust', 'cpp', 'c', 'csharp'].includes(lang)) {
    return <FileCode className={cn('text-indigo-400', className)} />
  }
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].includes(lang)) {
    return <FileImage className={cn('text-amber-400', className)} />
  }
  if (['md', 'txt', 'rst'].includes(lang)) {
    return <FileText className={cn('text-slate-400', className)} />
  }
  return <File className={cn('text-slate-500', className)} />
}

// ─── FileTree component ───────────────────────────────────────────────────────

export interface FileTreeProps {
  nodes: TreeNode[]
  selectedFileId: string | null
  onSelectFile: (file: TreeFile) => void
  defaultExpanded?: boolean
  className?: string
}

interface TreeNodeProps {
  node: TreeNode
  depth: number
  selectedFileId: string | null
  onSelectFile: (file: TreeFile) => void
  defaultExpanded: boolean
}

function TreeNodeItem({
  node,
  depth,
  selectedFileId,
  onSelectFile,
  defaultExpanded,
}: TreeNodeProps) {
  const [expanded, setExpanded] = React.useState(defaultExpanded || depth === 0)
  const indentPx = depth * 12

  if (node.type === 'dir') {
    return (
      <li>
        <button
          type="button"
          onClick={() => setExpanded((e) => !e)}
          className="flex w-full items-center gap-1.5 rounded px-2 py-1 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-slate-100 transition-colors text-left"
          style={{ paddingLeft: `${8 + indentPx}px` }}
          aria-expanded={expanded}
        >
          <span className="shrink-0 text-slate-500">
            {expanded ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
          </span>
          <span className="shrink-0 text-amber-400">
            {expanded ? (
              <FolderOpen className="h-3.5 w-3.5" />
            ) : (
              <Folder className="h-3.5 w-3.5" />
            )}
          </span>
          <span className="truncate">{node.name}</span>
        </button>

        {expanded && (
          <ul role="group">
            {node.children.map((child) => (
              <TreeNodeItem
                key={child.type === 'file' ? child.id : child.path}
                node={child}
                depth={depth + 1}
                selectedFileId={selectedFileId}
                onSelectFile={onSelectFile}
                defaultExpanded={defaultExpanded}
              />
            ))}
          </ul>
        )}
      </li>
    )
  }

  // File node
  const isSelected = node.id === selectedFileId
  return (
    <li>
      <button
        type="button"
        onClick={() => onSelectFile(node)}
        className={cn(
          'flex w-full items-center gap-1.5 rounded px-2 py-1 text-xs font-mono transition-colors text-left',
          isSelected
            ? 'bg-indigo-600/25 text-indigo-300 font-semibold'
            : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
        )}
        style={{ paddingLeft: `${8 + indentPx}px` }}
        aria-selected={isSelected}
        title={node.path}
      >
        <FileIcon language={node.language} className="h-3.5 w-3.5 shrink-0" />
        <span className="truncate">{node.name}</span>
        {node.is_binary && (
          <span className="ml-auto shrink-0 text-[10px] text-slate-600 font-sans">bin</span>
        )}
      </button>
    </li>
  )
}

export function FileTree({
  nodes,
  selectedFileId,
  onSelectFile,
  defaultExpanded = true,
  className,
}: FileTreeProps) {
  if (nodes.length === 0) {
    return (
      <div className={cn('p-4 text-xs text-slate-500 italic', className)}>
        No files found in this repository.
      </div>
    )
  }

  return (
    <nav aria-label="File tree" className={cn('overflow-y-auto', className)}>
      <ul role="tree">
        {nodes.map((node) => (
          <TreeNodeItem
            key={node.type === 'file' ? node.id : node.path}
            node={node}
            depth={0}
            selectedFileId={selectedFileId}
            onSelectFile={onSelectFile}
            defaultExpanded={defaultExpanded}
          />
        ))}
      </ul>
    </nav>
  )
}
