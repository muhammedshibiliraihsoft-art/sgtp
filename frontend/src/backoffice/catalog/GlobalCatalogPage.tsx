import { useCallback, useEffect, useRef, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertCircle, ChevronDown, ChevronLeft, ChevronRight, ChevronUp, ImagePlus, Loader2, ListTree, Plus, Search, Shirt, Trash2, X } from 'lucide-react'
import { ApiError } from '../../services/apiClient'
import { usePrivateImage } from '../../hooks/usePrivateImage'
import { createGlobalFamily, createGlobalStyleOption, getAllFamilies, getAllGlobalStyleOptions, getFamilyDetail, getFamilies, getOptionGroups, removeGlobalFamilyImage, setGlobalFamilyStatus, updateFamilyOptionGroups, updateGlobalFamily, uploadGlobalFamilyImage, uploadGlobalStyleOptionImages } from '../../features/catalog/api'
import type { CatalogFamily, CatalogFamilyDetail, CatalogFamilyPage, OptionGroup, ShopStyleOptionInputRequest, StyleOption, TranslationInput } from '../../features/catalog/types'
import { VariantsPanel } from '../../features/catalog/VariantsPanel'

type Tab = 'families' | 'variants' | 'groups' | 'styles'
type Locale = TranslationInput['locale']
const LOCALES: Locale[] = ['en', 'ar-KW', 'bn', 'ur']

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : 'Could not load the global catalog.'
}

function rowsOf(page: CatalogFamilyPage | CatalogFamily[]) {
  return Array.isArray(page) ? page : page.results
}

