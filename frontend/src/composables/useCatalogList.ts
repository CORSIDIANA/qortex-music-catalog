import { onBeforeUnmount, ref, watch, type Ref } from 'vue'
import { api, messageOf } from '../api'
import type { Page } from '../types'

export function useCatalogList<T>(resource: string, filter?: Ref<string>) {
  const rows = ref<T[]>([]) as Ref<T[]>
  const count = ref(0)
  const page = ref(1)
  const search = ref('')
  const pending = ref(true)
  const error = ref('')
  let controller: AbortController | undefined
  let timer: ReturnType<typeof setTimeout> | undefined

  async function reload() {
    controller?.abort()
    const current = new AbortController()
    controller = current
    pending.value = true
    error.value = ''
    const params = new URLSearchParams({ page: String(page.value), search: search.value })
    if (filter?.value) params.set('artist', filter.value)
    try {
      const result = await api<Page<T>>(`${resource}/?${params}`, { signal: current.signal })
      rows.value = result.results
      count.value = result.count
    } catch (reason) {
      if (!current.signal.aborted) error.value = messageOf(reason)
    } finally {
      if (!current.signal.aborted) pending.value = false
    }
  }

  watch([search, ...(filter ? [filter] : [])], () => {
    clearTimeout(timer)
    controller?.abort()
    pending.value = true
    timer = setTimeout(() => {
      if (page.value !== 1) page.value = 1
      else void reload()
    }, 250)
  })
  watch(page, () => void reload())
  void reload()
  onBeforeUnmount(() => {
    controller?.abort()
    clearTimeout(timer)
  })
  return { rows, count, page, search, pending, error, reload }
}
