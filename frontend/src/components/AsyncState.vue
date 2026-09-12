<script setup lang="ts">
defineProps<{
  pending?: boolean
  error?: string
  empty?: boolean
  title?: string
  description?: string
}>()
defineEmits<{ retry: [] }>()
</script>

<template>
  <div v-if="pending" class="state-panel" role="status">
    <span class="spinner"></span>
    <p>Loading your collection…</p>
  </div>
  <div v-else-if="error" class="state-panel" role="alert">
    <h2>We couldn’t load this.</h2>
    <p>{{ error }}</p>
    <button class="button secondary" @click="$emit('retry')">Try again</button>
  </div>
  <div v-else-if="empty" class="state-panel">
    <span class="empty-record" aria-hidden="true">◎</span>
    <h2>{{ title || 'Nothing here yet' }}</h2>
    <p>{{ description || 'Your collection starts with the first addition.' }}</p>
    <slot />
  </div>
</template>
