<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, messageOf } from '../api'
import type { SongDetail } from '../types'
import AsyncState from '../components/AsyncState.vue'
import FormDialog from '../components/FormDialog.vue'
const route = useRoute()
const router = useRouter()
const song = ref<SongDetail>()
const pending = ref(true)
const error = ref('')
const mode = ref<'edit' | 'delete' | null>(null)
const title = ref('')
const saving = ref(false)
const saveError = ref('')
async function load() {
  pending.value = true
  error.value = ''
  try {
    song.value = await api<SongDetail>(`songs/${route.params.id}/`)
  } catch (reason) {
    error.value = messageOf(reason)
  } finally {
    pending.value = false
  }
}
void load()
function edit(value: 'edit' | 'delete') {
  title.value = song.value?.title || ''
  saveError.value = ''
  mode.value = value
}
async function save() {
  saving.value = true
  saveError.value = ''
  try {
    if (mode.value === 'delete') {
      await api(`songs/${route.params.id}/`, { method: 'DELETE' })
      mode.value = null
      await router.push('/songs')
    } else {
      await api(`songs/${route.params.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ title: title.value.trim() }),
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
</script>

<template>
  <RouterLink class="back-link" to="/songs">← All songs</RouterLink>
  <AsyncState :pending="pending" :error="error" @retry="load" />
  <template v-if="song && !pending && !error">
    <section class="entity-hero">
      <div class="song-art" aria-hidden="true"><span>♪</span></div>
      <div>
        <p class="eyebrow">SONG / #{{ song.id }}</p>
        <h1>{{ song.title }}</h1>
        <p class="muted">
          One song, {{ song.album_count }}
          {{ song.album_count === 1 ? 'album appearance' : 'album appearances' }}.
        </p>
        <div class="action-row">
          <button class="button secondary small" @click="edit('edit')">Edit song</button
          ><button class="text-button danger-text" @click="edit('delete')">Delete song</button>
        </div>
      </div>
    </section>
    <div class="section-heading">
      <div>
        <p class="eyebrow">SAME SONG. DIFFERENT CONTEXT.</p>
        <h2>
          Appears on <span class="count-badge">{{ song.album_count }}</span>
        </h2>
      </div>
    </div>
    <div v-if="song.appears_on.length" class="appearance-list">
      <RouterLink
        v-for="item in song.appears_on"
        :key="item.album"
        class="appearance-row"
        :to="`/albums/${item.album}`"
        ><span class="mini-record" aria-hidden="true">◎</span>
        <div>
          <h3>{{ item.album_title }}</h3>
          <p>{{ item.artist_name }}</p>
        </div>
        <span class="track-tag">Track {{ String(item.track_number).padStart(2, '0') }}</span
        ><span aria-hidden="true">↗</span></RouterLink
      >
    </div>
    <AsyncState
      v-else
      empty
      title="Ready for its first album"
      description="Open an album and add this existing song to its tracklist."
      ><RouterLink class="button secondary" to="/albums">Browse albums →</RouterLink></AsyncState
    >
    <p v-if="song.appears_on.length > 1" class="field-hint relation-note">
      Every appearance points to this same song. Its track number belongs to the album, so it can be
      different each time.
    </p>
    <FormDialog
      :open="!!mode"
      :title="mode === 'delete' ? 'Delete song?' : 'Edit song'"
      :submit-label="mode === 'delete' ? 'Delete song' : 'Save changes'"
      :danger="mode === 'delete'"
      :pending="saving"
      :error="saveError"
      @close="mode = null"
      @submit="save"
      ><p v-if="mode === 'delete'">
        Delete <strong>{{ song.title }}</strong> from the catalog? This cannot be undone. Remove it
        from all album tracklists first.
      </p>
      <template v-else
        ><label class="field"
          >Song title<input v-model="title" required maxlength="200" autofocus
        /></label>
        <p class="field-hint">This changes the title everywhere this song appears.</p></template
      ></FormDialog
    >
  </template>
</template>
