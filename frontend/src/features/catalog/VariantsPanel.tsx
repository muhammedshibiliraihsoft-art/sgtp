import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, ChevronLeft, ChevronRight, Loader2, Plus, Search, Shirt, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../services/useAuth'
import { ApiError } from '../../services/apiClient'
import { createGlobalVariant, createShopVariant, getGlobalVariant, getGlobalVariantsPage, getShopVariant, getShopVariantsPage, setGlobalVariantDefault, setGlobalVariantStatus, setShopVariantStatus, updateGlobalVariant, updateShopVariant } from './api'
import type { CatalogFamily, TranslationInput, Variant, VariantDetail, VariantSource, VariantStatus } from './types'

type Props = { shopId?: string; families: CatalogFamily[]; initialFamily?: string; canManageVariants?: boolean }
type Locale = TranslationInput['locale']
type TranslationDraft = Record<Locale, { name: string; description: string }>
const locales: Locale[] = ['en', 'ar-KW', 'bn', 'ur']
const emptyDraft = (): TranslationDraft => ({ en: { name: '', description: '' }, 'ar-KW': { name: '', description: '' }, bn: { name: '', description: '' }, ur: { name: '', description: '' } })

function messageFor(error: unknown) {
  return error instanceof ApiError ? error.message : 'Could not load variants. Please try again.'
}

