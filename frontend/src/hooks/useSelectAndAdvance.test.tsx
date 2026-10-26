import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useSelectAndAdvance } from './useSelectAndAdvance'

function MultiSelectHarness({
  onCommit = vi.fn(),
  onAdvance = vi.fn(),
}: {
  onCommit?: (items: string[]) => void
  onAdvance?: () => void
}) {
  const [selectedItems, setSelectedItems] = useState<string[]>([])
  const { getItemProps } = useSelectAndAdvance({
    selectionMode: 'MULTI',
    selectedItems,
    onChange: setSelectedItems,
    onCommit,
    onAdvance,
    scopeKey: 'group-a',
  })

  return <form>
    {['A', 'B', 'C'].map(item => {
      const props = getItemProps(item)
      return <label key={item} onPointerDown={props.onPointerDown}>
        <input type="checkbox" checked={selectedItems.includes(item)} onChange={props.onChange} onKeyDown={props.onKeyDown} />
        {item}
      </label>
    })}
    <input aria-label="Notes" />
  </form>
}

describe('useSelectAndAdvance', () => {
  afterEach(cleanup)

  it('selects on a single activation without advancing', () => {
    const onAdvance = vi.fn()
    render(<MultiSelectHarness onAdvance={onAdvance} />)

    fireEvent.click(screen.getByRole('checkbox', { name: 'A' }))

    expect(screen.getByRole('checkbox', { name: 'A' })).toBeChecked()
    expect(onAdvance).not.toHaveBeenCalled()
  })

  it.each(['mouse', 'touch'] as const)('preserves all selected items on a %s double activation and commits before advancing', pointerType => {
    const calls: string[] = []
    const onCommit = vi.fn((items: string[]) => calls.push(`commit:${items.join(',')}`))
    const onAdvance = vi.fn(() => calls.push('advance'))
    render(<MultiSelectHarness onCommit={onCommit} onAdvance={onAdvance} />)

    fireEvent.click(screen.getByRole('checkbox', { name: 'A' }))
    fireEvent.click(screen.getByRole('checkbox', { name: 'B' }))
    const card = screen.getByRole('checkbox', { name: 'C' }).closest('label')!
    fireEvent.pointerDown(card, { pointerType, button: 0, isPrimary: true })
    fireEvent.click(screen.getByRole('checkbox', { name: 'C' }))
    fireEvent.pointerDown(card, { pointerType, button: 0, isPrimary: true })

    expect(screen.getByRole('checkbox', { name: 'A' })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: 'B' })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: 'C' })).toBeChecked()
    expect(onCommit).toHaveBeenCalledExactlyOnceWith(['A', 'B', 'C'])
    expect(calls).toEqual(['commit:A,B,C', 'advance'])
    expect(onAdvance).toHaveBeenCalledTimes(1)

    fireEvent.pointerDown(card, { pointerType, button: 0, isPrimary: true })
    fireEvent.pointerDown(card, { pointerType, button: 0, isPrimary: true })
    expect(onAdvance).toHaveBeenCalledTimes(1)
  })

  it('selects with the first Enter and commits the full selection on the second Enter', () => {
    const onCommit = vi.fn()
    const onAdvance = vi.fn()
    render(<MultiSelectHarness onCommit={onCommit} onAdvance={onAdvance} />)

    fireEvent.click(screen.getByRole('checkbox', { name: 'A' }))
    fireEvent.click(screen.getByRole('checkbox', { name: 'B' }))
    const optionC = screen.getByRole('checkbox', { name: 'C' })
    fireEvent.keyDown(optionC, { key: 'Enter' })
    expect(optionC).toBeChecked()
    expect(onAdvance).not.toHaveBeenCalled()

    fireEvent.keyDown(optionC, { key: 'Enter' })
    expect(onCommit).toHaveBeenCalledExactlyOnceWith(['A', 'B', 'C'])
    expect(onAdvance).toHaveBeenCalledTimes(1)
  })

  it('does not intercept Enter from a text input or make Space advance', () => {
    const onAdvance = vi.fn()
    render(<MultiSelectHarness onAdvance={onAdvance} />)

    fireEvent.keyDown(screen.getByRole('textbox', { name: 'Notes' }), { key: 'Enter' })
    fireEvent.keyDown(screen.getByRole('checkbox', { name: 'A' }), { key: ' ' })

    expect(onAdvance).not.toHaveBeenCalled()
  })
})
