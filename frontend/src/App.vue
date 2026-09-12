<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="header-inner">
      <RouterLink class="brand" to="/albums" aria-label="Music Catalog home">
        <span class="brand-record" aria-hidden="true"></span>
        <span>music<span class="brand-light">catalog</span><span class="brand-dot">.</span></span>
      </RouterLink>
      <nav aria-label="Main navigation">
        <RouterLink to="/albums">Albums</RouterLink>
        <RouterLink to="/artists">Artists</RouterLink>
        <RouterLink to="/songs">Songs</RouterLink>
      </nav>
      <span class="header-note"><i></i> A place for your collection</span>
    </div>
  </header>
  <main id="main" class="container" tabindex="-1"><RouterView :key="$route.path" /></main>
  <footer class="site-footer container">
    <span>Good music. Thoughtfully organized.</span>
    <span>Music Catalog <span aria-hidden="true">↗</span></span>
  </footer>
</template>