export function VariantsPanel({ shopId, families, initialFamily = '', canManageVariants = false }: Props) {
  const { t } = useTranslation()
  const { user } = useAuth()
  const navigate = useNavigate()
  const isMainSupplier = Boolean(user?.is_main_supplier_admin)
  const canManage = isMainSupplier || canManageVariants
  const [rows, setRows] = useState<Variant[]>([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [hasPrevious, setHasPrevious] = useState(false)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [family, setFamily] = useState(initialFamily)
  const [source, setSource] = useState<VariantSource>('all')
  const [status, setStatus] = useState<VariantStatus>('ACTIVE')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<VariantDetail | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [code, setCode] = useState('')
  const [draft, setDraft] = useState<TranslationDraft>(emptyDraft)
  const [showTranslations, setShowTranslations] = useState(false)
  const closeSurfaceRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const timer = window.setTimeout(() => { setPage(1); setSearch(searchInput.trim()) }, 300)
    return () => window.clearTimeout(timer)
  }, [searchInput])

  const load = useCallback(async () => {
    try {
      const result = isMainSupplier
        ? await getGlobalVariantsPage({ page, search, family: family || undefined, status })
        : await getShopVariantsPage(shopId ?? '', { page, search, family: family || undefined, status, source })
      setRows(result.results)
      setCount(result.count)
      setHasNext(Boolean(result.next))
      setHasPrevious(Boolean(result.previous))
      setError(null)
    } catch (loadError) {
      setError(messageFor(loadError))
    } finally {
      setLoading(false)
    }
  }, [family, isMainSupplier, page, search, shopId, source, status])

  useEffect(() => { queueMicrotask(() => void load()) }, [load])

  useEffect(() => {
    if (!createOpen && !selected) return
    const returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { setCreateOpen(false); setSelected(null); setEditing(false) }
      if (event.key !== 'Tab') return
      const dialog = document.querySelector<HTMLElement>('.variant-dialog, .variant-drawer')
      const focusable = dialog?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [href], [tabindex]:not([tabindex="-1"])')
      if (!focusable?.length) return
      if (event.shiftKey && document.activeElement === focusable[0]) { event.preventDefault(); focusable[focusable.length - 1].focus() }
      else if (!event.shiftKey && document.activeElement === focusable[focusable.length - 1]) { event.preventDefault(); focusable[0].focus() }
    }
    document.addEventListener('keydown', onKeyDown)
    closeSurfaceRef.current?.focus()
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      if (returnFocus?.isConnected) returnFocus.focus()
    }
  }, [createOpen, selected, editing])

  const familyNames = useMemo(() => new Map(families.map(item => [item.id, item.name])), [families])

  function changeFilter(update: () => void) {
    setLoading(true)
    update()
    setPage(1)
  }

  function startCreate() {
    setSelected(null)
    setCode('')
    setDraft(emptyDraft())
    setShowTranslations(false)
    setCreateOpen(true)
  }

  async function openVariant(variant: Variant) {
    setError(null)
    try {
      setSelected(isMainSupplier ? await getGlobalVariant(variant.id) : await getShopVariant(shopId ?? '', variant.id))
      setEditing(false)
    } catch (detailError) {
      setError(messageFor(detailError))
    }
  }

  function loadDraft(detail: VariantDetail) {
    const values = emptyDraft()
    detail.translations.forEach(item => { values[item.locale] = { name: item.name, description: item.description ?? '' } })
    setDraft(values)
    setShowTranslations(detail.translations.some(item => item.locale !== 'en'))
    setCode(detail.code)
    setEditing(true)
  }

  function payload() {
    return locales.flatMap(locale => {
      const value = draft[locale]
      if (!value.name.trim()) return []
      return [{ locale, name: value.name.trim(), ...(value.description.trim() ? { description: value.description.trim() } : {}) }]
    })
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!draft.en.name.trim()) return
    setSaving(true)
    setError(null)
    try {
      const translations = payload()
      if (createOpen) {
        const familyId = family || families[0]?.id
        if (!familyId) return
        const input = { family_id: familyId, code: code.trim(), translations }
        if (isMainSupplier) await createGlobalVariant(input)
        else await createShopVariant(shopId ?? '', input)
        setCreateOpen(false)
      } else if (selected) {
        const result = isMainSupplier
          ? await updateGlobalVariant(selected.id, translations)
          : await updateShopVariant(shopId ?? '', selected.id, translations)
        setSelected(result)
        setEditing(false)
      }
      await load()
    } catch (saveError) {
      setError(messageFor(saveError))
    } finally {
      setSaving(false)
    }
  }

  async function updateStatus(active: boolean) {
    if (!selected || !window.confirm(active ? 'Reactivate this variant?' : 'Archive this variant? Historical records will be preserved.')) return
    setSaving(true)
    setError(null)
    try {
      const result = isMainSupplier
        ? await setGlobalVariantStatus(selected.id, active)
        : await setShopVariantStatus(shopId ?? '', selected.id, active)
      setSelected(result)
      await load()
    } catch (actionError) {
      setError(messageFor(actionError))
    } finally {
      setSaving(false)
    }
  }

  async function setDefault() {
    if (!selected || selected.is_default || !window.confirm('Make this the default variant for its family?')) return
    setSaving(true)
    setError(null)
    try {
      const result = await setGlobalVariantDefault(selected.id)
      setSelected(result)
      await load()
    } catch (actionError) {
      setError(messageFor(actionError))
    } finally {
      setSaving(false)
    }
  }

  function viewDesigns(variant: VariantDetail) {
    const query = new URLSearchParams({ family: variant.family, variant: variant.id })
    navigate(`/designs?${query.toString()}`)
  }

  const localesToEdit = showTranslations ? locales.filter(locale => locale !== 'en') : []

  return <section className="variants-panel" aria-label={t('catalog.variants', 'Variants')}>
    <div className="catalog-family-toolbar variants-toolbar">
      <label className="catalog-search"><Search size={17} aria-hidden="true" /><span className="sr-only">{t('catalog.searchVariants', 'Search variants')}</span><input type="search" value={searchInput} onChange={event => { setLoading(true); setSearchInput(event.target.value) }} placeholder={t('catalog.searchVariantsPlaceholder', 'Search variants...')} /></label>
      <label className="variants-family-filter"><span>{t('catalog.family', 'Family')}</span><select value={family} onChange={event => changeFilter(() => setFamily(event.target.value))}><option value="">{t('catalog.allFamilies', 'All Families')}</option>{families.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      {!isMainSupplier && <div className="global-family-status-filter" role="group" aria-label={t('catalog.source', 'Source')}>{(['all', 'global', 'shop'] as const).map(value => <button type="button" key={value} className={source === value ? 'active' : ''} aria-pressed={source === value} onClick={() => changeFilter(() => setSource(value))}>{value === 'all' ? t('catalog.all', 'All') : value === 'global' ? t('catalog.global', 'Global') : t('catalog.shop', 'Shop')}</button>)}</div>}
      <div className="variants-toolbar-tail">
        {canManage && <div className="global-family-status-filter" role="group" aria-label={t('catalog.status', 'Status')}>{(['ACTIVE', 'ARCHIVED', 'all'] as const).map(value => <button type="button" key={value} className={status === value ? 'active' : ''} aria-pressed={status === value} onClick={() => changeFilter(() => setStatus(value))}>{value === 'ACTIVE' ? t('catalog.active', 'Active') : value === 'ARCHIVED' ? t('catalog.archived', 'Archived') : t('catalog.all', 'All')}</button>)}</div>}
        <span className="catalog-family-count">{t('catalog.variantCount', '{{count}} variants', { count })}</span>
      </div>
      {canManage && <button className="primary-button variants-create-button" type="button" onClick={startCreate} disabled={!families.length}><Plus size={16} />{t('catalog.newVariant', 'New Variant')}</button>}
    </div>
    {error && <div className="catalog-error" role="alert">{error}<button type="button" onClick={() => void load()} disabled={loading}>{t('catalog.retry', 'Retry')}</button></div>}
    {loading ? <div className="catalog-loading" role="status"><Loader2 className="animate-spin" /></div> : rows.length ? <div className="catalog-grid variants-grid">
      {rows.map(variant => <button className="catalog-card catalog-family-card variant-card" type="button" key={variant.id} onClick={() => void openVariant(variant)}>
        <Shirt size={20} aria-hidden="true" />
        <span><strong>{variant.name}</strong><small>{familyNames.get(variant.family) ?? variant.family} · {variant.code}</small></span>
        {variant.is_default && <span className="catalog-tag">{t('catalog.default', 'Default')}</span>}
        {!variant.is_active && <span className="catalog-tag catalog-tag-muted">{t('catalog.archived', 'Archived')}</span>}
        <span className="variant-source">{variant.is_global ? t('catalog.global', 'Global') : t('catalog.shop', 'Shop')}</span>
      </button>)}
    </div> : <div className="catalog-empty variants-empty" role="status"><AlertCircle size={17} />{search ? t('catalog.noVariantMatches', 'No variants match your search.') : status === 'ARCHIVED' ? t('catalog.noArchivedVariants', 'No archived variants.') : family ? t('catalog.noVariantsForFamily', 'No variants found for this family.') : t('catalog.noVariants', 'No variants available.')}</div>}
    {!loading && (hasPrevious || hasNext) && <nav className="catalog-family-pagination" aria-label={t('catalog.variantPages', 'Variant pages')}><button className="secondary-button" type="button" disabled={!hasPrevious} onClick={() => { setLoading(true); setPage(value => value - 1) }}><ChevronLeft size={16} />{t('catalog.previous', 'Previous')}</button><span>{t('catalog.page', 'Page {{page}}', { page })}</span><button className="secondary-button" type="button" disabled={!hasNext} onClick={() => { setLoading(true); setPage(value => value + 1) }}>{t('catalog.next', 'Next')}<ChevronRight size={16} /></button></nav>}

    {createOpen && <div className="catalog-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setCreateOpen(false) }}><form className="catalog-dialog variant-dialog" role="dialog" aria-modal="true" aria-labelledby="variant-create-title" onSubmit={event => void submit(event)}>
      <div className="catalog-dialog-heading"><h2 id="variant-create-title">{t('catalog.newVariant', 'New Variant')}</h2><button ref={closeSurfaceRef} type="button" className="catalog-icon-button" onClick={() => setCreateOpen(false)} aria-label={t('catalog.close', 'Close')}><X size={18} /></button></div>
      <label>{t('catalog.family', 'Garment family')}<select required value={family || families[0]?.id || ''} onChange={event => setFamily(event.target.value)}>{families.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label>{t('catalog.nameEnglish', 'Name (English)')}<input required maxLength={120} value={draft.en.name} onChange={event => setDraft(value => ({ ...value, en: { ...value.en, name: event.target.value } }))} /></label>
      <label>{t('catalog.code', 'Code')}<input required maxLength={64} pattern="[a-zA-Z0-9_-]+" value={code} onChange={event => setCode(event.target.value)} /></label>
      <label>{t('catalog.description', 'Description (optional)')}<textarea rows={2} maxLength={500} value={draft.en.description} onChange={event => setDraft(value => ({ ...value, en: { ...value.en, description: event.target.value } }))} /></label>
      <button type="button" className="global-disclosure" aria-expanded={showTranslations} onClick={() => setShowTranslations(value => !value)}>{showTranslations ? '−' : '+'} {t('catalog.addTranslations', 'Add translations')}</button>
      {localesToEdit.map(locale => <fieldset className="variant-translation-fields" key={locale}><legend>{locale}</legend><label>{t('catalog.name', 'Name')}<input maxLength={120} value={draft[locale].name} onChange={event => setDraft(value => ({ ...value, [locale]: { ...value[locale], name: event.target.value } }))} /></label><label>{t('catalog.description', 'Description')}<textarea rows={2} maxLength={500} value={draft[locale].description} onChange={event => setDraft(value => ({ ...value, [locale]: { ...value[locale], description: event.target.value } }))} /></label></fieldset>)}
      <div className="catalog-dialog-actions"><button type="button" className="secondary-button" onClick={() => setCreateOpen(false)}>{t('catalog.cancel', 'Cancel')}</button><button type="submit" className="primary-button" disabled={saving || !families.length}>{saving ? <Loader2 size={16} className="animate-spin" /> : null}{t('catalog.create', 'Create')}</button></div>
    </form></div>}

    {selected && <div className="catalog-family-drawer-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) { setSelected(null); setEditing(false) } }}><section className="catalog-family-drawer variant-drawer" role="dialog" aria-modal="true" aria-labelledby="variant-detail-title">
      <div className="catalog-family-drawer-header"><div className="catalog-family-drawer-identity"><Shirt size={22} aria-hidden="true" /><div><h2 id="variant-detail-title">{selected.name}</h2><small>{familyNames.get(selected.family) ?? selected.family} · {selected.code}</small></div></div><button ref={closeSurfaceRef} type="button" className="catalog-icon-button" aria-label={t('catalog.close', 'Close')} onClick={() => { setSelected(null); setEditing(false) }}><X size={18} /></button></div>
      <div className="variant-detail-tags">{selected.is_global ? t('catalog.global', 'Global') : t('catalog.shop', 'Shop')} · {selected.is_active ? t('catalog.active', 'Active') : t('catalog.archived', 'Archived')}{selected.is_default ? ` · ${t('catalog.default', 'Default')}` : ''}</div>
      {editing ? <form className="catalog-dialog variant-edit-form" onSubmit={event => void submit(event)}><label>{t('catalog.nameEnglish', 'Name (English)')}<input required maxLength={120} value={draft.en.name} onChange={event => setDraft(value => ({ ...value, en: { ...value.en, name: event.target.value } }))} /></label><label>{t('catalog.code', 'Code')}<input value={code} readOnly /></label><label>{t('catalog.description', 'Description')}<textarea rows={3} maxLength={500} value={draft.en.description} onChange={event => setDraft(value => ({ ...value, en: { ...value.en, description: event.target.value } }))} /></label><button type="button" className="global-disclosure" aria-expanded={showTranslations} onClick={() => setShowTranslations(value => !value)}>{showTranslations ? '−' : '+'} {t('catalog.translations', 'Translations')}</button>{showTranslations && locales.filter(locale => locale !== 'en').map(locale => <fieldset className="variant-translation-fields" key={locale}><legend>{locale}</legend><label>{t('catalog.name', 'Name')}<input maxLength={120} value={draft[locale].name} onChange={event => setDraft(value => ({ ...value, [locale]: { ...value[locale], name: event.target.value } }))} /></label><label>{t('catalog.description', 'Description')}<textarea rows={2} maxLength={500} value={draft[locale].description} onChange={event => setDraft(value => ({ ...value, [locale]: { ...value[locale], description: event.target.value } }))} /></label></fieldset>)}<div className="catalog-dialog-actions"><button type="button" className="secondary-button" onClick={() => setEditing(false)}>{t('catalog.cancel', 'Cancel')}</button><button className="primary-button" type="submit" disabled={saving}>{saving ? <Loader2 size={16} className="animate-spin" /> : null}{t('catalog.save', 'Save changes')}</button></div></form> : <>
        {selected.description && <p className="variant-description">{selected.description}</p>}
        {selected.is_global && !isMainSupplier && <p className="catalog-drawer-muted">{t('catalog.globalVariantReadOnly', 'Global variants are managed by Main Supplier.')}</p>}
      <div className="catalog-family-drawer-actions"><button type="button" className="primary-button" onClick={() => viewDesigns(selected)}>{t('catalog.viewDesigns', 'View Designs')}</button>
          {isMainSupplier && selected.is_global && selected.is_active && !selected.is_default && <button type="button" className="secondary-button" disabled={saving} onClick={() => void setDefault()}>{t('catalog.setDefault', 'Set as Default')}</button>}
          {canManage && (isMainSupplier || !selected.is_global) && <><button type="button" className="secondary-button" disabled={saving} onClick={() => loadDraft(selected)}>{t('catalog.edit', 'Edit')}</button><button type="button" className="secondary-button" disabled={saving} onClick={() => void updateStatus(!selected.is_active)}>{selected.is_active ? t('catalog.archive', 'Archive') : t('catalog.reactivate', 'Reactivate')}</button></>}
        </div>
      </>}
    </section></div>}
  </section>
}