export function GlobalCatalogPage() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<Tab>('families')
  const [families, setFamilies] = useState<CatalogFamily[]>([])
  const [activeVariantFamilies, setActiveVariantFamilies] = useState<CatalogFamily[]>([])
  const [familyCount, setFamilyCount] = useState(0)
  const [familyPage, setFamilyPage] = useState(1)
  const [familyHasNext, setFamilyHasNext] = useState(false)
  const [familyHasPrevious, setFamilyHasPrevious] = useState(false)
  const [familySearchInput, setFamilySearchInput] = useState('')
  const [familySearch, setFamilySearch] = useState('')
  const [familyStatus, setFamilyStatus] = useState<'ACTIVE' | 'ARCHIVED' | 'all'>('ACTIVE')
  const [groups, setGroups] = useState<OptionGroup[]>([])
  const [styleOptions, setStyleOptions] = useState<StyleOption[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedFamily, setSelectedFamily] = useState<CatalogFamilyDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [createStyleOpen, setCreateStyleOpen] = useState(false)
  const [code, setCode] = useState('')
  const [translations, setTranslations] = useState<Record<Locale, { name: string; description: string }>>({
    en: { name: '', description: '' }, 'ar-KW': { name: '', description: '' }, bn: { name: '', description: '' }, ur: { name: '', description: '' },
  })
  const [showExtraTranslations, setShowExtraTranslations] = useState(false)
  const [showDescriptions, setShowDescriptions] = useState(false)
  const [selectedGroupIds, setSelectedGroupIds] = useState<string[]>([])
  const [styleName, setStyleName] = useState('')
  const [styleCode, setStyleCode] = useState('')
  const [styleGroupId, setStyleGroupId] = useState('')
  const [newStyleImages, setNewStyleImages] = useState<File[]>([])
  const [imageBusy, setImageBusy] = useState(false)
  const [styleImageBusyId, setStyleImageBusyId] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const closeSurfaceRef = useRef<HTMLButtonElement>(null)
  const familyImage = usePrivateImage(selectedFamily?.image_content_url)

  useEffect(() => {
    const timer = window.setTimeout(() => { setFamilyPage(1); setFamilySearch(familySearchInput.trim()) }, 250)
    return () => window.clearTimeout(timer)
  }, [familySearchInput])

  const loadCatalog = useCallback(async () => {
    try {
      const [familyPageData, groupRows, styleRows, activeFamilyRows] = await Promise.all([
        getFamilies(familyPage, familySearch, familyStatus), getOptionGroups(), getAllGlobalStyleOptions(), getAllFamilies(),
      ])
      setFamilies(rowsOf(familyPageData))
      setActiveVariantFamilies(activeFamilyRows)
      if (!Array.isArray(familyPageData)) {
        setFamilyCount(familyPageData.count)
        setFamilyHasNext(Boolean(familyPageData.next))
        setFamilyHasPrevious(Boolean(familyPageData.previous))
      } else {
        setFamilyCount(familyPageData.length)
        setFamilyHasNext(false)
        setFamilyHasPrevious(false)
      }
      setGroups(groupRows)
      setStyleOptions(styleRows)
      setError(null)
    } catch (loadError) {
      setError(errorMessage(loadError))
    } finally {
      setIsLoading(false)
    }
  }, [familyPage, familySearch, familyStatus])

  useEffect(() => {
    let active = true
    queueMicrotask(() => { if (active) void loadCatalog() })
    return () => { active = false }
  }, [loadCatalog])

  useEffect(() => {
    if (!(createOpen || selectedFamily || detailLoading || createStyleOpen)) return
    const returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSelectedFamily(null)
        setCreateOpen(false)
        setCreateStyleOpen(false)
        return
      }
      if (event.key === 'Tab') {
        const dialog = document.querySelector('.global-family-drawer, .catalog-dialog')
        const focusable = dialog?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [href], [tabindex]:not([tabindex="-1"])')
        if (!focusable?.length) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
      }
    }
    document.addEventListener('keydown', onKeyDown)
    closeSurfaceRef.current?.focus()
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      if (returnFocus?.isConnected) returnFocus.focus()
    }
  }, [createOpen, selectedFamily, detailLoading, createStyleOpen])

  function resetFamilyForm() {
    setCode('')
    setTranslations({ en: { name: '', description: '' }, 'ar-KW': { name: '', description: '' }, bn: { name: '', description: '' }, ur: { name: '', description: '' } })
    setShowExtraTranslations(false)
    setShowDescriptions(false)
  }

  function translationPayload() {
    return LOCALES.flatMap(locale => {
      const value = translations[locale]
      if (!value.name.trim()) return []
      return [{ locale, name: value.name.trim(), ...(value.description.trim() ? { description: value.description.trim() } : {}) }]
    })
  }

  async function openFamily(familyId: string) {
    setDetailLoading(true)
    setError(null)
    try {
      const detail = await getFamilyDetail(familyId)
      setSelectedFamily(detail)
      setSelectedGroupIds(detail.option_groups.map(group => group.id))
      const values = { en: { name: '', description: '' }, 'ar-KW': { name: '', description: '' }, bn: { name: '', description: '' }, ur: { name: '', description: '' } }
      for (const item of detail.translations) values[item.locale] = { name: item.name, description: item.description ?? '' }
      setTranslations(values)
      setShowExtraTranslations(detail.translations.some(item => item.locale !== 'en'))
      setShowDescriptions(detail.translations.some(item => Boolean(item.description)))
    } catch (loadError) {
      setError(errorMessage(loadError))
    } finally {
      setDetailLoading(false)
    }
  }

  async function submitFamily(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSaving(true)
    setError(null)
    try {
      if (selectedFamily) {
        await updateGlobalFamily(selectedFamily.id, translationPayload())
        await updateFamilyOptionGroups(selectedFamily.id, selectedGroupIds)
        await openFamily(selectedFamily.id)
        setNotice(t('globalCatalog.saved', 'Family changes saved.'))
      } else {
        await createGlobalFamily({ code: code.trim(), translations: translationPayload() })
        setCreateOpen(false)
        resetFamilyForm()
        setNotice(t('globalCatalog.created', 'Garment family created.'))
      }
      await loadCatalog()
    } catch (saveError) {
      setError(errorMessage(saveError))
    } finally {
      setIsSaving(false)
    }
  }

  async function changeStatus(active: boolean) {
    if (!selectedFamily) return
    const message = active
      ? t('globalCatalog.confirmReactivate', 'Reactivate this garment family?')
      : t('globalCatalog.confirmArchive', 'Archive this garment family? Existing historical records will be preserved.')
    if (!window.confirm(message)) return
    setIsSaving(true)
    setError(null)
    try {
      const updated = await setGlobalFamilyStatus(selectedFamily.id, active)
      setSelectedFamily({ ...selectedFamily, status: updated.status })
      setNotice(active ? t('globalCatalog.reactivated', 'Family reactivated.') : t('globalCatalog.archived', 'Family archived.'))
      await loadCatalog()
    } catch (saveError) {
      setError(errorMessage(saveError))
    } finally {
      setIsSaving(false)
    }
  }

  async function uploadImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file || !selectedFamily) return
    setImageBusy(true)
    setError(null)
    try {
      const metadata = await uploadGlobalFamilyImage(selectedFamily.id, file)
      const imageUrl = metadata.image_content_url ? `${metadata.image_content_url}?v=${Date.now()}` : null
      setSelectedFamily({ ...selectedFamily, has_image: metadata.has_image, image_content_url: imageUrl })
      await loadCatalog()
    } catch (uploadError) {
      setError(errorMessage(uploadError))
    } finally {
      setImageBusy(false)
      event.target.value = ''
    }
  }

  async function removeImage() {
    if (!selectedFamily) return
    setImageBusy(true)
    setError(null)
    try {
      await removeGlobalFamilyImage(selectedFamily.id)
      setSelectedFamily({ ...selectedFamily, has_image: false, image_content_url: null })
      await loadCatalog()
    } catch (removeError) {
      setError(errorMessage(removeError))
    } finally {
      setImageBusy(false)
    }
  }

  async function submitStyle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!styleGroupId) return
    setIsSaving(true)
    setError(null)
    const data: ShopStyleOptionInputRequest = { option_group_id: styleGroupId, code: styleCode.trim(), translations: [{ locale: 'en', name: styleName.trim() }] }
    try {
      const created = await createGlobalStyleOption(data)
      setCreateStyleOpen(false)
      setStyleName('')
      setStyleCode('')
      setNewStyleImages([])
      let imageUploadError: unknown = null
      if (newStyleImages.length) {
        try {
          await uploadGlobalStyleOptionImages(created.id, newStyleImages)
          setNotice(t('globalCatalog.styleCreatedWithImages', 'Style option created and reference images uploaded.'))
        } catch (uploadError) {
          imageUploadError = uploadError
        }
      } else {
        setNotice(t('globalCatalog.styleCreated', 'Style option created.'))
      }
      await loadCatalog()
      if (imageUploadError) setError(t('globalCatalog.styleImageUploadFailed', 'Style option was created, but its image upload failed: {{message}}', { message: errorMessage(imageUploadError) }))
    } catch (saveError) {
      setError(errorMessage(saveError))
    } finally {
      setIsSaving(false)
    }
  }

  async function uploadStyleImages(option: StyleOption, event: ChangeEvent<HTMLInputElement>) {
    const files = event.target.files?.[0] ? [event.target.files[0]] : []
    if (!files.length) return
    setStyleImageBusyId(option.id)
    setError(null)
    setNotice(null)
    try {
      await uploadGlobalStyleOptionImages(option.id, files)
      setNotice(t('globalCatalog.styleImagesUploaded', 'Reference images uploaded for {{name}}.', { name: option.name }))
      await loadCatalog()
    } catch (uploadError) {
      setError(errorMessage(uploadError))
    } finally {
      setStyleImageBusyId(null)
      event.target.value = ''
    }
  }

  function moveGroup(index: number, direction: -1 | 1) {
    const nextIndex = index + direction
    if (nextIndex < 0 || nextIndex >= selectedGroupIds.length) return
    setSelectedGroupIds(current => {
      const next = [...current]
      ;[next[index], next[nextIndex]] = [next[nextIndex], next[index]]
      return next
    })
  }

  const groupsById = new Map(groups.map(group => [group.id, group]))
  const groupNames = new Map(groups.map(group => [group.id, group.name]))

  return (
    <div className="content-wrap global-catalog-page">
      <div className="catalog-heading"><div><h1>{t('globalCatalog.title', 'Global Catalog')}</h1><p>{t('globalCatalog.subtitle', 'Manage shared garment families, option groups and style defaults.')}</p></div>{activeTab === 'families' ? <button className="primary-button" onClick={() => { resetFamilyForm(); setSelectedFamily(null); setCreateOpen(true) }}><Plus size={16} /> {t('globalCatalog.newFamily', 'New Family')}</button> : activeTab === 'styles' ? <button className="primary-button" onClick={() => { setStyleGroupId(groups[0]?.id ?? ''); setCreateStyleOpen(true) }} disabled={!groups.length}><Plus size={16} /> {t('globalCatalog.newStyle', 'New Style Option')}</button> : null}</div>
      <div className="catalog-info-note"><AlertCircle size={17} /> {t('globalCatalog.scopeNote', 'Global garment families, groups and templates are managed here by Main Supplier. Shops can browse the families assigned to them.')}</div>
      {notice && <div className="catalog-success" role="status">{notice}<button type="button" aria-label={t('globalCatalog.dismiss', 'Dismiss')} onClick={() => setNotice(null)}><X size={16} /></button></div>}
      {error && <div className="catalog-error" role="alert">{error}<button type="button" onClick={() => { setIsLoading(true); setError(null); void loadCatalog() }} disabled={isLoading}>{t('globalCatalog.retry', 'Retry')}</button></div>}
      <div className="catalog-tabs" role="tablist" aria-label={t('globalCatalog.sections', 'Global catalog sections')}>
        {(['families', 'variants', 'groups', 'styles'] as const).map(tab => <button key={tab} role="tab" aria-selected={activeTab === tab} className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>{tab === 'families' ? t('globalCatalog.families', 'Garment Families') : tab === 'variants' ? t('globalCatalog.variants', 'Variants') : tab === 'groups' ? t('globalCatalog.groups', 'Option Groups') : t('globalCatalog.styles', 'Style Options')}</button>)}
      </div>
      {activeTab === 'variants' && <VariantsPanel families={activeVariantFamilies} />}
      {activeTab === 'families' && <div className="catalog-family-toolbar"><label className="catalog-search"><Search size={17} aria-hidden="true" /><span className="sr-only">{t('globalCatalog.searchLabel', 'Search garment families')}</span><input type="search" value={familySearchInput} onChange={event => setFamilySearchInput(event.target.value)} placeholder={t('globalCatalog.searchPlaceholder', 'Search by family name or code')} /></label><div className="global-family-status-filter" role="group" aria-label={t('globalCatalog.status', 'Status')}>{(['ACTIVE', 'ARCHIVED', 'all'] as const).map(status => <button type="button" key={status} className={familyStatus === status ? 'active' : ''} aria-pressed={familyStatus === status} onClick={() => { setFamilyStatus(status); setFamilyPage(1); setIsLoading(true) }}>{status === 'ACTIVE' ? t('globalCatalog.active', 'Active') : status === 'ARCHIVED' ? t('globalCatalog.archivedFilter', 'Archived') : t('globalCatalog.allStatuses', 'All')}</button>)}</div><span className="catalog-family-count">{familyCount} {t('globalCatalog.familyCount', 'families')}</span></div>}
      {isLoading ? <div className="catalog-loading"><Loader2 className="animate-spin" /></div> : <div className="catalog-grid">
        {activeTab === 'families' && families.map(family => <button type="button" className="catalog-card catalog-family-card" key={family.id} onClick={() => void openFamily(family.id)}><Shirt size={20} aria-hidden="true" /><span><strong>{family.name}</strong><small>{family.code}</small></span><span className={`catalog-tag ${family.status === 'ARCHIVED' ? 'catalog-tag-muted' : ''}`}>{family.status === 'ARCHIVED' ? t('globalCatalog.archivedFilter', 'Archived') : t('globalCatalog.active', 'Active')}</span><ChevronRight size={16} aria-hidden="true" /></button>)}
        {activeTab === 'groups' && groups.map(group => <article className="catalog-card" key={group.id}><ListTree size={20} /><div><strong>{group.name}</strong><small>{group.code}</small></div></article>)}
        {activeTab === 'styles' && styleOptions.map(option => <article className="catalog-card" key={option.id}><Shirt size={20} /><div><strong>{option.name}</strong><small>{groupNames.get(option.option_group) ?? option.option_group} · {option.code}</small><small>{t('globalCatalog.referenceImageCount', '{{count}} current image', { count: option.reference_images?.length ?? 0 })}</small></div><span className="catalog-tag">{option.is_active ? t('globalCatalog.active', 'Active') : t('globalCatalog.inactive', 'Inactive')}</span><label className="secondary-button global-upload-button">{styleImageBusyId === option.id ? <Loader2 className="animate-spin" size={15} /> : <ImagePlus size={15} />}{t('globalCatalog.addImage', 'Add or replace image')}<input aria-label={t('globalCatalog.addImageFor', 'Add image for {{name}}', { name: option.name })} type="file" accept="image/jpeg,image/png,image/webp" hidden disabled={styleImageBusyId === option.id} onChange={event => void uploadStyleImages(option, event)} /></label></article>)}
        {activeTab === 'families' && families.length === 0 && <p className="catalog-empty">{t('globalCatalog.noFamilies', 'No garment families found.')}</p>}
        {activeTab === 'groups' && groups.length === 0 && <p className="catalog-empty">{t('globalCatalog.noGroups', 'No option groups found.')}</p>}
        {activeTab === 'styles' && styleOptions.length === 0 && <p className="catalog-empty">{t('globalCatalog.noStyles', 'No global style options found.')}</p>}
      </div>}
      {activeTab === 'families' && !isLoading && (familyHasPrevious || familyHasNext) && <nav className="catalog-family-pagination" aria-label={t('globalCatalog.familyPages', 'Family pages')}><button className="secondary-button" type="button" disabled={!familyHasPrevious} onClick={() => { setFamilyPage(page => page - 1); setIsLoading(true) }}><ChevronLeft size={16} /> {t('globalCatalog.previous', 'Previous')}</button><span>{t('globalCatalog.page', 'Page {{page}}', { page: familyPage })}</span><button className="secondary-button" type="button" disabled={!familyHasNext} onClick={() => { setFamilyPage(page => page + 1); setIsLoading(true) }}>{t('globalCatalog.next', 'Next')} <ChevronRight size={16} /></button></nav>}

      {(createOpen || selectedFamily || detailLoading) && <div className="catalog-family-drawer-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) { setSelectedFamily(null); setCreateOpen(false) } }}><section className="catalog-family-drawer global-family-drawer" role="dialog" aria-modal="true" aria-labelledby="global-family-title">
        <div className="catalog-family-drawer-header"><div className="catalog-family-drawer-identity">{familyImage.objectUrl ? <img src={familyImage.objectUrl} alt="" /> : <Shirt size={22} aria-hidden="true" />}<div><h2 id="global-family-title">{selectedFamily?.name ?? (createOpen ? t('globalCatalog.newFamily', 'New Family') : t('globalCatalog.loadingFamily', 'Garment family'))}</h2><small>{selectedFamily?.code ?? (createOpen ? t('globalCatalog.newFamilyHint', 'Create a family and assign its style groups.') : '')}</small></div></div><button ref={closeSurfaceRef} type="button" className="catalog-icon-button" aria-label={t('globalCatalog.close', 'Close')} onClick={() => { setSelectedFamily(null); setCreateOpen(false) }}><X size={18} /></button></div>
        {detailLoading ? <div className="catalog-loading"><Loader2 className="animate-spin" /></div> : <>
          {selectedFamily && <div className="global-family-image-tools"><div className="global-family-preview">{familyImage.objectUrl ? <img src={familyImage.objectUrl} alt={t('globalCatalog.familyImageAlt', 'Garment family reference')} /> : <ImagePlus size={26} aria-hidden="true" />}</div><div><strong>{t('globalCatalog.referenceImage', 'Reference image')}</strong><small>{t('globalCatalog.imageHint', 'Optional JPEG, PNG or WebP image.')}</small><label className="secondary-button global-upload-button"><ImagePlus size={15} />{imageBusy ? t('globalCatalog.uploading', 'Uploading…') : selectedFamily.has_image ? t('globalCatalog.replaceImage', 'Replace image') : t('globalCatalog.uploadImage', 'Upload image')}<input type="file" accept="image/jpeg,image/png,image/webp" onChange={event => void uploadImage(event)} disabled={imageBusy} /></label></div>{selectedFamily.has_image && <button type="button" className="catalog-icon-button" aria-label={t('globalCatalog.removeImage', 'Remove image')} onClick={() => void removeImage()} disabled={imageBusy}><Trash2 size={16} /></button>}</div>}
          <form className="catalog-dialog global-family-form" onSubmit={event => void submitFamily(event)}>
            {!selectedFamily && <label>{t('globalCatalog.code', 'Code')}<input required maxLength={64} pattern="[a-zA-Z0-9_-]+" value={code} onChange={event => setCode(event.target.value)} /><small>{t('globalCatalog.codeHint', 'Use letters, numbers, hyphens, or underscores.')}</small></label>}
            {selectedFamily && <label>{t('globalCatalog.code', 'Code')}<input value={selectedFamily.code} readOnly /></label>}
            <label>{t('globalCatalog.nameEnglish', 'Name (English)')}<input required maxLength={120} value={translations.en.name} onChange={event => setTranslations(current => ({ ...current, en: { ...current.en, name: event.target.value } }))} /></label>
            <button className="global-disclosure" type="button" aria-expanded={showExtraTranslations} onClick={() => setShowExtraTranslations(value => !value)}><ChevronDown size={16} />{t('globalCatalog.otherLanguages', 'Other languages (optional)')}</button>
            {showExtraTranslations && LOCALES.filter(locale => locale !== 'en').map(locale => <label key={locale}>{locale}<input required={Boolean(selectedFamily?.translations.some(item => item.locale === locale))} maxLength={120} value={translations[locale].name} onChange={event => setTranslations(current => ({ ...current, [locale]: { ...current[locale], name: event.target.value } }))} /></label>)}
            <button className="global-disclosure" type="button" aria-expanded={showDescriptions} onClick={() => setShowDescriptions(value => !value)}><ChevronDown size={16} />{t('globalCatalog.descriptions', 'Descriptions (optional)')}</button>
            {showDescriptions && LOCALES.filter(locale => locale === 'en' || translations[locale].name.trim()).map(locale => <label key={locale}>{t('globalCatalog.descriptionLanguage', '{{locale}} description', { locale })}<textarea rows={2} maxLength={500} value={translations[locale].description} onChange={event => setTranslations(current => ({ ...current, [locale]: { ...current[locale], description: event.target.value } }))} /></label>)}
            {selectedFamily && <fieldset className="global-family-groups-fieldset"><legend>{t('globalCatalog.applicableGroups', 'Applicable option groups')}</legend><small>{t('globalCatalog.groupsHint', 'Choose groups shown for this family in Shop catalog.')}</small>{selectedGroupIds.map((id, index) => { const group = groupsById.get(id); return group ? <div className="global-family-group-row" key={id}><span>{group.name}<small>{group.code}</small></span><button type="button" className="catalog-icon-button" aria-label={t('globalCatalog.moveUp', 'Move up')} disabled={index === 0} onClick={() => moveGroup(index, -1)}><ChevronUp size={16} /></button><button type="button" className="catalog-icon-button" aria-label={t('globalCatalog.moveDown', 'Move down')} disabled={index === selectedGroupIds.length - 1} onClick={() => moveGroup(index, 1)}><ChevronDown size={16} /></button><button type="button" className="catalog-icon-button" aria-label={t('globalCatalog.removeGroup', 'Remove group')} onClick={() => setSelectedGroupIds(ids => ids.filter(item => item !== id))}><X size={16} /></button></div> : null })}<label>{t('globalCatalog.addGroup', 'Add option group')}<select value="" onChange={event => { const id = event.target.value; if (id && !selectedGroupIds.includes(id)) setSelectedGroupIds(ids => [...ids, id]) }}><option value="">{t('globalCatalog.selectGroup', 'Select a group')}</option>{groups.filter(group => !selectedGroupIds.includes(group.id)).map(group => <option value={group.id} key={group.id}>{group.name} · {group.code}</option>)}</select></label></fieldset>}
            <div className="catalog-dialog-actions"><button type="button" className="secondary-button" onClick={() => { setSelectedFamily(null); setCreateOpen(false) }}>{t('globalCatalog.close', 'Close')}</button><button type="submit" className="primary-button" disabled={isSaving || !translations.en.name.trim()}>{isSaving ? <Loader2 size={16} className="animate-spin" /> : null} {selectedFamily ? t('globalCatalog.save', 'Save changes') : t('globalCatalog.createFamily', 'Create Family')}</button></div>
          </form>
          {selectedFamily && <div className="global-family-lifecycle"><span className={`catalog-tag ${selectedFamily.status === 'ARCHIVED' ? 'catalog-tag-muted' : ''}`}>{selectedFamily.status === 'ARCHIVED' ? t('globalCatalog.archivedFilter', 'Archived') : t('globalCatalog.active', 'Active')}</span><button type="button" className="secondary-button" disabled={isSaving} onClick={() => void changeStatus(selectedFamily.status === 'ARCHIVED')}>{selectedFamily.status === 'ARCHIVED' ? t('globalCatalog.reactivate', 'Reactivate') : t('globalCatalog.archive', 'Archive')}</button></div>}
        </>}
      </section></div>}

      {createStyleOpen && <div className="catalog-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setCreateStyleOpen(false) }}><form className="catalog-dialog" role="dialog" aria-modal="true" onSubmit={event => void submitStyle(event)} aria-labelledby="global-style-create-title"><div className="catalog-dialog-heading"><h2 id="global-style-create-title">{t('globalCatalog.createStyleTitle', 'Create global style option')}</h2><button ref={closeSurfaceRef} type="button" className="catalog-icon-button" onClick={() => setCreateStyleOpen(false)} aria-label={t('globalCatalog.close', 'Close')}><X size={18} /></button></div><label>{t('globalCatalog.nameEnglish', 'Name (English)')}<input required maxLength={120} value={styleName} onChange={event => setStyleName(event.target.value)} /></label><label>{t('globalCatalog.code', 'Code')}<input required maxLength={64} pattern="[a-zA-Z0-9_-]+" value={styleCode} onChange={event => setStyleCode(event.target.value)} /></label><label>{t('globalCatalog.groups', 'Option group')}<select required value={styleGroupId} onChange={event => setStyleGroupId(event.target.value)}>{groups.map(group => <option key={group.id} value={group.id}>{group.name}</option>)}</select></label><label>{t('globalCatalog.referenceImageOptional', 'Reference image (optional)')}<input type="file" accept="image/jpeg,image/png,image/webp" onChange={event => setNewStyleImages(event.target.files?.[0] ? [event.target.files[0]] : [])} /><small>{t('globalCatalog.referenceImagesR2Hint', 'One image uploads privately to R2 after the style option is created.')}</small></label><div className="catalog-dialog-actions"><button type="button" className="secondary-button" onClick={() => setCreateStyleOpen(false)}>{t('globalCatalog.cancel', 'Cancel')}</button><button className="primary-button" type="submit" disabled={isSaving || groups.length === 0}>{isSaving ? <Loader2 size={16} className="animate-spin" /> : null} {t('globalCatalog.create', 'Create')}</button></div></form></div>}
    </div>
  )
}
