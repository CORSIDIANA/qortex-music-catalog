export function moveItem<T>(items: readonly T[], from: number, to: number): T[] {
  const next = [...items]
  if (from < 0 || to < 0 || from >= next.length || to >= next.length || from === to) return next
  const [item] = next.splice(from, 1)
  next.splice(to, 0, item)
  return next
}

export function orderChanged(
  current: readonly { id: number }[],
  saved: readonly { id: number }[],
): boolean {
  return (
    current.length !== saved.length || current.some((track, index) => track.id !== saved[index]?.id)
  )
}
