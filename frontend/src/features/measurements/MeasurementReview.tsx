import type { Client, RelatedPerson } from '../clients/types'
import type { CatalogFamily, OptionGroup, Variant, StyleOption } from '../catalog/types'
import type { MeasurementSet, MeasurementUnit } from './types'
import { useTranslation } from 'react-i18next'
import { PrivateReferenceImage } from './PrivateReferenceImage'

interface Props {
  client: Client
  wearer: RelatedPerson | null
  family: CatalogFamily | null
  variant: Variant | null
  groups: OptionGroup[]
  selectedStyles: Record<string, StyleOption[]>
  designName: string
  designSaved: boolean
  measurementSet: MeasurementSet | null
  historyCount: number
  fabric: { material_id: string; name: string; unit: string; available: string } | null
}

export function MeasurementReview({ client, wearer, family, variant, groups, selectedStyles, designName, designSaved, measurementSet, historyCount, fabric }: Props) {
  const { t, i18n } = useTranslation()
  const measurements = measurementSet?.values ?? []
  const personName = wearer?.name ?? client.name
  return <section className="measurement-review info-card" aria-labelledby="measurement-review-heading">
    <div className="measurement-review-heading"><div><span className="backoffice-eyebrow">{t('measurements.finalReview')}</span><h2 id="measurement-review-heading">{t('measurements.reviewTitle')}</h2></div><span className="measurement-review-count">{t('measurements.historyCount', { count: historyCount })}</span></div>
    <div className="measurement-review-grid">
      <article><h3>{t('measurements.clientAndWearer')}</h3><p><strong>{personName}</strong></p>{wearer && <small>{t('measurements.primaryClient')}: {client.name}</small>}</article>
      <article><h3>{t('measurements.garment')}</h3><p>{family?.name ?? t('measurements.chooseFamily')}</p>{variant && <small>{variant.name}</small>}</article>
      <article><h3>{t('measurements.design')}</h3><p>{designName || (Object.keys(selectedStyles).length ? t('measurements.currentSelections') : t('measurements.noDesign'))}</p>{designSaved && <small>{t('measurements.savedShopDesign')}</small>}{!designSaved && Object.keys(selectedStyles).length > 0 && <small>{t('measurements.designSessionOnly')}</small>}</article>
      <article><h3>{t('measurements.measurements')}</h3>{measurementSet ? <><p>{t('measurements.version', { version: measurementSet.version })}</p><small>{t('measurements.measurementsCount', { count: measurements.length })} · {new Date(measurementSet.created_at).toLocaleString(i18n.resolvedLanguage || 'en')}</small></> : <p>{t('measurements.noSavedSet')}</p>}</article>
      <article><h3>{t('measurements.fabric')}</h3>{fabric ? <><p>{fabric.name}</p><small>{fabric.available} {fabric.unit} {t('measurements.available')} · {t('measurements.displayOnly')}</small></> : <p>{t('measurements.noFabricSelected')}</p>}<small>{t('measurements.fabricNote')}</small></article>
    </div>
    <div className="measurement-review-selections"><h3>{t('measurements.designSections')}</h3>{Object.keys(selectedStyles).length ? <div className="measurement-review-groups">{groups.map(group => {
      const options = selectedStyles[group.id] ?? []
      if (!options.length) return null
      return <section key={group.id}><h4>{group.name}</h4><ul>{options.map(option => <li key={`${option.option_group}:${option.id}`}><PrivateReferenceImage image={option.reference_images[0]} alt={t('measurements.referenceAlt', { name: option.name })} /><span><strong>{option.name}</strong><small>{option.code}</small></span></li>)}</ul></section>
    })}</div> : <p>{t('measurements.noStyleSections')}</p>}</div>
    {measurementSet && <div className="measurement-review-values"><h3>{t('measurements.versionValues', { version: measurementSet.version })}</h3><div className="measurement-review-values-grid">{measurements.map(value => <div key={value.id}><span>{value.label}</span><strong>{value.value} {value.unit as MeasurementUnit}</strong></div>)}</div></div>}
  </section>
}
