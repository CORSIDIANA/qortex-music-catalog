<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ page: number; count: number }>()
defineEmits<{ 'update:page': [page: number] }>()
const pages = computed(() => Math.ceil(props.count / 24))
</script>

<template>
  <nav v-if="pages > 1" class="pagination" aria-label="Pagination">
    <button
      class="button secondary small"
      :disabled="page === 1"
      @click="$emit('update:page', page - 1)"
    >
      ← Previous
    </button>
    <span>Page {{ page }} of {{ pages }}</span>
    <button
      class="button secondary small"
      :disabled="page >= pages"
      @click="$emit('update:page', page + 1)"
    >
      Next →
    </button>
  </nav>
</template>
