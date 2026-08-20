import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FileTree, buildTree } from './components/file-tree'
import { CodeViewer } from './components/code-viewer'
import { SymbolPanel } from './components/symbol-panel'
import { ResizablePanes } from './components/resizable-panes'
import type { FileListItem, FileDetail, SymbolResponse } from '@/lib/api/types'

// ─── buildTree ────────────────────────────────────────────────────────────────

describe('buildTree', () => {
  const flatFiles: FileListItem[] = [
    { id: 'f1', path: 'app/services/auth.py', language: 'python', size_bytes: 1000, line_count: 30, is_binary: false },
    { id: 'f2', path: 'app/api/routes.py', language: 'python', size_bytes: 800, line_count: 20, is_binary: false },
    { id: 'f3', path: 'app/config.py', language: 'python', size_bytes: 400, line_count: 10, is_binary: false },
    { id: 'f4', path: 'README.md', language: 'markdown', size_bytes: 200, line_count: 5, is_binary: false },
  ]

  it('builds a nested directory structure from a flat list', () => {
    const tree = buildTree(flatFiles)

    const appDir = tree.find((n) => n.type === 'dir' && n.name === 'app')
    expect(appDir).toBeDefined()
    expect(tree.find((n) => n.type === 'file' && n.name === 'README.md')).toBeDefined()
  })

  it('correctly nests subdirectories', () => {
    const tree = buildTree(flatFiles)
    const appDir = tree.find((n) => n.type === 'dir' && n.name === 'app')
    expect(appDir?.type).toBe('dir')
    if (appDir?.type === 'dir') {
      const servicesDir = appDir.children.find(
        (n) => n.type === 'dir' && n.name === 'services'
      )
      expect(servicesDir).toBeDefined()
    }
  })

  it('returns an empty array for an empty file list', () => {
    expect(buildTree([])).toEqual([])
  })

  it('sorts directories before files', () => {
    const tree = buildTree(flatFiles)
    // First child of root should be the 'app' directory
    expect(tree[0].type).toBe('dir')
    expect(tree[0].name).toBe('app')
    // README.md file comes after the directory
    expect(tree[1].type).toBe('file')
  })
})

// ─── FileTree ─────────────────────────────────────────────────────────────────

describe('FileTree', () => {
  const flatFiles: FileListItem[] = [
    { id: 'f1', path: 'src/index.ts', language: 'typescript', size_bytes: 500, line_count: 10, is_binary: false },
    { id: 'f2', path: 'src/utils.ts', language: 'typescript', size_bytes: 400, line_count: 8, is_binary: false },
    { id: 'f3', path: 'README.md', language: 'markdown', size_bytes: 100, line_count: 4, is_binary: false },
  ]
  const nodes = buildTree(flatFiles)
  const onSelectFile = vi.fn()

  beforeEach(() => onSelectFile.mockClear())

  it('renders directory and file nodes', () => {
    render(
      <FileTree
        nodes={nodes}
        selectedFileId={null}
        onSelectFile={onSelectFile}
      />
    )
    expect(screen.getByText('src')).toBeInTheDocument()
    expect(screen.getByText('README.md')).toBeInTheDocument()
  })

  it('calls onSelectFile when a file is clicked', async () => {
    const user = userEvent.setup()
    render(
      <FileTree
        nodes={nodes}
        selectedFileId={null}
        onSelectFile={onSelectFile}
      />
    )
    // Click on README.md (top-level file)
    await user.click(screen.getByText('README.md'))
    expect(onSelectFile).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'f3', path: 'README.md' })
    )
  })

  it('collapses a directory when its button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <FileTree
        nodes={nodes}
        selectedFileId={null}
        onSelectFile={onSelectFile}
        defaultExpanded
      />
    )
    // Collapse the 'src' directory
    const srcButton = screen.getByRole('button', { name: /src/i })
    await user.click(srcButton)
    // After collapse, the files inside should not be visible
    expect(screen.queryByText('index.ts')).not.toBeInTheDocument()
  })

  it('marks the selected file with aria-selected', () => {
    render(
      <FileTree
        nodes={nodes}
        selectedFileId="f3"
        onSelectFile={onSelectFile}
      />
    )
    const readmeBtn = screen.getByText('README.md').closest('button')
    expect(readmeBtn).toHaveAttribute('aria-selected', 'true')
  })

  it('shows binary marker for binary files', () => {
    const binaryNodes = buildTree([
      { id: 'b1', path: 'image.png', language: 'png', size_bytes: 5000, line_count: 0, is_binary: true },
    ])
    render(
      <FileTree nodes={binaryNodes} selectedFileId={null} onSelectFile={onSelectFile} />
    )
    expect(screen.getByText('bin')).toBeInTheDocument()
  })
})

// ─── CodeViewer ───────────────────────────────────────────────────────────────

