<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, messageOf } from '../api'
import { useCatalogList } from '../composables/useCatalogList'
import type { Album, AlbumDetail, Artist, Page } from '../types'
import AlbumCard from '../components/AlbumCard.vue'
import AlbumForm from '../components/AlbumForm.vue'
import AsyncState from '../components/AsyncState.vue'
import PaginationNav from '../components/PaginationNav.vue'
const router = useRouter()
const artist = ref('')
const artists = ref<Artist[]>([])
const filterError = ref('')
const open = ref(false)
const { rows, count, page, search, pending, error, reload } = useCatalogList<Album>(
  'albums',
  artist,
)
async function loadArtists() {
  filterError.value = ''
  try {
    let nextPage = 1
    let result: Page<Artist>
    const all: Artist[] = []
    do {
      result = await api<Page<Artist>>(`artists/?page=${nextPage++}`)
      all.push(...result.results)
    } while (result.next)
    artists.value = all
  } catch (reason) {
    filterError.value = messageOf(reason)
  }
}
void loadArtists()
function created(album: AlbumDetail) {
  open.value = false
  void router.push(`/albums/${album.id}`)
}
</script>

<template>
  <section class="collection-hero">
    <div>
      <p class="eyebrow"><span></span> YOUR PERSONAL LINER NOTES</p>
      <h1>Every album.<br />A little <em>universe.</em></h1>
      <p class="hero-description">
        Give your records a home. Explore the artists,<br class="desktop-break" />
        collect the songs, and make every track count.
      </p>
    </div>
    <div class="hero-record" aria-hidden="true">
      <div class="hero-sleeve">
        <span>THE<br />COLLECTION</span><small>VOL. 01 / ALWAYS GROWING</small>
      </div>
      <div class="hero-vinyl">
        <span>MC<br /><small>SIDE A</small></span>
      </div>
      <span class="hero-sticker">KEEP<br />DISCOVERING</span>
    </div>
  </section>
  <section aria-labelledby="albums-title">
    <div class="section-heading">
      <div>
        <p class="eyebrow">ON THE SHELF</p>
        <h2 id="albums-title">
          Your albums <span class="count-badge">{{ count }}</span>
        </h2>
      </div>
      <button class="button" @click="open = true">
        <span aria-hidden="true">＋</span> Add album
      </button>
    </div>
    <div class="filter-bar">
      <label class="search-field"
        ><span class="sr-only">Search albums</span><span aria-hidden="true">⌕</span
        ><input v-model="search" type="search" placeholder="Search albums or artists…" /></label
      ><label class="filter-select"
        ><span class="sr-only">Filter by artist</span
        ><select v-model="artist">
          <option value="">All artists</option>
          <option v-for="item in artists" :key="item.id" :value="String(item.id)">
            {{ item.name }}
          </option>
        </select></label
      >
    </div>
    <p v-if="filterError" class="error-message" role="alert">
      Artist filters: {{ filterError }}
      <button class="text-button" @click="loadArtists">Retry</button>
    </p>
    <AsyncState
      :pending="pending"
      :error="error"
      :empty="!rows.length"
      :title="search || artist ? 'No albums found' : 'Your first album is waiting'"
      :description="
        search || artist
          ? 'Try another search or choose a different artist.'
          : 'Start with an artist, then add an album to the shelf.'
      "
      @retry="reload"
      ><RouterLink v-if="!search && !artist" class="button secondary" to="/artists"
        >Browse artists →</RouterLink
      ></AsyncState
    >
    <div v-if="!pending && !error && rows.length" class="album-grid">
      <AlbumCard v-for="album in rows" :key="album.id" :album="album" />
    </div>
    <PaginationNav v-if="!pending && !error" v-model:page="page" :count="count" />
  </section>
  <aside class="collection-note">
    <span aria-hidden="true">↔</span>
    <div>
      <strong>One song. More than one home.</strong>
      <p>A song can appear on different albums, with its own place on each tracklist.</p>
    </div>
    <RouterLink to="/songs">Explore songs <span aria-hidden="true">↗</span></RouterLink>
  </aside>
  <AlbumForm :open="open" @close="open = false" @saved="created" />
</template>
