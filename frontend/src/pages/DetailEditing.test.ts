// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../api'
import ArtistPage from './ArtistPage.vue'
import SongPage from './SongPage.vue'

vi.mock('../api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api')>()),
  api: vi.fn(),
}))
vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '1' } }),
  useRouter: () => ({ push: vi.fn() }),
}))
const request = vi.mocked(api)
const stubs = {
  RouterLink: { template: '<a><slot /></a>' },
  AlbumForm: true,
  FormDialog: {
    props: ['open'],
    emits: ['submit'],
    template:
      '<form v-if="open" @submit.prevent="$emit(\'submit\')"><slot/><button>Save</button></form>',
  },
}
beforeEach(() => request.mockReset())

describe('editing summary-only API representations', () => {
  it('refreshes song detail after PATCH so its appearances remain visible', async () => {
    const detail = {
      id: 1,
      title: 'Old title',
      album_count: 1,
      appears_on: [
        { album: 5, album_title: 'Shared home', artist_name: 'Artist', track_number: 7 },
      ],
    }
    request.mockResolvedValueOnce(detail)
    const wrapper = mount(SongPage, { global: { stubs } })
    await flushPromises()
    await wrapper
      .findAll('button')
      .find((button) => button.text() === 'Edit song')!
      .trigger('click')
    await wrapper.get('input').setValue('New title')
    request
      .mockResolvedValueOnce({ id: 1, title: 'New title', album_count: 1 })
      .mockResolvedValueOnce({ ...detail, title: 'New title' })
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.get('h1').text()).toBe('New title')
    expect(wrapper.text()).toContain('Shared home')
    expect(request.mock.calls[2][0]).toBe('songs/1/')
    wrapper.unmount()
  })

  it('refreshes artist detail after PATCH so discography remains visible', async () => {
    const detail = {
      id: 1,
      name: 'Old name',
      album_count: 1,
      albums: [
        {
          id: 2,
          title: 'A record',
          artist: 1,
          artist_name: 'Old name',
          release_year: 2024,
          track_count: 2,
        },
      ],
    }
    request.mockResolvedValueOnce(detail)
    const wrapper = mount(ArtistPage, { global: { stubs } })
    await flushPromises()
    await wrapper
      .findAll('button')
      .find((button) => button.text() === 'Edit artist')!
      .trigger('click')
    await wrapper.get('input').setValue('New name')
    request
      .mockResolvedValueOnce({ id: 1, name: 'New name', album_count: 1 })
      .mockResolvedValueOnce({ ...detail, name: 'New name' })
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.get('h1').text()).toBe('New name')
    expect(wrapper.text()).toContain('A record')
    expect(request.mock.calls[2][0]).toBe('artists/1/')
    wrapper.unmount()
  })
})
