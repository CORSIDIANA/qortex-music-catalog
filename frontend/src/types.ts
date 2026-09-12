export interface Page<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
export interface Artist {
  id: number
  name: string
  album_count: number
}
export interface Album {
  id: number
  title: string
  artist: number
  artist_name: string
  release_year: number
  track_count: number
  revision: number
}
export interface Song {
  id: number
  title: string
  album_count: number
}
export interface Track {
  id: number
  song: number
  song_title: string
  track_number: number
}
export interface AlbumDetail extends Album {
  tracks: Track[]
}
export interface ArtistDetail extends Artist {
  albums: Album[]
}
export interface Appearance {
  album: number
  album_title: string
  artist_name: string
  track_number: number
}
export interface SongDetail extends Song {
  appears_on: Appearance[]
}
