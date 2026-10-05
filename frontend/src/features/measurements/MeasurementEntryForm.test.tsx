import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MeasurementEntryForm, type DraftValue } from './MeasurementEntryForm'
import type { MeasurementDefinition } from './types'
import i18n from '../../i18n'

const definitions: MeasurementDefinition[] = [
  { id: 'chest-id', code: 'chest', group_code: 'upper', sort_order: 1, is_active: true, is_global: true, translations: [{ locale: 'en', name: 'Chest', description: '' }], mappings: [] },
  { id: 'sleeve-id', code: 'sleeve', group_code: 'upper', sort_order: 2, is_active: true, is_global: true, translations: [{ locale: 'en', name: 'Sleeve', description: '' }], mappings: [] },
]

describe('MeasurementEntryForm unit controls', () => {
  afterEach(cleanup)

  beforeEach(async () => {
    await i18n.changeLanguage('en')
  })

  it('bulk-applies the selected unit without changing values and keeps per-row overrides', () => {
    const values: Record<string, DraftValue> = {
      'chest-id': { value: '40.125', unit: 'INCH' },
      'sleeve-id': { value: '62', unit: '' },
    }
    const onChange = vi.fn()

    render(<MeasurementEntryForm
      definitions={definitions}
      values={values}
      onChange={onChange}
      onSave={vi.fn()}
      saving={false}
      canWrite
      locale="en"
    />)

    fireEvent.click(within(screen.getByRole('group', { name: 'Default unit' })).getByRole('button', { name: 'Default unit: CM' }))
    expect(onChange).toHaveBeenNthCalledWith(1, 'chest-id', { value: '40.125', unit: 'CM' })
    expect(onChange).toHaveBeenNthCalledWith(2, 'sleeve-id', { value: '62', unit: 'CM' })

    fireEvent.click(within(screen.getByRole('group', { name: 'Chest unit' })).getByRole('button', { name: 'Chest unit: INCH' }))
    expect(onChange).toHaveBeenNthCalledWith(3, 'chest-id', { value: '40.125', unit: 'INCH' })
  })

  it('disables both global and row controls for read-only or saving forms', () => {
    render(<MeasurementEntryForm
      definitions={definitions}
      values={{}}
      onChange={vi.fn()}
      onSave={vi.fn()}
      saving={false}
      canWrite={false}
      locale="en"
    />)

    expect(within(screen.getByRole('group', { name: 'Default unit' })).getByRole('button', { name: 'Default unit: INCH' })).toBeDisabled()
    expect(within(screen.getByRole('group', { name: 'Chest unit' })).getByRole('button', { name: 'Chest unit: CM' })).toBeDisabled()
  })
})
