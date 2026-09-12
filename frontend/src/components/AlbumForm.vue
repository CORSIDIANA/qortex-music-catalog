<script setup lang="ts">
import { ref, watch } from 'vue'
import { api, messageOf } from '../api'
import type { Album, AlbumDetail, Artist, Page } from '../types'
import FormDialog from './FormDialog.vue'
const props = defineProps<{ open: boolean; album?: Album; initialArtist?: number }>()
const emit = defineEmits<{ close: []; saved: [album: AlbumDetail] }>()
const title = ref('')
const artist = ref<number | ''>('')
const year = ref(new Date().getFullYear())
const artists = ref<Artist[]>([])
const pending = ref(false)
const error = ref('')
const loadingArtists = ref(false)
watch(
  () => props.open,
  async (open) => {
    if (!open) return
    title.value = props.album?.title || ''
    artist.value = props.album?.artist || props.initialArtist || ''
    year.value = props.album?.release_year || new Date().getFullYear()
    error.value = ''
    artists.value = []
    loadingArtists.value = true
    try {
      let page = 1
      let result: Page<Artist>
      do {
        result = await api<Page<Artist>>(`artists/?page=${page++}`)
        artists.value.push(...result.results)
      } while (result.next)
    } catch (reason) {
      error.value = messageOf(reason)
    } finally {
      loadingArtists.value = false
    }
  },
)
async function save() {
  pending.value = true
  error.value = ''
  try {
    const result = await api<AlbumDetail>(props.album ? `albums/${props.album.id}/` : 'albums/', {
      method: props.album ? 'PATCH' : 'POST',
      body: JSON.stringify({
        title: title.value.trim(),
        artist: artist.value,
        release_year: year.value,
      }),
    })
    emit('saved', result)
  } catch (reason) {
    error.value = messageOf(reason)
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <FormDialog
    :open="open"
    :title="album ? 'Edit album' : 'Add an album'"
    :pending="pending || loadingArtists"
    :error="error"
    :submit-label="album ? 'Save changes' : 'Create album'"
    @close="$emit('close')"
    @submit="save"
  >
    <label class="field"
      >Album title<input v-model="title" required maxlength="200" autocomplete="off" autofocus
    /></label>
    <label class="field"
      >Artist<select v-model="artist" required>
        <option disabled value="">
          {{ loadingArtists ? 'Loading artists…' : 'Choose an artist' }}
        </option>
        <option v-for="item in artists" :key="item.id" :value="item.id">{{ item.name }}</option>
      </select></label
    >
    <p v-if="!loadingArtists && !artists.length" class="field-hint">
      Create an artist on the Artists page before adding an album.
    </p>
    <label class="field"
      >Release year<input v-model.number="year" type="number" required min="1" max="9999"
    /></label>
  </FormDialog>
</template>
