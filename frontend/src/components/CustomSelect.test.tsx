import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { CustomSelect } from './CustomSelect'

describe('CustomSelect keyboard interaction', () => {
  afterEach(cleanup)

  it('opens with ArrowDown, navigates options, and selects with Enter', () => {
    const onChange = vi.fn()
    render(<CustomSelect ariaLabel="Garment family" value="shirt" options={[
      { value: 'abaya', label: 'Abaya' },
      { value: 'shirt', label: "Men’s Shirt" },
      { value: 'dress', label: 'Long Dress' },
    ]} onChange={onChange} />)

    const trigger = screen.getByRole('button', { name: 'Garment family' })
    trigger.focus()
    fireEvent.keyDown(trigger, { key: 'ArrowDown' })
    expect(screen.getByRole('option', { name: "Men’s Shirt" })).toHaveFocus()
    fireEvent.keyDown(screen.getByRole('option', { name: "Men’s Shirt" }), { key: 'ArrowDown' })
    const longDress = screen.getByRole('option', { name: 'Long Dress' })
    expect(longDress).toHaveFocus()
    // A native button's Enter key activation is dispatched as click by the browser.
    fireEvent.click(longDress)

    expect(onChange).toHaveBeenCalledWith('dress')
    expect(trigger).toHaveFocus()
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })

  it('closes with Escape and returns focus to the trigger', () => {
    render(<CustomSelect ariaLabel="Garment family" value="shirt" options={[
      { value: 'shirt', label: "Men’s Shirt" }, { value: 'dress', label: 'Long Dress' },
    ]} onChange={vi.fn()} />)
    const trigger = screen.getByRole('button', { name: 'Garment family' })
    fireEvent.keyDown(trigger, { key: 'ArrowDown' })
    fireEvent.keyDown(screen.getByRole('option', { name: "Men’s Shirt" }), { key: 'Escape' })
    expect(trigger).toHaveFocus()
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })
})
