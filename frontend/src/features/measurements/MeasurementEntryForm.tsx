import { memo, useCallback, useMemo, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { MeasurementUnitControl } from './MeasurementUnitControl'
import type { MeasurementDefinition, MeasurementUnit } from './types'

// A unit is intentionally blank until the user chooses one.  The measurement
// contract forbids an implicit CM/INCH default because it could misrepresent a value.
export type DraftValue = { value: string; unit: MeasurementUnit | '' }

interface Props {
  definitions: MeasurementDefinition[]
  seedValues: Record<string, DraftValue>
  previousValues: Record<string, { value: string; unit: MeasurementUnit }>
  onDirtyChange: (dirty: boolean) => void
  onSave: (values: Record<string, DraftValue>) => Promise<boolean>
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

interface FieldProps {
  definition: MeasurementDefinition
  locale: string
  value: DraftValue
  previous?: { value: string; unit: MeasurementUnit }
  invalid: boolean
  disabled: boolean
  onChange: (id: string, value: DraftValue) => void
  onKeyDown: (event: KeyboardEvent<HTMLInputElement>, id: string) => void
  onBlur: () => void
  inputRefs: Map<string, HTMLInputElement>
}

const EMPTY_DRAFT: DraftValue = { value: '', unit: '' }

const MeasurementField = memo(function MeasurementField({ definition, locale, value, previous, invalid, disabled, onChange, onKeyDown, onBlur, inputRefs }: FieldProps) {
  const { t } = useTranslation()
  const label = definitionName(definition, locale)
  const description = definitionDescription(definition, locale)
  const inputId = `measurement-${definition.id}`
  const current = value
  const inputRef = useCallback((node: HTMLInputElement | null) => {
    if (node) inputRefs.set(definition.id, node)
    else inputRefs.delete(definition.id)
  }, [definition.id, inputRefs])

  return <div className="measurement-field" key={definition.id}>
    <label htmlFor={inputId}>{label}</label>
    <div className="measurement-field-inputs">
      <input
        ref={inputRef}
        id={inputId}
        type="text"
        inputMode="decimal"
        autoComplete="off"
        value={current.value}
        onChange={event => onChange(definition.id, { ...current, value: event.target.value })}
        onKeyDown={event => onKeyDown(event, definition.id)}
        onBlur={onBlur}
        disabled={disabled}
        aria-invalid={invalid}
        aria-describedby={description ? `${inputId}-description ${inputId}-previous` : `${inputId}-previous`}
      />
      <MeasurementUnitControl
        label={t('measurements.rowUnit', { name: label })}
        value={current.unit}
        compact
        disabled={disabled}
        onChange={unit => onChange(definition.id, { ...current, unit })}
      />
    </div>
    {description && <small id={`${inputId}-description`}>{description}</small>}
    <small id={`${inputId}-previous`} className="measurement-previous-hint">
      {previous ? `${t('measurements.previousValue', 'Previous')}: ${previous.value} ${previous.unit}` : '\u00a0'}
    </small>
  </div>
})

export const MeasurementEntryForm = memo(function MeasurementEntryForm({ definitions, seedValues, previousValues, onDirtyChange, onSave, saving, canWrite, locale }: Props) {
  const { t } = useTranslation()
  const [values, setValues] = useState<Record<string, DraftValue>>(seedValues)
  const [invalidFieldId, setInvalidFieldId] = useState<string | null>(null)
  const valuesRef = useRef(values)
  const [inputRefs] = useState(() => new Map<string, HTMLInputElement>())
  const saveButtonRef = useRef<HTMLButtonElement>(null)
  const lastEnterRef = useRef<{ fieldId: string; time: number } | null>(null)

  const groups = useMemo(() => {
    const result = new Map<string, MeasurementDefinition[]>()
    definitions.forEach(definition => {
      const key = definition.group_code || 'measurements'
      const items = result.get(key)
      if (items) items.push(definition)
      else result.set(key, [definition])
    })
    return result
  }, [definitions])

  const completed = definitions.reduce((count, item) => count + Number(Boolean(values[item.id]?.value.trim())), 0)
  const selectedUnits = new Set(definitions.map(item => values[item.id]?.unit ?? ''))
  const commonUnit = selectedUnits.size === 1 ? [...selectedUnits][0] as MeasurementUnit | '' : ''

  const updateValue = useCallback((definitionId: string, value: DraftValue) => {
    const next = { ...valuesRef.current, [definitionId]: value }
    valuesRef.current = next
    setValues(next)
    setInvalidFieldId(null)
    lastEnterRef.current = null
    onDirtyChange(true)
  }, [onDirtyChange])

  const focusField = useCallback((fieldId: string, selectValue: boolean) => {
    const target = inputRefs.get(fieldId)
    if (!target) return
    target.focus()
    if (selectValue && target.value) target.select()
  }, [inputRefs])

  const onBlur = useCallback(() => { lastEnterRef.current = null }, [])

  const handleKeyDown = useCallback((event: KeyboardEvent<HTMLInputElement>, fieldId: string) => {
    if (event.key !== 'Enter') return
    event.preventDefault()
    const index = definitions.findIndex(item => item.id === fieldId)
    const current = valuesRef.current[fieldId]
    const raw = current?.value.trim() ?? ''
    if (raw && (!/^-?\d+(?:\.\d{1,4})?$/.test(raw) || !current?.unit)) {
      setInvalidFieldId(fieldId)
      return
    }
    if (event.shiftKey) {
      lastEnterRef.current = null
      if (index > 0) focusField(definitions[index - 1].id, true)
      return
    }

    const now = Date.now()
    const previousEnter = lastEnterRef.current
    if (!previousEnter || previousEnter.fieldId !== fieldId || now - previousEnter.time > 500) {
      lastEnterRef.current = { fieldId, time: now }
      return
    }
    lastEnterRef.current = null

    setInvalidFieldId(null)
    const nextDefinition = definitions[index + 1]
    if (nextDefinition) focusField(nextDefinition.id, true)
    else if (canWrite && !saving && definitions.some(item => valuesRef.current[item.id]?.value.trim())) saveButtonRef.current?.focus()
  }, [canWrite, definitions, focusField, saving])

  const applyDefaultUnit = useCallback((unit: MeasurementUnit) => {
    const next = { ...valuesRef.current }
    definitions.forEach(definition => {
      next[definition.id] = { ...(valuesRef.current[definition.id] ?? EMPTY_DRAFT), unit }
    })
    valuesRef.current = next
    setValues(next)
    setInvalidFieldId(null)
    lastEnterRef.current = null
    onDirtyChange(true)
  }, [definitions, onDirtyChange])

  const submit = useCallback(async () => {
    if (!canWrite || saving || completed === 0) return
    const currentValues = valuesRef.current
    const invalid = definitions.find(definition => {
      const value = currentValues[definition.id]
      const raw = value?.value.trim() ?? ''
      return Boolean(raw && (!/^-?\d+(?:\.\d{1,4})?$/.test(raw) || !value?.unit))
    })
    if (invalid) {
      setInvalidFieldId(invalid.id)
      inputRefs.get(invalid.id)?.focus()
      return
    }
    const saved = await onSave(currentValues)
    if (saved) {
      const empty: Record<string, DraftValue> = {}
      valuesRef.current = empty
      setValues(empty)
      setInvalidFieldId(null)
      onDirtyChange(false)
    }
  }, [canWrite, completed, definitions, inputRefs, onDirtyChange, onSave, saving])

  if (!definitions.length) return <div className="measurement-empty" role="status">{t('measurements.noDefinitions')}</div>

  return <div className="measurement-entry">
    <div className="measurement-entry-header"><div><h3>{t('measurements.measurements')}</h3><p>{t('measurements.entered', { done: completed, total: definitions.length })} · {t('measurements.partialAllowed')}</p></div><button ref={saveButtonRef} type="button" className="btn-primary" onClick={() => void submit()} disabled={!canWrite || saving || completed === 0}>{saving ? t('measurements.saving') : t('measurements.saveVersion')}</button></div>
    {invalidFieldId && <p className="measurement-field-error" role="alert">{t('measurements.enterValue')}</p>}
    <div className="measurement-entry-tools">
      <MeasurementUnitControl
        label={t('measurements.defaultUnit')}
        value={commonUnit}
        disabled={!canWrite || saving}
        onChange={applyDefaultUnit}
      />
      <p className="measurement-global-unit-hint">{t('measurements.globalUnitHint')}</p>
    </div>
    {[...groups.entries()].map(([group, items]) => <section className="measurement-field-group" key={group}>
      {groups.size > 1 && <h4>{group.replaceAll('_', ' ')}</h4>}
      <div className="measurement-field-grid">{items.map(definition => <MeasurementField
        key={definition.id}
        definition={definition}
        locale={locale}
        value={values[definition.id] ?? EMPTY_DRAFT}
        previous={previousValues[definition.id]}
        invalid={invalidFieldId === definition.id}
        disabled={!canWrite || saving}
        onChange={updateValue}
        onKeyDown={handleKeyDown}
        onBlur={onBlur}
        inputRefs={inputRefs}
      />)}</div>
    </section>)}
    <p className="measurement-unit-note">{t('measurements.unitNote')}</p>
  </div>
})
