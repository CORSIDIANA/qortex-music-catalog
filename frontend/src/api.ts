export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export function errorMessage(value: unknown): string {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.map(errorMessage).join(' ')
  if (value && typeof value === 'object') {
    return Object.entries(value)
      .map(([key, message]) =>
        ['detail', 'non_field_errors'].includes(key)
          ? errorMessage(message)
          : `${key.replaceAll('_', ' ')}: ${errorMessage(message)}`,
      )
      .join(' ')
  }
  return 'Something went wrong. Please try again.'
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api/${path}`, {
      ...options,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(0, 'Cannot reach the catalog. Check your connection and try again.')
  }
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null)
    throw new ApiError(
      response.status,
      payload
        ? errorMessage(payload)
        : `The request failed (${response.status}). Please try again.`,
    )
  }
  return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>)
}

export function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.'
}
