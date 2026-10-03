import type { MeasurementDefinition } from './types'
import type { MeasurementUnit } from './types'
import { useTranslation } from 'react-i18next'

// A unit is intentionally blank until the user chooses one.  The measurement
// contract forbids an implicit CM/INCH default because that could permanently
// misrepresent an otherwise valid decimal value.
export type DraftValue = { value: string; unit: MeasurementUnit | '' }

interface Props {
  definitions: MeasurementDefinition[]
  values: Record<string, DraftValue>
  onChange: (definitionId: string, value: DraftValue) => void
  onSave: () => void
  saving: boolean
  canWrite: boolean
  locale: string
}

function definitionName(definition: MeasurementDefinition, locale: string) {
  return definition.translations.find(item => item.locale === locale)?.name
    || definition.translations.find(item => item.locale === 'en')?.name
    || definition.code
}

function definitionDescription(definition: MeasurementDefinition, locale: string) {
  return definition.translations.find(item => item.locale === locale)?.description
    || definition.translations.find(item => item.locale === 'en')?.description
    || ''
}

export function MeasurementEntryForm({ definitions, values, onChange, onSave, saving, canWrite, locale }: Props) {
  const { t } = useTranslation()
  if (!definitions.length) return <div className="measurement-empty" role="status">{t('measurements.noDefinitions')}</div>

  const completed = definitions.filter(item => values[item.id]?.value.trim()).length
  const groups = new Map<string, MeasurementDefinition[]>()
  definitions.forEach(definition => {
    const key = definition.group_code || 'measurements'
    groups.set(key, [...(groups.get(key) ?? []), definition])
  })

  return <div className="measurement-entry">
    <div className="measurement-entry-header"><div><h3>{t('measurements.measurements')}</h3><p>{t('measurements.entered', { done: completed, total: definitions.length })} · {t('measurements.partialAllowed')}</p></div><button type="button" className="btn-primary" onClick={onSave} disabled={!canWrite || saving || completed === 0}>{saving ? t('measurements.saving') : t('measurements.saveVersion')}</button></div>
    {[...groups.entries()].map(([group, items]) => <section className="measurement-field-group" key={group}>
      {groups.size > 1 && <h4>{group.replaceAll('_', ' ')}</h4>}
      <div className="measurement-field-grid">{items.map(definition => {
        const label = definitionName(definition, locale)
        const description = definitionDescription(definition, locale)
        const current = values[definition.id] ?? { value: '', unit: '' as const }
        return <label className="measurement-field" key={definition.id}>
          <span>{label}</span>
          <span className="measurement-field-inputs">
            <input
              type="number"
              inputMode="decimal"
              step="0.0001"
              aria-label={label}
              value={current.value}
              onChange={event => onChange(definition.id, { ...current, value: event.target.value })}
              disabled={!canWrite || saving}
            />
            <select aria-label={`${label} unit`} value={current.unit} onChange={event => onChange(definition.id, { ...current, unit: event.target.value as MeasurementUnit })} disabled={!canWrite || saving} required>
              <option value="" disabled>{t('measurements.chooseUnit')}</option>
              <option value="CM">CM</option><option value="INCH">INCH</option>
            </select>
          </span>
          {description && <small>{description}</small>}
        </label>
      })}</div>
    </section>)}
    <p className="measurement-unit-note">{t('measurements.unitNote')}</p>
  </div>
}
