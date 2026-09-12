<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, messageOf } from '../api'
import { useCatalogList } from '../composables/useCatalogList'
import type { Song } from '../types'
import AsyncState from '../components/AsyncState.vue'
import FormDialog from '../components/FormDialog.vue'
import PaginationNav from '../components/PaginationNav.vue'
const router = useRouter()
const { rows, count, page, search, pending, error, reload } = useCatalogList<Song>('songs')
const open = ref(false)
const title = ref('')
const saving = ref(false)
const saveError = ref('')
function create() {
  title.value = ''
  saveError.value = ''
  open.value = true
}
async function save() {
  saving.value = true
  saveError.value = ''
  try {
    const song = await api<Song>('songs/', {
      method: 'POST',
      body: JSON.stringify({ title: title.value.trim() }),
    })
    open.value = false
    await router.push(`/songs/${song.id}`)
  } catch (reason) {
    saveError.value = messageOf(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="page-intro">
    <p class="eyebrow">THE THREADS THAT CONNECT ALBUMS</p>
    <div class="section-heading">
      <div>
        <h1>Songs<span class="accent">.</span></h1>
        <p class="muted">One recording, wherever it belongs.</p>
      </div>
      <button class="button" @click="create">＋ Add song</button>
    </div>
  </section>
  <label class="search-field standalone-search"
    ><span class="sr-only">Search songs</span><span aria-hidden="true">⌕</span
    ><input v-model="search" type="search" placeholder="Find a song…"
  /></label>
  <div class="list-caption">
    <span>{{ count }} {{ count === 1 ? 'song' : 'songs' }}</span
    ><span>SONG / ALBUM APPEARANCES</span>
  </div>
  <AsyncState
    :pending="pending"
    :error="error"
    :empty="!rows.length"
    :title="search ? 'No songs found' : 'A collection starts with a song'"
    :description="
      search ? 'Try another title.' : 'Add a song here, or create one while editing an album.'
    "
    @retry="reload"
  />
  <div v-if="!pending && !error && rows.length" class="song-list">
    <RouterLink v-for="item in rows" :key="item.id" :to="`/songs/${item.id}`" class="song-row"
      ><span class="song-symbol" aria-hidden="true">♪</span>
      <div>
        <h2>{{ item.title }}</h2>
        <span class="muted small-text">Song #{{ item.id }}</span>
      </div>
      <span class="appearance-tag" :class="{ shared: item.album_count > 1 }"
        >{{ item.album_count > 1 ? '↔ ' : '' }}{{ item.album_count }}
        {{ item.album_count === 1 ? 'album' : 'albums' }}</span
      ><span aria-hidden="true">↗</span></RouterLink
    >
  </div>
  <PaginationNav v-if="!pending && !error" v-model:page="page" :count="count" />
  <FormDialog
    :open="open"
    title="Add a song"
    submit-label="Create song"
    :pending="saving"
    :error="saveError"
    @close="open = false"
    @submit="save"
    ><label class="field"
      >Song title<input v-model="title" required maxlength="200" autofocus autocomplete="off"
    /></label>
    <p class="field-hint">
      This creates one reusable song. Add it to any album from the album’s tracklist.
    </p></FormDialog
  >
</template>
