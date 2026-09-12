<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, messageOf } from '../api'
import { useCatalogList } from '../composables/useCatalogList'
import type { Artist } from '../types'
import AsyncState from '../components/AsyncState.vue'
import FormDialog from '../components/FormDialog.vue'
import PaginationNav from '../components/PaginationNav.vue'
const router = useRouter()
const { rows, count, page, search, pending, error, reload } = useCatalogList<Artist>('artists')
const open = ref(false)
const name = ref('')
const saving = ref(false)
const saveError = ref('')
function create() {
  name.value = ''
  saveError.value = ''
  open.value = true
}
async function save() {
  saving.value = true
  saveError.value = ''
  try {
    const artist = await api<Artist>('artists/', {
      method: 'POST',
      body: JSON.stringify({ name: name.value.trim() }),
    })
    open.value = false
    await router.push(`/artists/${artist.id}`)
  } catch (reason) {
    saveError.value = messageOf(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="page-intro">
    <p class="eyebrow">THE PEOPLE BEHIND THE RECORDS</p>
    <div class="section-heading">
      <div>
        <h1>Artists<span class="accent">.</span></h1>
        <p class="muted">Every collection begins with a voice.</p>
      </div>
      <button class="button" @click="create">＋ Add artist</button>
    </div>
  </section>
  <label class="search-field standalone-search"
    ><span class="sr-only">Search artists</span><span aria-hidden="true">⌕</span
    ><input v-model="search" type="search" placeholder="Find an artist…"
  /></label>
  <div class="list-caption">
    <span>{{ count }} {{ count === 1 ? 'artist' : 'artists' }}</span
    ><span>YOUR COLLECTION / A—Z</span>
  </div>
  <AsyncState
    :pending="pending"
    :error="error"
    :empty="!rows.length"
    :title="search ? 'No artists found' : 'Meet your first artist'"
    :description="
      search ? 'Try another name.' : 'Add an artist to start building your album collection.'
    "
    @retry="reload"
  />
  <div v-if="!pending && !error && rows.length" class="artist-grid">
    <RouterLink v-for="item in rows" :key="item.id" :to="`/artists/${item.id}`" class="artist-card"
      ><span class="artist-avatar" :class="`avatar-${item.id % 4}`" aria-hidden="true">{{
        item.name.slice(0, 1).toUpperCase()
      }}</span>
      <div>
        <h2>{{ item.name }}</h2>
        <p>{{ item.album_count }} {{ item.album_count === 1 ? 'album' : 'albums' }}</p>
      </div>
      <span class="card-arrow" aria-hidden="true">↗</span></RouterLink
    >
  </div>
  <PaginationNav v-if="!pending && !error" v-model:page="page" :count="count" />
  <FormDialog
    :open="open"
    title="Add an artist"
    submit-label="Create artist"
    :pending="saving"
    :error="saveError"
    @close="open = false"
    @submit="save"
    ><label class="field"
      >Artist name<input
        v-model="name"
        required
        maxlength="200"
        autofocus
        autocomplete="off" /></label
  ></FormDialog>
</template>
