<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { api, messageOf } from '../api'
import type { AlbumDetail } from '../types'
import RecordCover from '../components/RecordCover.vue'
import AlbumForm from '../components/AlbumForm.vue'
import AsyncState from '../components/AsyncState.vue'
import FormDialog from '../components/FormDialog.vue'
import TracklistEditor from '../components/TracklistEditor.vue'
const route = useRoute()
const router = useRouter()
const album = ref<AlbumDetail>()
const pending = ref(true)
const error = ref('')
const editing = ref(false)
const deleting = ref(false)
const saving = ref(false)
const saveError = ref('')
const dirty = ref(false)
const trackBusy = ref(false)
async function load() {
  pending.value = true
  error.value = ''
  try {
    album.value = await api<AlbumDetail>(`albums/${route.params.id}/`)
  } catch (reason) {
    error.value = messageOf(reason)
  } finally {
    pending.value = false
  }
}
void load()
function updated(value: AlbumDetail) {
  album.value = value
  editing.value = false
}
function confirmDelete() {
  deleting.value = true
  saveError.value = ''
}
async function remove() {
  saving.value = true
  saveError.value = ''
  try {
    await api(`albums/${route.params.id}/`, { method: 'DELETE' })
    deleting.value = false
    await router.push('/albums')
  } catch (reason) {
    saveError.value = messageOf(reason)
  } finally {
    saving.value = false
  }
}
onBeforeRouteLeave(
  () => !dirty.value || window.confirm('You have an unsaved track order. Discard it and leave?'),
)
function beforeUnload(event: BeforeUnloadEvent) {
  if (dirty.value) {
    event.preventDefault()
    event.returnValue = ''
  }
}
window.addEventListener('beforeunload', beforeUnload)
onBeforeUnmount(() => window.removeEventListener('beforeunload', beforeUnload))
</script>

<template>
  <RouterLink class="back-link" to="/albums">← Back to the collection</RouterLink>
  <AsyncState :pending="pending" :error="error" @retry="load" />
  <template v-if="album && !pending && !error">
    <section class="album-detail-hero">
      <RecordCover
        :id="album.id"
        :title="album.title"
        :artist="album.artist_name"
        :year="album.release_year"
      />
      <div class="album-detail-copy">
        <p class="eyebrow">ALBUM / {{ album.release_year }}</p>
        <h1>{{ album.title }}</h1>
        <RouterLink class="artist-link" :to="`/artists/${album.artist}`"
          >{{ album.artist_name }} <span aria-hidden="true">↗</span></RouterLink
        >
        <div class="detail-facts">
          <span>{{ album.release_year }}<small>RELEASED</small></span
          ><span
            >{{ album.track_count
            }}<small>{{ album.track_count === 1 ? 'TRACK' : 'TRACKS' }}</small></span
          >
        </div>
        <div class="action-row">
          <button
            class="button secondary small"
            :disabled="dirty || trackBusy"
            @click="editing = true"
          >
            Edit album</button
          ><button
            class="text-button danger-text"
            :disabled="dirty || trackBusy"
            @click="confirmDelete"
          >
            Delete album
          </button>
        </div>
        <p v-if="dirty" class="field-hint">
          Save or cancel your track order before editing the album.
        </p>
      </div>
    </section>
    <TracklistEditor
      :album="album"
      @updated="updated"
      @dirty="dirty = $event"
      @busy="trackBusy = $event"
    />
    <AlbumForm :open="editing" :album="album" @close="editing = false" @saved="updated" />
    <FormDialog
      :open="deleting"
      title="Delete this album?"
      submit-label="Delete album"
      danger
      :pending="saving"
      :error="saveError"
      @close="deleting = false"
      @submit="remove"
      ><p>
        Delete <strong>{{ album.title }}</strong> and its tracklist? This cannot be undone. Its
        songs remain in the catalog and on other albums.
      </p></FormDialog
    >
  </template>
</template>
