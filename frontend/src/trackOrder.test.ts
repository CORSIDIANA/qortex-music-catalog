import { describe, expect, it } from 'vitest'
import { moveItem, orderChanged } from './trackOrder'

describe('track order drafts', () => {
  const saved = [
    { id: 11, song: 2 },
    { id: 12, song: 1 },
    { id: 13, song: 7 },
  ]
  it('moves placements while keeping song identities and the saved order intact', () => {
    const draft = moveItem(saved, 0, 2)
    expect(draft.map((track) => track.id)).toEqual([12, 13, 11])
    expect(draft.map((track) => track.song)).toEqual([1, 7, 2])
    expect(saved.map((track) => track.id)).toEqual([11, 12, 13])
    expect(orderChanged(draft, saved)).toBe(true)
  })
  it('moving back cancels the draft without a server write', () => {
    expect(orderChanged(moveItem(moveItem(saved, 0, 2), 2, 0), saved)).toBe(false)
  })
  it('ignores out-of-bounds keyboard moves', () => {
    expect(moveItem(saved, 0, -1)).toEqual(saved)
    expect(moveItem(saved, 2, 3)).toEqual(saved)
    expect(moveItem(saved, -1, 1)).toEqual(saved)
  })
  it('detects placement addition and removal as changes', () => {
    expect(orderChanged([...saved, { id: 14, song: 8 }], saved)).toBe(true)
    expect(orderChanged(saved.slice(1), saved)).toBe(true)
  })
})