describe('CodeViewer', () => {
  const mockFile: FileDetail = {
    id: 'f1',
    repository_id: 'repo-1',
    path: 'src/main.ts',
    language: 'typescript',
    size_bytes: 100,
    line_count: 5,
    is_binary: false,
    content: 'const x = 1\nconsole.log(x)',
    error: null,
    symbols: [],
  }

  it('renders code content for a text file', async () => {
    render(<CodeViewer file={mockFile} />)
    // Content is passed to CodeBlock which renders it
    await waitFor(() => {
      expect(screen.getByText(/const x = 1/i)).toBeInTheDocument()
    })
  })

  it('renders binary placeholder for a binary file', () => {
    const binaryFile: FileDetail = { ...mockFile, is_binary: true, content: null }
    render(<CodeViewer file={binaryFile} />)
    expect(screen.getByTestId('binary-placeholder')).toBeInTheDocument()
    expect(screen.getByText('Binary file')).toBeInTheDocument()
  })

  it('renders binary placeholder when content is null', () => {
    const noContentFile: FileDetail = { ...mockFile, content: null }
    render(<CodeViewer file={noContentFile} />)
    expect(screen.getByTestId('binary-placeholder')).toBeInTheDocument()
  })

  it('renders placeholder when no file is selected', () => {
    render(<CodeViewer file={null} />)
    expect(screen.getByText(/select a file/i)).toBeInTheDocument()
  })

  it('renders loading skeleton when isLoading is true', () => {
    const { container } = render(<CodeViewer file={null} isLoading />)
    // Skeletons render as divs with animate-pulse class
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('renders error state when error is provided', () => {
    render(<CodeViewer file={null} error={new Error('Network timeout')} />)
    expect(screen.getByText('Failed to load file')).toBeInTheDocument()
    expect(screen.getByText('Network timeout')).toBeInTheDocument()
  })
})

// ─── SymbolPanel ──────────────────────────────────────────────────────────────

describe('SymbolPanel', () => {
  const symbols: SymbolResponse[] = [
    { id: 's1', name: 'AuthService', kind: 'class', start_line: 10, end_line: 45, is_exported: true, docstring: null },
    { id: 's2', name: 'login', kind: 'method', start_line: 18, end_line: 32, is_exported: true, docstring: null },
    { id: 's3', name: 'verify_token', kind: 'method', start_line: 34, end_line: 44, is_exported: false, docstring: null },
    { id: 's4', name: 'get_settings', kind: 'function', start_line: 5, end_line: 8, is_exported: true, docstring: null },
  ]

  it('renders symbols grouped by kind', () => {
    const onScroll = vi.fn()
    render(<SymbolPanel symbols={symbols} onScrollToLine={onScroll} />)

    expect(screen.getByText('Classes')).toBeInTheDocument()
    expect(screen.getByText('Methods')).toBeInTheDocument()
    expect(screen.getByText('Functions')).toBeInTheDocument()
    expect(screen.getByText('AuthService')).toBeInTheDocument()
    expect(screen.getByText('login')).toBeInTheDocument()
    expect(screen.getByText('get_settings')).toBeInTheDocument()
  })

  it('calls onScrollToLine with the correct start_line when a symbol is clicked', async () => {
    const user = userEvent.setup()
    const onScroll = vi.fn()
    render(<SymbolPanel symbols={symbols} onScrollToLine={onScroll} />)

    await user.click(screen.getByText('AuthService'))
    expect(onScroll).toHaveBeenCalledWith(10)
  })

  it('calls onScrollToLine with the method start line', async () => {
    const user = userEvent.setup()
    const onScroll = vi.fn()
    render(<SymbolPanel symbols={symbols} onScrollToLine={onScroll} />)

    await user.click(screen.getByText('verify_token'))
    expect(onScroll).toHaveBeenCalledWith(34)
  })

  it('shows empty state when no symbols are present', () => {
    render(<SymbolPanel symbols={[]} onScrollToLine={vi.fn()} />)
    expect(screen.getByText(/no symbols found/i)).toBeInTheDocument()
  })
})

// ─── ResizablePanes ───────────────────────────────────────────────────────────

describe('ResizablePanes', () => {
  const panes = [
    { id: 'a', minWidth: 100, defaultWidth: 200 },
    { id: 'b', minWidth: 100, defaultWidth: 400 },
    { id: 'c', minWidth: 100, defaultWidth: 200 },
  ]

  it('renders all children', () => {
    render(
      <ResizablePanes panes={panes} storageKey="test:panes">
        <div>Pane A</div>
        <div>Pane B</div>
        <div>Pane C</div>
      </ResizablePanes>
    )
    expect(screen.getByText('Pane A')).toBeInTheDocument()
    expect(screen.getByText('Pane B')).toBeInTheDocument()
    expect(screen.getByText('Pane C')).toBeInTheDocument()
  })

  it('renders separator handles between panes', () => {
    render(
      <ResizablePanes panes={panes} storageKey="test:panes">
        <div>Pane A</div>
        <div>Pane B</div>
        <div>Pane C</div>
      </ResizablePanes>
    )
    // Two separators for three panes
    const separators = screen.getAllByRole('separator')
    expect(separators).toHaveLength(2)
  })

  it('sets initial pane widths from defaultWidth', () => {
    const { container } = render(
      <ResizablePanes panes={panes} storageKey="test:panes-width">
        <div>A</div>
        <div>B</div>
        <div>C</div>
      </ResizablePanes>
    )
    // First pane div should have flex-basis: 200px
    const paneElements = container.querySelectorAll(':scope > div > div')
    expect((paneElements[0] as HTMLElement).style.flexBasis).toBe('200px')
  })

  it('updates pane width on drag', () => {
    const { container } = render(
      <ResizablePanes panes={panes} storageKey="test:panes-drag">
        <div>A</div>
        <div>B</div>
        <div>C</div>
      </ResizablePanes>
    )
    const handle = screen.getAllByRole('separator')[0]
    fireEvent.pointerDown(handle, { clientX: 200, pointerId: 1 })
    fireEvent.pointerMove(container.firstChild as Element, { clientX: 250 })
    fireEvent.pointerUp(container.firstChild as Element)

    // First pane should now be wider (200 + 50 = 250)
    const paneElements = container.querySelectorAll(':scope > div > div')
    const newWidth = parseFloat((paneElements[0] as HTMLElement).style.flexBasis)
    expect(newWidth).toBeGreaterThan(200)
  })
})
