// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, expect, it, vi } from 'vitest'
import { api } from '../api'
import AddSongPanel from './AddSongPanel.vue'

vi.mock('../api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api')>()),
  api: vi.fn(),
}))
const request = vi.mocked(api)
beforeEach(() => request.mockReset())

it('retries a failed next page without losing earlier suggestions or skipping results', async () => {
  request.mockResolvedValueOnce({
    results: [{ id: 1, title: 'First suggestion', album_count: 1 }],
    next: 'page2',
  })
  const wrapper = mount(AddSongPanel, { props: { placedSongs: [], busy: false } })
  await flushPromises()
  request.mockRejectedValueOnce(new Error('Temporary failure'))
  await wrapper
    .findAll('button')
    .find((button) => button.text() === 'Show more songs')!
    .trigger('click')
  await flushPromises()
  expect(request.mock.calls[1][0]).toContain('page=2')
  request.mockResolvedValueOnce({
    results: [{ id: 2, title: 'Second suggestion', album_count: 0 }],
    next: null,
  })
  await wrapper
    .findAll('button')
    .find((button) => button.text() === 'Retry')!
    .trigger('click')
  await flushPromises()
  expect(request.mock.calls[2][0]).toContain('page=2')
  expect(wrapper.text()).toContain('First suggestion')
  expect(wrapper.text()).toContain('Second suggestion')
  wrapper.unmount()
})

it('prevents duplicate placement while keeping the existing song visible', async () => {
  request.mockResolvedValueOnce({
    results: [{ id: 7, title: 'Shared song', album_count: 2 }],
    next: null,
  })
  const wrapper = mount(AddSongPanel, { props: { placedSongs: [7], busy: false } })
  await flushPromises()
  const suggestion = wrapper.get('.song-suggestions button')
  expect(suggestion.text()).toContain('Already on this album')
  expect(suggestion.attributes('disabled')).toBeDefined()
  await suggestion.trigger('click')
  expect(wrapper.emitted('add')).toBeUndefined()
  wrapper.unmount()
})
