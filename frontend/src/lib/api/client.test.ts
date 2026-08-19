import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { RealApiClient } from './client'
import { ApiClientError } from './errors'
import type { SourceItem } from './types'

describe('RealApiClient', () => {
  let client: RealApiClient
  const originalFetch = global.fetch

  beforeEach(() => {
    client = new RealApiClient({
      baseUrl: 'http://localhost:8000',
      getApiKey: () => 'test-api-key-123',
    })
  })

  afterEach(() => {
    global.fetch = originalFetch
  })

  it('sends X-API-Key header and parses JSON correctly', async () => {
    const mockData = {
      items: [
        {
          id: 'repo-1',
          name: 'backend',
          slug: 'backend',
          status: 'ready',
          source: 'upload',
          file_count: 5,
          created_at: '2026-08-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockData,
    })

    const res = await client.listRepositories({ page: 2, page_size: 10 })
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/repositories?page=2&page_size=10',
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-API-Key': 'test-api-key-123',
          'Content-Type': 'application/json',
        }),
      })
    )
    expect(res.items[0].name).toBe('backend')
  })

  it('parses error payloads and throws typed ApiClientError', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({
        error: {
          code: 'REPO_NOT_FOUND',
          message: 'Repository not found',
          details: { id: 'invalid-id' },
        },
      }),
    })

    await expect(client.getRepository('invalid-id')).rejects.toSatisfy(
      (err: unknown) => {
        return (
          err instanceof ApiClientError &&
          err.status === 404 &&
          err.code === 'REPO_NOT_FOUND' &&
          err.message === 'Repository not found'
        )
      }
    )
  })

  it('handles 401 AUTH_REQUIRED error', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({
        error: {
          code: 'AUTH_REQUIRED',
          message: 'Authentication key required',
          details: {},
        },
      }),
    })

    await expect(
      client.cloneRepository('https://github.com/org/repo.git')
    ).rejects.toSatisfy((err: unknown) => {
      return (
        err instanceof ApiClientError &&
        err.status === 401 &&
        err.code === 'AUTH_REQUIRED'
      )
    })
  })

  it('handles file upload via FormData without setting Content-Type header', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        id: 'repo-new',
        name: 'test-upload',
        slug: 'test-upload',
        status: 'pending',
        source: 'upload',
        size_bytes: 1024,
        file_count: 0,
        primary_language: null,
        detected_languages: null,
        frameworks: null,
        created_at: '2026-08-01T00:00:00Z',
      }),
    })

    const file = new File(['content'], 'repo.zip', { type: 'application/zip' })
    const res = await client.uploadRepository(file, 'custom-name')

    expect(res.name).toBe('test-upload')
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/repositories',
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData),
      })
    )
  })

  it('parses SSE stream tokens and sources for chat streaming', async () => {
    const encoder = new TextEncoder()
    const chunks = [
      'data: Hello\n\n',
      'data:  world!\n\n',
      'data: __sources__:[{"path":"src/main.py","start_line":1,"end_line":10}]\n\n',
      'data: [DONE]\n\n',
    ]

    let chunkIndex = 0
    const mockStream = new ReadableStream({
      pull(controller) {
        if (chunkIndex < chunks.length) {
          controller.enqueue(encoder.encode(chunks[chunkIndex]))
          chunkIndex++
        } else {
          controller.close()
        }
      },
    })

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: mockStream,
    })

    const tokens: string[] = []
    let sources: SourceItem[] = []
    let done = false

    await client.sendMessageStream(
      'repo-1',
      'session-1',
      { question: 'Hello?' },
      {
        onToken: (tok) => tokens.push(tok),
        onSources: (srcs) => {
          sources = srcs
        },
        onDone: () => {
          done = true
        },
      }
    )

    expect(tokens.join('')).toBe('Hello world!')
    expect(sources).toEqual([
      { path: 'src/main.py', start_line: 1, end_line: 10 },
    ])
    expect(done).toBe(true)
  })
})
