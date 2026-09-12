<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { api, messageOf } from '../api'
import type { Page, Song } from '../types'
defineProps<{ placedSongs: number[]; busy: boolean }>()
defineEmits<{ add: [payload: { song: number } | { title: string }]; close: [] }>()
const mode = ref<'existing' | 'new'>('existing')
const search = ref('')
const title = ref('')
const results = ref<Song[]>([])
const page = ref(1)
const hasNext = ref(false)
const pending = ref(false)
const error = ref('')
const retryAppend = ref(false)
let controller: AbortController | undefined
let timer: ReturnType<typeof setTimeout> | undefined
async function load(append = false) {
  controller?.abort()
  const current = new AbortController()
  controller = current
  pending.value = true
  error.value = ''
  retryAppend.value = append
  const requestedPage = append ? page.value + 1 : 1
  try {
    const result = await api<Page<Song>>(
      `songs/?${new URLSearchParams({ search: search.value, page: String(requestedPage) })}`,
      { signal: current.signal },
    )
    results.value = append ? [...results.value, ...result.results] : result.results
    page.value = requestedPage
    hasNext.value = !!result.next
  } catch (reason) {
    if (!current.signal.aborted) error.value = messageOf(reason)
  } finally {
    if (!current.signal.aborted) pending.value = false
  }
}
watch(search, () => {
  clearTimeout(timer)
  controller?.abort()
  pending.value = true
  page.value = 1
  timer = setTimeout(() => void load(), 250)
})
void load()
function more() {
  void load(true)
}
onBeforeUnmount(() => {
  clearTimeout(timer)
  controller?.abort()
})
</script>

<template>
  <section class="add-song-panel" aria-labelledby="add-song-heading">
    <div class="section-heading compact">
      <h3 id="add-song-heading">Add to this album</h3>
      <button
        class="icon-button"
        aria-label="Close add song"
        :disabled="busy"
        @click="$emit('close')"
      >
        ×
      </button>
    </div>
    <div class="segmented-control" aria-label="Song source">
      <button
        :class="{ selected: mode === 'existing' }"
        :aria-pressed="mode === 'existing'"
        :disabled="busy"
        @click="mode = 'existing'"
      >
        Existing song</button
      ><button
        :class="{ selected: mode === 'new' }"
        :aria-pressed="mode === 'new'"
        :disabled="busy"
        @click="mode = 'new'"
      >
        Create a song
      </button>
    </div>
    <template v-if="mode === 'existing'">
      <label class="field"
        >Find an existing song<input
          v-model="search"
          type="search"
          placeholder="Search the song catalog…"
          :disabled="busy"
          autocomplete="off"
      /></label>
      <p class="field-hint">
        Reuse the same song across albums. Its position is unique to each album.
      </p>
      <p v-if="pending" class="field-hint" role="status">Searching…</p>
      <p v-if="error" class="error-message" role="alert">
        {{ error }} <button class="text-button" @click="load(retryAppend)">Retry</button>
      </p>
      <ul v-if="!pending && !error" class="song-suggestions">
        <li v-for="song in results" :key="song.id">
          <button
            :disabled="busy || placedSongs.includes(song.id)"
            @click="$emit('add', { song: song.id })"
          >
            <span
              ><strong>{{ song.title }}</strong
              ><small
                >Song #{{ song.id }} · {{ song.album_count }}
                {{ song.album_count === 1 ? 'album' : 'albums' }}</small
              ></span
            ><span>{{ placedSongs.includes(song.id) ? 'Already on this album' : '+ Add' }}</span>
          </button>
        </li>
      </ul>
      <p v-if="!pending && !error && !results.length" class="field-hint">
        No matching songs. Use “Create a song” to add a new recording.
      </p>
      <button
        v-if="hasNext && !pending && !error"
        class="text-button"
        :disabled="busy"
        @click="more"
      >
        Show more songs
      </button>
    </template>
    <form v-else @submit.prevent="$emit('add', { title: title.trim() })">
      <label class="field"
        >New song title<input
          v-model="title"
          required
          maxlength="200"
          :disabled="busy"
          autocomplete="off"
          placeholder="Give this song a name"
      /></label>
      <p class="field-hint">
        Creates a reusable song and adds it here in one step. For a song already in your catalog,
        use Existing song.
      </p>
      <button class="button small" :disabled="busy">
        {{ busy ? 'Adding…' : 'Create & add song' }}
      </button>
    </form>
  </section>
</template>
