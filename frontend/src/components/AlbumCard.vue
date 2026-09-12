<script setup lang="ts">
import type { Album } from '../types'
import RecordCover from './RecordCover.vue'
defineProps<{ album: Album }>()
</script>

<template>
  <RouterLink :to="`/albums/${album.id}`" class="album-card">
    <RecordCover
      :id="album.id"
      :title="album.title"
      :artist="album.artist_name"
      :year="album.release_year"
    />
    <div class="album-card-meta">
      <div>
        <h3>{{ album.title }}</h3>
        <p>{{ album.artist_name }}</p>
      </div>
      <span class="card-arrow" aria-hidden="true">↗</span>
    </div>
    <div class="album-card-foot">
      <span>{{ album.release_year }}</span
      ><span>{{ album.track_count }} {{ album.track_count === 1 ? 'track' : 'tracks' }}</span>
    </div>
  </RouterLink>
</template>
