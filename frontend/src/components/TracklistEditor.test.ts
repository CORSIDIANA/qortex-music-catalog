// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError } from '../api'
import type { AlbumDetail } from '../types'
import TracklistEditor from './TracklistEditor.vue'

vi.mock('../api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api')>()),
  api: vi.fn(),
}))
const request = vi.mocked(api)
const album: AlbumDetail = {
  id: 1,
  title: 'First album',
  artist: 1,
  artist_name: 'An artist',
  release_year: 2024,
  track_count: 3,
  revision: 4,
  tracks: [
    { id: 11, song: 1, song_title: 'First song', track_number: 1 },
    { id: 12, song: 2, song_title: 'Second song', track_number: 2 },
    { id: 13, song: 3, song_title: 'Third song', track_number: 3 },
  ],
}
function editor(value = album) {
  return mount(TracklistEditor, {
    props: { album: value },
    global: {
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
        FormDialog: {
          props: ['open'],
          emits: ['submit'],
          template:
            '<form v-if="open" @submit.prevent="$emit(\'submit\')"><slot/><button>Confirm</button></form>',
        },
      },
    },
  })
}
beforeEach(() => request.mockReset())
afterEach(() => vi.restoreAllMocks())

describe('tracklist mutation recovery', () => {
  it('sends placement IDs and the original revision only after Save order', async () => {
    const wrapper = editor()
    await wrapper.get('[aria-label="Move First song down"]').trigger('click')
    expect(request).not.toHaveBeenCalled()
    request.mockResolvedValueOnce({ ...album, revision: 5 })
    await wrapper
      .findAll('button')
      .find((button) => button.text() === 'Save order')!
      .trigger('click')
    expect(request).toHaveBeenCalledWith('albums/1/tracks/reorder/', {
      method: 'PUT',
      body: JSON.stringify({ track_ids: [12, 11, 13], revision: 4 }),
    })
    wrapper.unmount()
  })

  it('keeps conflict recovery visible after further local moves', async () => {
    const wrapper = editor()
    await wrapper.get('[aria-label="Move First song down"]').trigger('click')
    request.mockRejectedValueOnce(new ApiError(409, 'Stale revision.'))
    await wrapper
      .findAll('button')
      .find((button) => button.text() === 'Save order')!
      .trigger('click')
    await flushPromises()
    await wrapper.get('[aria-label="Move First song down"]').trigger('click')
    expect(wrapper.text()).toContain('Reload latest')
    expect(wrapper.text()).toContain('changed in another session')
    expect(
      wrapper
        .findAll('button')
        .find((button) => button.text() === 'Save order')!
        .attributes('disabled'),
    ).toBeDefined()
    wrapper.unmount()
  })

  it('locks writes after successful DELETE and failed refresh, then recovers by reload', async () => {
    const wrapper = editor()
    await wrapper.get('[aria-label="Remove First song from album"]').trigger('click')
    request
      .mockResolvedValueOnce(undefined)
      .mockRejectedValueOnce(new ApiError(0, 'Network unavailable.'))
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('The song was removed')
    expect(wrapper.get('[aria-label="Move First song down"]').attributes('disabled')).toBeDefined()
    const refreshed = { ...album, revision: 5, tracks: album.tracks.slice(1), track_count: 2 }
    request.mockResolvedValueOnce(refreshed)
    await wrapper
      .findAll('button')
      .find((button) => button.text() === 'Reload latest tracklist')!
      .trigger('click')
    await flushPromises()
    expect(wrapper.emitted('updated')?.at(-1)).toEqual([refreshed])
    await wrapper.setProps({ album: refreshed })
    expect(wrapper.text()).not.toContain('First song')
    expect(wrapper.text()).toContain('Latest tracklist loaded.')
    wrapper.unmount()
  })

  it('can normalize a single gapped track without an artificial reorder', async () => {
    const wrapper = editor({
      ...album,
      track_count: 1,
      tracks: [{ ...album.tracks[0], track_number: 32767 }],
    })
    request.mockResolvedValueOnce(album)
    await wrapper
      .findAll('button')
      .find((button) => button.text() === 'Renumber from 1')!
      .trigger('click')
    expect(request).toHaveBeenCalledWith('albums/1/tracks/reorder/', {
      method: 'PUT',
      body: JSON.stringify({ track_ids: [11], revision: 4 }),
    })
    wrapper.unmount()
  })
})
