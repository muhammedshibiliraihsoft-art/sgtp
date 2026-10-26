import type { KeyboardEvent } from 'react'

const GRID_ITEM_SELECTOR = '[data-arrow-grid-item]:not(:disabled)'

export function handleArrowKeyGrid(event: KeyboardEvent<HTMLElement>) {
  if (!['ArrowDown', 'ArrowUp', 'ArrowLeft', 'ArrowRight'].includes(event.key)) return
  const current = event.target instanceof HTMLElement
    ? event.target.closest<HTMLElement>(GRID_ITEM_SELECTOR)
    : null
  const grid = current?.closest<HTMLElement>('[data-arrow-key-grid]')
  if (!current || !grid) return

  const items = [...grid.querySelectorAll<HTMLElement>(GRID_ITEM_SELECTOR)]
  const origin = current.getBoundingClientRect()
  const centerX = origin.left + origin.width / 2
  const centerY = origin.top + origin.height / 2
  const candidates = items.flatMap(item => {
    if (item === current) return []
    const rect = item.getBoundingClientRect()
    const x = rect.left + rect.width / 2
    const y = rect.top + rect.height / 2
    const primary = event.key === 'ArrowRight' ? x - centerX
      : event.key === 'ArrowLeft' ? centerX - x
        : event.key === 'ArrowDown' ? y - centerY : centerY - y
    if (primary <= 0) return []
    const cross = event.key === 'ArrowRight' || event.key === 'ArrowLeft'
      ? Math.abs(y - centerY)
      : Math.abs(x - centerX)
    return [{ item, score: primary + cross * 2 }]
  }).sort((a, b) => a.score - b.score)

  if (candidates[0]) {
    event.preventDefault()
    event.stopPropagation()
    candidates[0].item.focus()
  }
}

export function handleArrowKeyTabs(event: KeyboardEvent<HTMLElement>) {
  const backwards = event.key === 'ArrowLeft'
  if (!backwards && event.key !== 'ArrowRight' && event.key !== 'Home' && event.key !== 'End') return
  const tab = event.target instanceof HTMLElement ? event.target.closest<HTMLElement>('[role="tab"]') : null
  const list = tab?.closest<HTMLElement>('[role="tablist"]')
  if (!tab || !list) return
  const tabs = [...list.querySelectorAll<HTMLElement>('[role="tab"]:not(:disabled)')]
  if (!tabs.length) return
  const current = tabs.indexOf(tab)
  const next = event.key === 'Home' ? 0
    : event.key === 'End' ? tabs.length - 1
      : (current + (backwards ? -1 : 1) + tabs.length) % tabs.length
  event.preventDefault()
  tabs[next].focus()
  tabs[next].click()
}
