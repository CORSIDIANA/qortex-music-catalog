<script setup lang="ts">
defineProps<{ id: number; title: string; artist: string; year?: number }>()
</script>

<template>
  <div class="record-cover" :class="`cover-${id % 6}`" aria-hidden="true">
    <div class="cover-top">
      <span>{{ artist }}</span
      ><span>{{ year }}</span>
    </div>
    <div class="cover-art">
      <div class="cover-orbit"></div>
      <div class="vinyl"><span></span></div>
    </div>
    <div class="cover-bottom">
      <strong>{{ title }}</strong
      ><span>MC—{{ String(id).padStart(3, '0') }}</span>
    </div>
  </div>
</template>
