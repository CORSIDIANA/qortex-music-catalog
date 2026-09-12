// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { api } from '../api'
import App from '../App.vue'
import type { AlbumDetail } from '../types'
import AlbumPage from './AlbumPage.vue'

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
  track_count: 2,
  revision: 4,
  tracks: [
    { id: 11, song: 1, song_title: 'First song', track_number: 1 },
    { id: 12, song: 2, song_title: 'Second song', track_number: 2 },
  ],
}
beforeEach(() => request.mockReset())
afterEach(() => vi.restoreAllMocks())

it.each(['/albums/2', '/songs'])(
  'asks before discarding the draft when navigating to %s',
  async (destination) => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/albums/:id', component: AlbumPage },
        { path: '/:pathMatch(.*)*', component: { template: '<p>Another page</p>' } },
      ],
    })
    await router.push('/albums/1')
    await router.isReady()
    request.mockResolvedValue(album)
    const wrapper = mount(App, {
      global: { plugins: [router], stubs: { FormDialog: true, AlbumForm: true } },
    })
    try {
      await flushPromises()
      await wrapper.get('[aria-label="Move First song down"]').trigger('click')
      expect(wrapper.text()).toContain('Unsaved order')
      const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
      await router.push(destination)
      await flushPromises()
      expect(confirm).toHaveBeenCalledTimes(1)
      expect(router.currentRoute.value.path).toBe('/albums/1')
      expect(wrapper.text()).toContain('Unsaved order')

      confirm.mockReturnValue(true)
      await router.push(destination)
      await flushPromises()
      expect(confirm).toHaveBeenCalledTimes(2)
      expect(router.currentRoute.value.path).toBe(destination)
      expect(wrapper.text()).not.toContain('Unsaved order')
    } finally {
      wrapper.unmount()
    }
  },
)
