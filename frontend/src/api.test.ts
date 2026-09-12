import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, errorMessage } from './api'

afterEach(() => vi.unstubAllGlobals())
describe('API feedback', () => {
  it('preserves field validation and nested reorder errors', () => {
    expect(
      errorMessage({
        track_ids: ['Each placement must appear exactly once.'],
        detail: 'No changes saved.',
      }),
    ).toBe('track ids: Each placement must appear exactly once. No changes saved.')
  })
  it('returns no JSON for successful deletion', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })))
    await expect(api('albums/1/', { method: 'DELETE' })).resolves.toBeUndefined()
  })
  it('keeps conflict status for the stale-draft recovery flow', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ detail: 'Tracklist changed.' }), { status: 409 }),
        ),
    )
    await expect(api('albums/1/tracks/reorder/')).rejects.toMatchObject({
      status: 409,
      message: 'Tracklist changed.',
    })
  })
  it('shows useful feedback for an unavailable backend', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    await expect(api('albums/')).rejects.toMatchObject({
      status: 0,
      message: 'Cannot reach the catalog. Check your connection and try again.',
    })
  })
  it('does not expose an HTML error page', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('<html>upstream unavailable</html>', { status: 502 })),
    )
    await expect(api('albums/')).rejects.toMatchObject({
      status: 502,
      message: 'The request failed (502). Please try again.',
    })
  })
})
