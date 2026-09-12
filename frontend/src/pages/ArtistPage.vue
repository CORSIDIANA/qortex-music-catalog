<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, messageOf } from '../api'
import type { AlbumDetail, ArtistDetail } from '../types'
import AlbumCard from '../components/AlbumCard.vue'
import AlbumForm from '../components/AlbumForm.vue'
import AsyncState from '../components/AsyncState.vue'
import FormDialog from '../components/FormDialog.vue'
const route = useRoute()
const router = useRouter()
const artist = ref<ArtistDetail>()
const pending = ref(true)
const error = ref('')
const mode = ref<'edit' | 'delete' | null>(null)
const name = ref('')
const saving = ref(false)
const saveError = ref('')
const albumOpen = ref(false)
async function load() {
  pending.value = true
  error.value = ''
  try {
    artist.value = await api<ArtistDetail>(`artists/${route.params.id}/`)
  } catch (reason) {
    error.value = messageOf(reason)
  } finally {
    pending.value = false
  }
}
void load()
function edit(value: 'edit' | 'delete') {
  name.value = artist.value?.name || ''
  saveError.value = ''
  mode.value = value
}
async function save() {
  saving.value = true
  saveError.value = ''
  try {
    if (mode.value === 'delete') {
      await api(`artists/${route.params.id}/`, { method: 'DELETE' })
      mode.value = null
      await router.push('/artists')
    } else {
      await api(`artists/${route.params.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ name: name.value.trim() }),
      })
      mode.value = null
      await load()
    }
  } catch (reason) {
    saveError.value = messageOf(reason)
  } finally {
    saving.value = false
  }
}
function created(album: AlbumDetail) {
  albumOpen.value = false
  void router.push(`/albums/${album.id}`)
}
</script>

<template>
  <RouterLink class="back-link" to="/artists">← All artists</RouterLink>
  <AsyncState :pending="pending" :error="error" @retry="load" />
  <template v-if="artist && !pending && !error">
    <section class="entity-hero">
      <span
        class="artist-avatar large-avatar"
        :class="`avatar-${artist.id % 4}`"
        aria-hidden="true"
        >{{ artist.name.slice(0, 1).toUpperCase() }}</span
      >
      <div>
        <p class="eyebrow">ARTIST</p>
        <h1>{{ artist.name }}</h1>
        <p class="muted">
          {{ artist.album_count }} {{ artist.album_count === 1 ? 'album' : 'albums' }} in the
          collection
        </p>
        <div class="action-row">
          <button class="button secondary small" @click="edit('edit')">Edit artist</button
          ><button class="text-button danger-text" @click="edit('delete')">Delete artist</button>
        </div>
      </div>
    </section>
    <div class="section-heading">
      <h2>Discography</h2>
      <button class="button" @click="albumOpen = true">＋ Add album</button>
    </div>
    <div v-if="artist.albums.length" class="album-grid">
      <AlbumCard v-for="album in artist.albums" :key="album.id" :album="album" />
    </div>
    <AsyncState
      v-else
      empty
      title="The first release goes here"
      description="Add an album to this artist’s discography."
    />
    <AlbumForm
      :open="albumOpen"
      :initial-artist="artist.id"
      @close="albumOpen = false"
      @saved="created"
    />
    <FormDialog
      :open="!!mode"
      :title="mode === 'delete' ? 'Delete artist?' : 'Edit artist'"
      :submit-label="mode === 'delete' ? 'Delete artist' : 'Save changes'"
      :danger="mode === 'delete'"
      :pending="saving"
      :error="saveError"
      @close="mode = null"
      @submit="save"
      ><p v-if="mode === 'delete'">
        Delete <strong>{{ artist.name }}</strong
        >? This cannot be undone. An artist with albums cannot be deleted; move or remove their
        albums first.
      </p>
      <label v-else class="field"
        >Artist name<input v-model="name" required maxlength="200" autofocus /></label
    ></FormDialog>
  </template>
</template>
