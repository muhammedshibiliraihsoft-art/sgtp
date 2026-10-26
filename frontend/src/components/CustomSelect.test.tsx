import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { CustomSelect, ResponsiveChoice } from './CustomSelect'

describe('responsive choice tiles', () => {
  afterEach(() => {
    cleanup()
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 1024 })
  })

  it.each([
    { count: 5, expectedButtons: 5, overflow: null },
    { count: 6, expectedButtons: 6, overflow: '+1 more' },
    { count: 8, expectedButtons: 6, overflow: '+3 more' },
  ])('uses the compact mobile family preview for $count choices', ({ count, expectedButtons, overflow }) => {
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 375 })
    const options = Array.from({ length: count }, (_, index) => ({ value: `family-${index + 1}`, label: `Family ${index + 1}` }))
    render(<ResponsiveChoice ariaLabel="Garment family" value="family-1" options={options} onChange={vi.fn()} mobilePreviewLimit={5} />)

    const choiceGrid = screen.getByRole('group', { name: 'Garment family' })
    expect(choiceGrid.querySelector('.responsive-choice-grid')).toHaveClass('has-mobile-preview')
    expect(within(choiceGrid).getAllByRole('button')).toHaveLength(expectedButtons)
    if (overflow) expect(within(choiceGrid).getByRole('button', { name: overflow })).toHaveTextContent(overflow)
    else expect(within(choiceGrid).queryByRole('button', { name: /more/ })).not.toBeInTheDocument()
  })

  it('opens the mobile overflow list and selects a hidden family by its stable ID', () => {
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 375 })
    const onChange = vi.fn()
    const options = Array.from({ length: 8 }, (_, index) => ({ value: `family-${index + 1}`, label: `Family ${index + 1}` }))
    render(<ResponsiveChoice ariaLabel="Garment family" value="family-1" options={options} onChange={onChange} mobilePreviewLimit={5} />)

    fireEvent.click(screen.getByRole('button', { name: '+3 more' }))
    fireEvent.click(within(screen.getByRole('dialog', { name: 'Garment family' })).getByRole('button', { name: 'Family 8' }))
    expect(onChange).toHaveBeenCalledWith('family-8')
  })

  it('shows compact choices and puts overflow in a searchable popup', () => {
    const onChange = vi.fn()
    render(<ResponsiveChoice ariaLabel="Garment family" value="shirt" options={[
      { value: 'abaya', label: 'Abaya' },
      { value: 'shirt', label: 'Men’s Shirt' },
      { value: 'dress', label: 'Long Dress' },
      { value: 'pants', label: 'Pants' },
      { value: 'skirt', label: 'Skirt' },
      { value: 'coat', label: 'Coat' },
      { value: 'jacket', label: 'Jacket' },
      { value: 'thobe', label: 'Thobe' },
      { value: 'tunic', label: 'Tunic' },
    ]} onChange={onChange} />)

    expect(screen.getByRole('button', { name: 'Men’s Shirt' })).toHaveAttribute('aria-pressed', 'true')
    fireEvent.click(screen.getByRole('button', { name: '+7 more' }))
    expect(screen.getByRole('dialog', { name: 'Garment family' })).toBeInTheDocument()
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search options' }), { target: { value: 'abaya' } })
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Abaya' }))

    expect(onChange).toHaveBeenCalledWith('abaya')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('places a browse-all plus tile in the sixth slot of a six-card family picker', () => {
    const onChange = vi.fn()
    render(<ResponsiveChoice ariaLabel="Garment family" value="abaya" previewLimit={5} options={[
      { value: 'abaya', label: 'Abaya' },
      { value: 'dress', label: 'Darraa / Long Dress' },
      { value: 'dishdasha', label: 'Kuwaiti Dishdasha' },
      { value: 'shirt', label: 'Men’s Shirt' },
      { value: 'thobe', label: 'Thobe' },
      { value: 'trousers', label: 'Trousers' },
    ]} onChange={onChange} />)

    const choiceGrid = screen.getByRole('group', { name: 'Garment family' })
    expect(within(choiceGrid).getAllByRole('button')).toHaveLength(6)
    const moreTile = within(choiceGrid).getByRole('button', { name: 'Browse all 6 choices' })
    expect(moreTile).toHaveClass('responsive-choice-more-tile')
    fireEvent.click(moreTile)
    fireEvent.click(within(screen.getByRole('dialog', { name: 'Garment family' })).getByRole('button', { name: 'Trousers' }))
    expect(onChange).toHaveBeenCalledWith('trousers')
  })

  it('closes the overflow popup with Escape and returns focus to the choice tiles', () => {
    render(<ResponsiveChoice ariaLabel="Garment family" value="shirt" options={[
      { value: 'shirt', label: 'Men’s Shirt' }, { value: 'dress', label: 'Long Dress' }, { value: 'abaya', label: 'Abaya' },
    ]} onChange={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: '+1 more' }))
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Men’s Shirt' })).toHaveFocus()
  })

  it('preserves empty-value prompts used by legacy CustomSelect callers', () => {
    render(<CustomSelect ariaLabel="Shop" value="" options={[
      { value: '', label: 'Choose a shop' }, { value: 'one', label: 'Shop one' },
    ]} onChange={vi.fn()} />)
    expect(screen.getByText('Choose a shop')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Shop one' })).toBeInTheDocument()
  })
})
