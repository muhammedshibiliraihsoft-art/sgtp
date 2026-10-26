import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { handleArrowKeyGrid, handleArrowKeyTabs } from './useArrowKeyGrid'

function rect(left: number, top: number) {
  return { x: left, y: top, left, top, right: left + 100, bottom: top + 50, width: 100, height: 50, toJSON: () => ({}) } as DOMRect
}

describe('keyboard navigation patterns', () => {
  it('moves through visible grid cards by their on-screen direction', () => {
    render(<div data-arrow-key-grid onKeyDown={handleArrowKeyGrid}>
      <button data-arrow-grid-item>First</button><button data-arrow-grid-item>Second</button>
      <button data-arrow-grid-item>Third</button>
    </div>)
    const first = screen.getByRole('button', { name: 'First' })
    const second = screen.getByRole('button', { name: 'Second' })
    const third = screen.getByRole('button', { name: 'Third' })
    first.getBoundingClientRect = () => rect(0, 0)
    second.getBoundingClientRect = () => rect(120, 0)
    third.getBoundingClientRect = () => rect(0, 80)

    first.focus()
    fireEvent.keyDown(first, { key: 'ArrowRight' })
    expect(second).toHaveFocus()
    fireEvent.keyDown(second, { key: 'ArrowDown' })
    expect(third).toHaveFocus()
  })

  it('roves tab focus and activates the tab with arrow keys', () => {
    const onActivate = vi.fn()
    render(<div role="tablist" onKeyDown={handleArrowKeyTabs}>
      <button role="tab" onClick={onActivate}>Families</button>
      <button role="tab" onClick={onActivate}>Variants</button>
      <button role="tab" onClick={onActivate}>Styles</button>
    </div>)
    const families = screen.getByRole('tab', { name: 'Families' })
    const variants = screen.getByRole('tab', { name: 'Variants' })
    families.focus()
    fireEvent.keyDown(families, { key: 'ArrowRight' })
    expect(variants).toHaveFocus()
    expect(onActivate).toHaveBeenCalledOnce()
  })
})
