import { QueryCache, QueryClient, MutationCache } from '@tanstack/react-query'
import { ApiClientError } from './api/errors'

export const AUTH_REQUIRED_EVENT = 'codegraph:auth-required'

export interface AuthRequiredEventDetail {
  error: ApiClientError
}

export function dispatchAuthRequired(error: ApiClientError) {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent<AuthRequiredEventDetail>(AUTH_REQUIRED_EVENT, {
        detail: { error },
      })
    )
  }
}

function handleGlobalError(error: unknown) {
  if (error instanceof ApiClientError) {
    if (error.status === 401 || error.code === 'AUTH_REQUIRED') {
      dispatchAuthRequired(error)
    }
  }
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    queryCache: new QueryCache({
      onError: (error) => {
        handleGlobalError(error)
      },
    }),
    mutationCache: new MutationCache({
      onError: (error) => {
        handleGlobalError(error)
      },
    }),
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes
        retry: (failureCount, error) => {
          if (error instanceof ApiClientError && (error.status === 401 || error.status === 404)) {
            return false
          }
          return failureCount < 1
        },
        refetchOnWindowFocus: false,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

export const queryClient = createQueryClient()
