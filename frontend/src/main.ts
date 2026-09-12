import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import AlbumsPage from './pages/AlbumsPage.vue'
import AlbumPage from './pages/AlbumPage.vue'
import ArtistsPage from './pages/ArtistsPage.vue'
import ArtistPage from './pages/ArtistPage.vue'
import SongsPage from './pages/SongsPage.vue'
import SongPage from './pages/SongPage.vue'
import NotFoundPage from './pages/NotFoundPage.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/albums' },
    { path: '/albums', component: AlbumsPage },
    { path: '/albums/:id', component: AlbumPage },
    { path: '/artists', component: ArtistsPage },
    { path: '/artists/:id', component: ArtistPage },
    { path: '/songs', component: SongsPage },
    { path: '/songs/:id', component: SongPage },
    { path: '/:pathMatch(.*)*', component: NotFoundPage },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

createApp(App).use(router).mount('#app')
