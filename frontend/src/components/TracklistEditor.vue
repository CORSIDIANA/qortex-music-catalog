<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { api, ApiError, messageOf } from '../api'
import { moveItem, orderChanged } from '../trackOrder'
import type { AlbumDetail, Track } from '../types'
import AddSongPanel from './AddSongPanel.vue'
import FormDialog from './FormDialog.vue'
const props = defineProps<{ album: AlbumDetail }>()
const emit = defineEmits<{
  updated: [album: AlbumDetail]
  dirty: [dirty: boolean]
  busy: [busy: boolean]
}>()
const tracks = ref<Track[]>([])
const busy = ref(false)
const error = ref('')
const notice = ref('')
const stale = ref(false)
const needsReload = ref(false)
const locked = computed(() => busy.value || needsReload.value)
const adding = ref(false)
const removing = ref<Track | null>(null)
const draggedId = ref<number | null>(null)
const dropTarget = ref<number | null>(null)
const dirty = computed(() => orderChanged(tracks.value, props.album.tracks))
const hasNumberGaps = computed(() =>
  props.album.tracks.some((track, index) => track.track_number !== index + 1),
)
watch(
  () => props.album,
  (album) => {
    tracks.value = [...album.tracks]
    stale.value = false
  },
  { immediate: true },
)
watch(dirty, (value) => emit('dirty', value))
watch(locked, (value) => emit('busy', value))
function move(from: number, to: number) {
  if (locked.value) return
  tracks.value = moveItem(tracks.value, from, to)
  notice.value = 'Order changed locally. Save order to keep your changes.'
  if (!stale.value) error.value = ''
}
function dragStart(event: DragEvent, id: number) {
  if (locked.value) {
    event.preventDefault()
    return
  }
  draggedId.value = id
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(id))
  }
}
function drop(index: number) {
  const from = tracks.value.findIndex((track) => track.id === draggedId.value)
  if (from >= 0) move(from, index)
  draggedId.value = null
  dropTarget.value = null
}
function endDrag() {
  draggedId.value = null
  dropTarget.value = null
}
function confirmRemove(track: Track) {
  removing.value = track
  if (!stale.value) error.value = ''
}
function cancel() {
  tracks.value = [...props.album.tracks]
  if (!stale.value) error.value = ''
  notice.value = 'Draft discarded.'
}
async function save() {
  if (needsReload.value || stale.value) return
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    const album = await api<AlbumDetail>(`albums/${props.album.id}/tracks/reorder/`, {
      method: 'PUT',
      body: JSON.stringify({
        track_ids: tracks.value.map((track) => track.id),
        revision: props.album.revision,
      }),
    })
    stale.value = false
    emit('updated', album)
    notice.value = 'Track order saved.'
  } catch (reason) {
    stale.value = reason instanceof ApiError && reason.status === 409
    error.value = stale.value
      ? 'This tracklist changed in another session. Your draft is still here. Reload the latest version before reordering again.'
      : messageOf(reason)
  } finally {
    busy.value = false
  }
}
async function reload() {
  if (dirty.value && !window.confirm('Discard your draft and load the latest tracklist?')) return
  busy.value = true
  error.value = ''
  try {
    emit('updated', await api<AlbumDetail>(`albums/${props.album.id}/`))
    needsReload.value = false
    stale.value = false
    notice.value = 'Latest tracklist loaded.'
  } catch (reason) {
    error.value = messageOf(reason)
  } finally {
    busy.value = false
  }
}
async function add(payload: { song: number } | { title: string }) {
  if (needsReload.value) return
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    emit(
      'updated',
      await api<AlbumDetail>(`albums/${props.album.id}/tracks/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    )
    adding.value = false
    notice.value = 'Song added to this album.'
  } catch (reason) {
    error.value = messageOf(reason)
  } finally {
    busy.value = false
  }
}
async function remove() {
  if (!removing.value) return
  busy.value = true
  error.value = ''
  notice.value = ''
  try {
    await api(`albums/${props.album.id}/tracks/${removing.value.id}/`, { method: 'DELETE' })
    removing.value = null
    needsReload.value = true
    emit('updated', await api<AlbumDetail>(`albums/${props.album.id}/`))
    needsReload.value = false
    notice.value = 'Removed from this album. The song is still in your catalog.'
  } catch (reason) {
    error.value = needsReload.value
      ? `The song was removed, but the refreshed tracklist could not load. Reload before making more changes. ${messageOf(reason)}`
      : messageOf(reason)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="tracklist" aria-labelledby="tracklist-heading" :aria-busy="busy">
    <div class="section-heading">
      <div>
        <p class="eyebrow">EVERY SONG IN ITS PLACE</p>
        <h2 id="tracklist-heading">
          Tracklist <span class="count-badge">{{ tracks.length }}</span>
        </h2>
      </div>
      <button class="button secondary small" :disabled="locked || dirty" @click="adding = !adding">
        {{ adding ? 'Close' : '＋ Add song' }}
      </button>
    </div>
    <p class="tracklist-hint">
      Drag tracks to reorder, or use the arrow buttons. Save when it feels right.
    </p>
    <p v-if="hasNumberGaps && !dirty" class="field-hint">
      This tracklist has gaps in its numbering.
      <button class="text-button" :disabled="locked" @click="save">Renumber from 1</button>
    </p>
    <div v-if="dirty" class="draft-bar">
      <span
        ><strong>Unsaved order</strong
        ><small>Adding and removing songs resumes after you save or cancel.</small></span
      >
      <div class="action-row">
        <button class="button secondary small" :disabled="busy" @click="cancel">Cancel</button
        ><button class="button small" :disabled="busy || stale" @click="save">
          {{ busy ? 'Saving…' : 'Save order' }}
        </button>
      </div>
    </div>
    <div v-if="error" class="error-message" role="alert">
      {{ error }}
      <button v-if="stale" class="text-button" :disabled="busy" @click="reload">
        Reload latest
      </button>
    </div>
    <button v-if="needsReload" class="button secondary small" :disabled="busy" @click="reload">
      Reload latest tracklist
    </button>
    <p class="sr-only" role="status" aria-live="polite">{{ notice }}</p>
    <p v-if="notice && !dirty" class="success-message">{{ notice }}</p>
    <ol v-if="tracks.length" class="track-rows" aria-label="Album tracklist">
      <li
        v-for="(track, index) in tracks"
        :key="track.id"
        class="track-row"
        :class="{ dragging: draggedId === track.id, 'drop-target': dropTarget === index }"
        :draggable="!locked"
        @dragstart="dragStart($event, track.id)"
        @dragover.prevent="dropTarget = index"
        @drop.prevent="drop(index)"
        @dragend="endDrag"
      >
        <span class="drag-grip" aria-hidden="true">⠿</span
        ><span class="track-number">{{
          String(dirty ? index + 1 : track.track_number).padStart(2, '0')
        }}</span>
        <RouterLink class="track-title" :to="`/songs/${track.song}`"
          >{{ track.song_title }}<small>View song & appearances ↗</small></RouterLink
        >
        <div class="track-actions">
          <button
            class="icon-button"
            :disabled="locked || index === 0"
            :aria-label="`Move ${track.song_title} up`"
            @click="move(index, index - 1)"
          >
            ↑</button
          ><button
            class="icon-button"
            :disabled="locked || index === tracks.length - 1"
            :aria-label="`Move ${track.song_title} down`"
            @click="move(index, index + 1)"
          >
            ↓</button
          ><button
            class="icon-button remove-button"
            :disabled="locked || dirty"
            :aria-label="`Remove ${track.song_title} from album`"
            @click="confirmRemove(track)"
          >
            ×
          </button>
        </div>
      </li>
    </ol>
    <div v-else class="track-empty">
      <span aria-hidden="true">♪</span>
      <h3>The tracklist is yours to write.</h3>
      <p>Add a song from the catalog, or create something new.</p>
      <button v-if="!adding" class="button secondary small" @click="adding = true">
        ＋ Add the first song
      </button>
    </div>
    <AddSongPanel
      v-if="adding && !dirty"
      :placed-songs="tracks.map((track) => track.song)"
      :busy="locked"
      @add="add"
      @close="adding = false"
    />
    <FormDialog
      :open="!!removing"
      title="Remove from this album?"
      submit-label="Remove song"
      :pending="busy"
      :error="removing ? error : ''"
      @close="removing = null"
      @submit="remove"
      ><p>
        <strong>{{ removing?.song_title }}</strong> will leave this tracklist. The song and its
        appearances on other albums will stay in your catalog.
      </p></FormDialog
    >
  </section>
</template>
