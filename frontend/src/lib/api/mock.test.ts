import { describe, it, expect, beforeEach } from 'vitest'
import { MockApiClient } from './mock'
import { ApiClientError } from './errors'
import type { SourceItem } from './types'

describe('MockApiClient', () => {
  let client: MockApiClient

  beforeEach(() => {
    client = new MockApiClient({ latencyMs: 0, pipelineStepDurationMs: 200 })
  })

  it('returns health check status', async () => {
    const health = await client.health()
    expect(health.status).toBe('ok')
    expect(health.version).toBe('2.0.0')
    expect(health.checks.database).toBe('ok')
  })

  it('lists mock repositories with pagination', async () => {
    const res = await client.listRepositories({ page: 1, page_size: 2 })
    expect(res.items).toHaveLength(2)
    expect(res.total).toBeGreaterThanOrEqual(3)
    expect(res.page).toBe(1)
    expect(res.page_size).toBe(2)
  })

  it('fetches a repository by ID or throws 404', async () => {
    const repo = await client.getRepository('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11')
    expect(repo.name).toBe('fastapi-backend')
    expect(repo.primary_language).toBe('Python')

    await expect(client.getRepository('invalid-id')).rejects.toThrowError(
      ApiClientError
    )
  })

  it('creates an uploaded repo and progresses through pipeline stages', async () => {
    const file = new File(['fake zip content'], 'test-project.zip', {
      type: 'application/zip',
    })
    const created = await client.uploadRepository(file)
    expect(created.id).toBeDefined()
    expect(created.name).toBe('test-project')
    expect(created.status).toBe('pending')

    // Initial status
    const initialStatus = await client.getRepositoryStatus(created.id)
    expect(initialStatus.status).toBe('pending')
    expect(initialStatus.phase).toBe('ingestion')

    // Advance time into stage 2 window (200–400ms): 'ingesting'
    await new Promise((r) => setTimeout(r, 250))
    const stage2 = await client.getRepositoryStatus(created.id)
    expect(stage2.status).toBe('ingesting')
    expect(stage2.phase).toBe('extraction')

    // Advance time into stage 3 window (400–600ms): 'parsing'
    await new Promise((r) => setTimeout(r, 250))
    const stage3 = await client.getRepositoryStatus(created.id)
    expect(stage3.status).toBe('parsing')
    expect(stage3.phase).toBe('parsing')

    // Advance time past all stages (≥800ms from creation): 'ready'
    await new Promise((r) => setTimeout(r, 500))
    const readyStatus = await client.getRepositoryStatus(created.id)
    expect(readyStatus.status).toBe('ready')
    expect(readyStatus.progress).toBe(100)
  })

  it('validates git clone URLs and creates repository on valid HTTPS URL', async () => {
    await expect(
      client.cloneRepository('git@github.com:user/repo.git')
    ).rejects.toThrow('Git URL must use HTTPS protocol')

    const cloned = await client.cloneRepository('https://github.com/org/sample-app.git')
    expect(cloned.id).toBeDefined()
    expect(cloned.name).toBe('sample-app')
    expect(cloned.source).toBe('clone')
  })

  it('deletes repository by ID', async () => {
    const initial = await client.listRepositories()
    const targetId = initial.items[0].id

    await client.deleteRepository(targetId)
    await expect(client.getRepository(targetId)).rejects.toThrow('Repository not found')
  })

  it('lists files and gets file details with symbols', async () => {
    const files = await client.listFiles('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11')
    expect(files.items.length).toBeGreaterThan(0)

    const file = await client.getFile(
      'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      'f1001-auth-py'
    )
    expect(file.path).toBe('app/services/auth.py')
    expect(file.content).toContain('class AuthService')
    expect(file.symbols.length).toBe(3)

    const symbols = await client.getSymbols(
      'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      'f1001-auth-py'
    )
    expect(symbols.some((s) => s.name === 'AuthService')).toBe(true)
  })

  it('returns dependency graph and node details', async () => {
    const graph = await client.getGraph('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11')
    expect(graph.nodes.length).toBe(3)
    expect(graph.edges.length).toBe(3)
    expect(graph.metrics.has_cycles).toBe(false)

    const node = await client.getNodeDetail(
      'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      'f1001-auth-py'
    )
    expect(node.id).toBe('f1001-auth-py')
    expect(node.dependencies.length).toBe(1)
    expect(node.dependents.length).toBe(1)
  })

  it('performs semantic search returning matched chunks', async () => {
    const searchRes = await client.search('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', {
      query: 'login',
    })
    expect(searchRes.results.length).toBeGreaterThan(0)
    expect(searchRes.results[0].content).toContain('login')
  })

  it('manages chat sessions and streams AI responses with sources', async () => {
    const session = await client.createChatSession('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', {
      title: 'Test Session',
    })
    expect(session.session_id).toBeDefined()

    const sessions = await client.listChatSessions('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11')
    expect(sessions.some((s) => s.id === session.session_id)).toBe(true)

    const receivedTokens: string[] = []
    let receivedSources: SourceItem[] = []
    let doneCalled = false

    await client.sendMessageStream(
      'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      session.session_id,
      { question: 'Where is auth defined?' },
      {
        onToken: (tok) => receivedTokens.push(tok),
        onSources: (srcs) => {
          receivedSources = srcs
        },
        onDone: () => {
          doneCalled = true
        },
      }
    )

    expect(receivedTokens.length).toBeGreaterThan(0)
    expect(receivedSources.length).toBeGreaterThan(0)
    expect(doneCalled).toBe(true)

    const history = await client.listChatMessages(
      'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      session.session_id
    )
    expect(history.length).toBe(2)
    expect(history[0].role).toBe('user')
    expect(history[1].role).toBe('assistant')
  })
})
