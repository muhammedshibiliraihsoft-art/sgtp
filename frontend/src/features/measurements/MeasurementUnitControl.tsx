import type { MeasurementUnit } from './types'
import { useTranslation } from 'react-i18next'

interface Props {
  label: string
  value: MeasurementUnit | ''
  onChange: (unit: MeasurementUnit) => void
  disabled: boolean
  compact?: boolean
}

export function MeasurementUnitControl({ label, value, onChange, disabled, compact = false }: Props) {
  const { t } = useTranslation()
  return <fieldset className={`measurement-unit-control${compact ? ' is-compact' : ''}`} aria-label={label}>
    {!compact && <legend>{label}</legend>}
    <div className="measurement-unit-options">
      {(['INCH', 'CM'] as const).map(unit => <button
        key={unit}
        type="button"
        aria-label={`${label}: ${unit}`}
        aria-pressed={value === unit}
        disabled={disabled}
        className={value === unit ? 'is-selected' : ''}
        onClick={() => onChange(unit)}
      >{t(unit === 'INCH' ? 'measurements.unitInch' : 'measurements.unitCm')}</button>)}
    </div>
  </fieldset>
}
