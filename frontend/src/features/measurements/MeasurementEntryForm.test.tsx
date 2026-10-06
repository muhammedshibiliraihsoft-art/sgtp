import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MeasurementEntryForm, type DraftValue } from './MeasurementEntryForm'
import type { MeasurementDefinition } from './types'
import i18n from '../../i18n'

const definitions: MeasurementDefinition[] = [
  { id: 'chest-id', code: 'chest', group_code: 'upper', sort_order: 1, is_active: true, is_global: true, translations: [{ locale: 'en', name: 'Chest', description: '' }], mappings: [] },
  { id: 'sleeve-id', code: 'sleeve', group_code: 'upper', sort_order: 2, is_active: true, is_global: true, translations: [{ locale: 'en', name: 'Sleeve', description: '' }], mappings: [] },
]

describe('MeasurementEntryForm workflow', () => {
  afterEach(cleanup)

  beforeEach(async () => {
    await i18n.changeLanguage('en')
  })

  it('bulk-applies the selected unit without changing values and keeps per-row overrides', () => {
    const values: Record<string, DraftValue> = {
      'chest-id': { value: '40.125', unit: 'INCH' },
      'sleeve-id': { value: '62', unit: '' },
    }
    render(<MeasurementEntryForm
      definitions={definitions}
      seedValues={values}
      previousValues={{}}
      onDirtyChange={vi.fn()}
      onSave={vi.fn(async () => true)}
      saving={false}
      canWrite
      locale="en"
    />)

    fireEvent.click(within(screen.getByRole('group', { name: 'Default unit' })).getByRole('button', { name: 'Default unit: CM' }))
    expect(within(screen.getByRole('group', { name: 'Chest unit' })).getByRole('button', { name: 'Chest unit: CM' })).toHaveAttribute('aria-pressed', 'true')
    expect((screen.getByLabelText('Chest') as HTMLInputElement).value).toBe('40.125')
    expect((screen.getByLabelText('Sleeve') as HTMLInputElement).value).toBe('62')

    fireEvent.click(within(screen.getByRole('group', { name: 'Chest unit' })).getByRole('button', { name: 'Chest unit: INCH' }))
    expect(within(screen.getByRole('group', { name: 'Chest unit' })).getByRole('button', { name: 'Chest unit: INCH' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('disables both global and row controls for read-only or saving forms', () => {
    render(<MeasurementEntryForm
      definitions={definitions}
      seedValues={{}}
      previousValues={{}}
      onDirtyChange={vi.fn()}
      onSave={vi.fn(async () => true)}
      saving={false}
      canWrite={false}
      locale="en"
    />)

    expect(within(screen.getByRole('group', { name: 'Default unit' })).getByRole('button', { name: 'Default unit: INCH' })).toBeDisabled()
    expect(within(screen.getByRole('group', { name: 'Chest unit' })).getByRole('button', { name: 'Chest unit: CM' })).toBeDisabled()
  })

  it('navigates on a second Enter within 500ms and selects the next value', () => {
    const now = vi.spyOn(Date, 'now').mockReturnValueOnce(1000).mockReturnValueOnce(1200)
    render(<MeasurementEntryForm definitions={definitions} seedValues={{ 'chest-id': { value: '40', unit: 'CM' }, 'sleeve-id': { value: '24', unit: 'CM' } }} previousValues={{ 'chest-id': { value: '39', unit: 'CM' } }} onDirtyChange={vi.fn()} onSave={vi.fn(async () => true)} saving={false} canWrite locale="en" />)

    const chest = screen.getByLabelText('Chest') as HTMLInputElement
    const sleeve = screen.getByLabelText('Sleeve') as HTMLInputElement
    expect(screen.getByText('Previous: 39 CM')).toBeInTheDocument()
    chest.focus()
    fireEvent.keyDown(chest, { key: 'Enter' })
    expect(document.activeElement).toBe(chest)
    fireEvent.keyDown(chest, { key: 'Enter' })
    expect(document.activeElement).toBe(sleeve)
    expect(sleeve.selectionStart).toBe(0)
    expect(sleeve.selectionEnd).toBe(sleeve.value.length)
    now.mockRestore()
  })

  it('uses Shift+Enter to return to the prior field and does not submit', () => {
    const onSave = vi.fn(async () => true)
    render(<MeasurementEntryForm definitions={definitions} seedValues={{ 'chest-id': { value: '40', unit: 'CM' }, 'sleeve-id': { value: '24', unit: 'CM' } }} previousValues={{}} onDirtyChange={vi.fn()} onSave={onSave} saving={false} canWrite locale="en" />)
    const chest = screen.getByLabelText('Chest')
    const sleeve = screen.getByLabelText('Sleeve')
    sleeve.focus()
    fireEvent.keyDown(sleeve, { key: 'Enter', shiftKey: true })
    expect(document.activeElement).toBe(chest)
    expect(onSave).not.toHaveBeenCalled()
  })
})
