/**
 * Canonical typed API error for CodeGraph v2.
 * Matches backend error response shape: { error: { code, message, details } }
 */
export class ApiClientError extends Error {
  readonly code: string
  readonly status: number
  readonly details: Record<string, unknown>

  constructor(
    message: string,
    status: number = 500,
    code: string = 'UNKNOWN_ERROR',
    details: Record<string, unknown> = {}
  ) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.code = code
    this.details = details
    Object.setPrototypeOf(this, ApiClientError.prototype)
  }

  static fromErrorResponse(status: number, data?: unknown): ApiClientError {
    if (
      data &&
      typeof data === 'object' &&
      'error' in data &&
      typeof (data as Record<string, unknown>).error === 'object'
    ) {
      const err = (data as { error: { code?: string; message?: string; details?: Record<string, unknown> } }).error
      return new ApiClientError(
        err.message || 'An API error occurred',
        status,
        err.code || 'UNKNOWN_ERROR',
        err.details || {}
      )
    }

    if (
      data &&
      typeof data === 'object' &&
      'detail' in data &&
      typeof (data as Record<string, unknown>).detail === 'string'
    ) {
      return new ApiClientError((data as { detail: string }).detail, status, 'VALIDATION_ERROR')
    }

    return new ApiClientError(
      `Request failed with status ${status}`,
      status,
      status === 401 ? 'AUTH_REQUIRED' : 'HTTP_ERROR'
    )
  }
}
