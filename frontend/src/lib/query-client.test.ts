import { describe, it, expect, vi } from 'vitest'
import { createQueryClient, AUTH_REQUIRED_EVENT } from './query-client'
import { ApiClientError } from './api/errors'

describe('QueryClient Reactive Auth', () => {
  it('dispatches AUTH_REQUIRED_EVENT when query throws 401 ApiClientError', async () => {
    const eventHandler = vi.fn()
    window.addEventListener(AUTH_REQUIRED_EVENT, eventHandler)

    const client = createQueryClient()
    const error401 = new ApiClientError('Auth required', 401, 'AUTH_REQUIRED')

    await expect(
      client.fetchQuery({
        queryKey: ['test-auth-401'],
        queryFn: () => Promise.reject(error401),
      })
    ).rejects.toThrow('Auth required')

    expect(eventHandler).toHaveBeenCalled()
    window.removeEventListener(AUTH_REQUIRED_EVENT, eventHandler)
  })

  it('does not dispatch AUTH_REQUIRED_EVENT on generic 500 error', async () => {
    const eventHandler = vi.fn()
    window.addEventListener(AUTH_REQUIRED_EVENT, eventHandler)

    const client = createQueryClient()
    const error500 = new ApiClientError('Internal server error', 500, 'INTERNAL_ERROR')

    await expect(
      client.fetchQuery({
        queryKey: ['test-500'],
        queryFn: () => Promise.reject(error500),
      })
    ).rejects.toThrow('Internal server error')

    expect(eventHandler).not.toHaveBeenCalled()
    window.removeEventListener(AUTH_REQUIRED_EVENT, eventHandler)
  })
})
