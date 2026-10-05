import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { usePrivateImage } from '../../hooks/usePrivateImage'
import { ApiError } from '../../services/apiClient'
import { createShopStyleOption, createShopVariant, getAllFamilies, getAllShopStyleOptions, getFamilyDetail, getFamilies, getOptionGroups, updateShopStyleOptionTranslations, uploadShopStyleOptionImages } from './api'
import type { CatalogFamily, CatalogFamilyDetail, OptionGroup, StyleOption } from './types'
import { VariantsPanel } from './VariantsPanel'
import { AlertCircle, ArrowRight, Check, ChevronDown, ChevronLeft, ChevronRight, ImagePlus, Layers3, Loader2, Plus, Search, Shirt, X } from 'lucide-react'
import './Catalog.css'

type Tab = 'families' | 'variants' | 'styles'
type CreateKind = 'variant' | 'style' | null
type FailedStyleUpload = { optionId: string; files: File[] }

function ShopFamilyCard({ family, onOpen }: { family: CatalogFamily; onOpen: (familyId: string) => void }) {
  const image = usePrivateImage(family.image_content_url)
  return <button className="catalog-card catalog-family-card" type="button" onClick={() => onOpen(family.id)}>
    {image.objectUrl ? <img className="catalog-family-thumbnail" src={image.objectUrl} alt="" /> : <Shirt size={20} aria-hidden="true" />}
    <span><strong>{family.name}</strong><small>{family.code}</small></span><ArrowRight size={17} aria-hidden="true" />
  </button>
}

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : 'Could not load the catalog. Please try again.'
}

function StyleReferenceThumbnail({ image }: { image: StyleOption['reference_images'][number] }) {
  const privateImage = usePrivateImage(image.content_url)
  return <div className="catalog-style-reference" aria-label={image.alt_text || 'Style reference image'}>
    {privateImage.objectUrl ? <img src={privateImage.objectUrl} alt={image.alt_text || 'Style reference'} loading="lazy" /> : <ImagePlus size={22} aria-hidden="true" />}
  </div>
}

export function CatalogPage() {
  const { t } = useTranslation()
  const { shopId, role, isLoading: isShopLoading } = useCurrentShop()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedTab = searchParams.get('tab')
  const activeTab: Tab = requestedTab === 'variants' || requestedTab === 'styles' ? requestedTab : 'families'
  const [familyPage, setFamilyPage] = useState(1)
  const [familySearchInput, setFamilySearchInput] = useState('')
  const [familySearch, setFamilySearch] = useState('')
  const [familyCount, setFamilyCount] = useState(0)
  const [familyHasNext, setFamilyHasNext] = useState(false)
  const [familyHasPrevious, setFamilyHasPrevious] = useState(false)
  const [openedFamily, setOpenedFamily] = useState<CatalogFamilyDetail | null>(null)
  const [isFamilyDetailLoading, setIsFamilyDetailLoading] = useState(false)
  const [familyDetailError, setFamilyDetailError] = useState<string | null>(null)
  const [expandedGroupId, setExpandedGroupId] = useState<string | null>(null)
  const [families, setFamilies] = useState<CatalogFamily[]>([])
  const [groups, setGroups] = useState<OptionGroup[]>([])
  const [styleOptions, setStyleOptions] = useState<StyleOption[]>([])
  const [selectedStyleId, setSelectedStyleId] = useState<string | null>(null)
  const [editStyleName, setEditStyleName] = useState('')
  const [isStyleSaving, setIsStyleSaving] = useState(false)
  const [styleUploadProgress, setStyleUploadProgress] = useState<number | null>(null)
  const [styleNotice, setStyleNotice] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createKind, setCreateKind] = useState<CreateKind>(null)
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [selectedFamily, setSelectedFamily] = useState('')
  const [selectedGroup, setSelectedGroup] = useState('')
  const [newStyleImages, setNewStyleImages] = useState<File[]>([])
  const [failedStyleUpload, setFailedStyleUpload] = useState<FailedStyleUpload | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const closeDrawerRef = useRef<HTMLButtonElement>(null)
  const familyFilter = searchParams.get('family') || ''
  const groupFilter = searchParams.get('option_group') || ''
  const familyImage = usePrivateImage(openedFamily?.image_content_url)
  const selectedStyle = styleOptions.find(option => option.id === selectedStyleId) ?? null

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setFamilyPage(1)
      setFamilySearch(familySearchInput.trim())
    }, 250)
    return () => window.clearTimeout(timer)
  }, [familySearchInput])

  useEffect(() => {
    const isOpen = Boolean(openedFamily || isFamilyDetailLoading || familyDetailError || createKind)
    if (!isOpen) return
    const returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpenedFamily(null)
        setCreateKind(null)
        return
      }
      if (event.key === 'Tab') {
        const dialog = document.querySelector('.catalog-family-drawer, .catalog-dialog')
        const focusable = dialog?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [href], [tabindex]:not([tabindex="-1"])')
        if (!focusable?.length) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
      }
    }
    document.addEventListener('keydown', onKeyDown)
    closeDrawerRef.current?.focus()
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      if (returnFocus?.isConnected) returnFocus.focus()
    }
  }, [openedFamily, isFamilyDetailLoading, familyDetailError, createKind])

  const loadCatalog = useCallback(async () => {
    if (!shopId) return
    try {
      const [familyResult, groupRows, optionRows] = await Promise.all([
        activeTab === 'families' ? getFamilies(familyPage, familySearch) : activeTab === 'variants' ? getAllFamilies() : Promise.resolve([]),
        activeTab === 'styles' ? getOptionGroups() : Promise.resolve([]),
        activeTab === 'styles' ? getAllShopStyleOptions(shopId, groupFilter || undefined) : Promise.resolve([]),
      ])
      const familyRows = Array.isArray(familyResult) ? familyResult : familyResult.results
      if (!Array.isArray(familyResult)) {
        setFamilyCount(familyResult.count)
        setFamilyHasNext(Boolean(familyResult.next))
        setFamilyHasPrevious(Boolean(familyResult.previous))
      }
      setError(null)
      setFamilies(familyRows)
      setGroups(groupRows)
      if (activeTab === 'styles') {
        setStyleOptions(optionRows)
      }
    } catch (loadError) {
      setError(errorMessage(loadError))
    } finally {
      setIsLoading(false)
    }
  }, [activeTab, familyPage, familySearch, groupFilter, shopId])

  useEffect(() => {
    let active = true
    if (!isShopLoading && shopId) queueMicrotask(() => { if (active) { setIsLoading(true); void loadCatalog() } })
    return () => { active = false }
  }, [activeTab, familyPage, familySearch, familyFilter, groupFilter, shopId, isShopLoading, loadCatalog])

  const optionsByGroup = useMemo(() => {
    const grouped = new Map<string, StyleOption[]>()
    for (const option of styleOptions) {
      const groupOptions = grouped.get(option.option_group) ?? []
      groupOptions.push(option)
      grouped.set(option.option_group, groupOptions)
    }
    return grouped
  }, [styleOptions])

  function openCreate(kind: Exclude<CreateKind, null>, groupId?: string) {
    setCreateKind(kind)
    setName('')
    setCode('')
    setSelectedFamily(families[0]?.id ?? '')
    setSelectedGroup(groupId ?? groups[0]?.id ?? '')
    setNewStyleImages([])
  }

  function selectStyle(option: StyleOption) {
    setSelectedStyleId(option.id)
    setEditStyleName(option.name)
    setStyleNotice(null)
  }

  async function saveStyleName() {
    if (!shopId || !selectedStyle || selectedStyle.is_global || role === 'VIEWER' || !editStyleName.trim()) return
    setIsStyleSaving(true)
    setError(null)
    try {
      const updated = await updateShopStyleOptionTranslations(shopId, selectedStyle.id, [{ locale: 'en', name: editStyleName.trim() }])
      setStyleOptions(current => current.map(option => option.id === updated.id ? { ...option, ...updated } : option))
      setEditStyleName(updated.name || editStyleName.trim())
      setStyleNotice(t('catalog.styleSaved', 'Style option name saved.'))
    } catch (saveError) {
      setError(errorMessage(saveError))
    } finally {
      setIsStyleSaving(false)
    }
  }

  async function uploadStyleReferences(files: FileList | null) {
    if (!shopId || !selectedStyle || selectedStyle.is_global || role === 'VIEWER' || !files?.length) return
    setStyleUploadProgress(0)
    setStyleNotice(null)
    setError(null)
    try {
      const addedImages = await uploadShopStyleOptionImages(shopId, selectedStyle.id, Array.from(files), (_index, percent) => setStyleUploadProgress(percent))
      setStyleOptions(current => current.map(option => option.id === selectedStyle.id
        ? { ...option, reference_images: [...option.reference_images, ...addedImages] }
        : option))
      setStyleNotice(t('catalog.styleImagesUploaded', 'Reference images uploaded successfully.'))
    } catch (uploadError) {
      setError(errorMessage(uploadError))
    } finally {
      setStyleUploadProgress(null)
    }
  }

  async function openFamily(familyId: string) {
    setIsFamilyDetailLoading(true)
    setFamilyDetailError(null)
    setOpenedFamily(null)
    try {
      setOpenedFamily(await getFamilyDetail(familyId))
    } catch (loadError) {
      setFamilyDetailError(errorMessage(loadError))
    } finally {
      setIsFamilyDetailLoading(false)
    }
  }

  function browseVariants(familyId: string) {
    setOpenedFamily(null)
    setSearchParams({ tab: 'variants', family: familyId })
  }

  function browseStyles(groupId: string) {
    setOpenedFamily(null)
    setExpandedGroupId(groupId)
    setSearchParams({ tab: 'styles', option_group: groupId })
  }

  function browseDesigns(familyId: string) {
    navigate(`/designs?family=${encodeURIComponent(familyId)}`)
  }

  async function retryFailedStyleUpload() {
    if (!shopId || !failedStyleUpload) return
    setIsSaving(true)
    setError(null)
    try {
      await uploadShopStyleOptionImages(shopId, failedStyleUpload.optionId, failedStyleUpload.files)
      setFailedStyleUpload(null)
      await loadCatalog()
    } catch (uploadError) {
      setError(t('catalog.styleImageUploadFailed', 'Style option was created, but its image upload failed: {{message}}', { message: errorMessage(uploadError) }))
    } finally {
      setIsSaving(false)
    }
  }

  async function submitCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!shopId || !createKind) return
    setIsSaving(true)
    setError(null)
    setIsLoading(true)
    try {
      const translations = [{ locale: 'en' as const, name: name.trim() }]
      if (createKind === 'variant') {
        await createShopVariant(shopId, { family_id: selectedFamily, code: code.trim(), translations })
      } else {
        const created = await createShopStyleOption(shopId, { option_group_id: selectedGroup, code: code.trim(), translations })
        setExpandedGroupId(selectedGroup)
        let imageUploadError: unknown = null
        if (newStyleImages.length) {
          try {
            await uploadShopStyleOptionImages(shopId, created.id, newStyleImages)
          } catch (uploadError) {
            imageUploadError = uploadError
          }
        }
        setCreateKind(null)
        setFailedStyleUpload(imageUploadError ? { optionId: created.id, files: newStyleImages } : null)
        setNewStyleImages([])
        await loadCatalog()
        if (imageUploadError) {
          setError(t('catalog.styleImageUploadFailed', 'Style option was created, but its image upload failed: {{message}}', { message: errorMessage(imageUploadError) }))
        }
        return
      }
      setCreateKind(null)
      await loadCatalog()
    } catch (saveError) {
      setError(errorMessage(saveError))
      setIsLoading(false)
    } finally {
      setIsSaving(false)
    }
  }

  if (isShopLoading) return <div className="content-wrap catalog-loading"><Loader2 className="animate-spin" /></div>
  if (!shopId) return <div className="content-wrap catalog-message"><AlertCircle /> {t('catalog.noShop', 'No shop context found.')}</div>

  return (
    <div className="content-wrap catalog-page">
      <div className="catalog-heading">
        <div>
          <h1>{t('catalog.title', 'Catalog')}</h1>
          <p>{t('catalog.subtitle', 'Manage your shop variants and style options.')}</p>
        </div>
        {activeTab === 'styles' && <button className="primary-button" onClick={() => openCreate('style')} disabled={!groups.length}><Plus size={16} />{t('catalog.newItem', { item: t('catalog.styleOption', 'Style option') })}</button>}
      </div>

      {error && <div className="catalog-error" role="alert">{error}<button onClick={() => { if (failedStyleUpload) void retryFailedStyleUpload(); else { setIsLoading(true); setError(null); void loadCatalog() } }} disabled={isLoading || isSaving}>Retry</button></div>}

      {activeTab === 'families' && <div className="catalog-family-toolbar"><label className="catalog-search"><Search size={17} aria-hidden="true" /><span className="sr-only">{t('catalog.searchFamilies', 'Search garment families')}</span><input type="search" value={familySearchInput} onChange={event => setFamilySearchInput(event.target.value)} placeholder={t('catalog.searchPlaceholder', 'Search families by name or code')} /></label><span className="catalog-family-count">{t('catalog.familyCount', { count: familyCount })}</span></div>}

      <div className="catalog-tabs" role="tablist" aria-label="Catalog sections">
        {(['families', 'variants', 'styles'] as const).map(tab => <button key={tab} role="tab" aria-selected={activeTab === tab} className={activeTab === tab ? 'active' : ''} onClick={() => { setIsLoading(true); const next = new URLSearchParams(searchParams); next.set('tab', tab); if (tab !== 'variants') next.delete('family'); if (tab !== 'styles') next.delete('option_group'); setSearchParams(next) }}>{tab === 'families' ? t('catalog.families', 'Garment Families') : tab === 'variants' ? t('catalog.variants', 'Variants') : t('catalog.styles', 'Style Options')}</button>)}
      </div>

      {!isLoading && !error && activeTab === 'styles' && !groups.length && <div className="catalog-info-note" role="status"><AlertCircle size={18} /><span>{t('catalog.noGroupsHint', 'No option groups are available for this Shop. Ask your Main Supplier to configure the global catalog.')}</span></div>}
      {!isLoading && !error && activeTab === 'variants' && !families.length && <div className="catalog-info-note" role="status"><AlertCircle size={18} /><span>{t('catalog.noFamiliesHint', 'No garment families are available. Ask your Main Supplier to add them to the global catalog.')}</span></div>}

      {activeTab === 'variants' ? <VariantsPanel shopId={shopId} families={families} initialFamily={familyFilter} canManageVariants={role === 'ADMIN' || role === 'STAFF'} /> : isLoading ? <div className="catalog-loading"><Loader2 className="animate-spin" /></div> : (
        <div className={`catalog-grid${activeTab === 'styles' ? ' catalog-styles-grid' : ''}`}>
        {activeTab === 'families' && families.map(family => <ShopFamilyCard family={family} key={family.id} onOpen={familyId => void openFamily(familyId)} />)}
          {activeTab === 'styles' && <div className={`catalog-style-workspace${selectedStyle ? ' has-selection' : ''}`}>
            <div className={`catalog-group-grid${selectedStyle ? ' catalog-style-list' : ''}`}>
            {groups.filter(group => !groupFilter || group.id === groupFilter).map(group => {
              const groupOptions = optionsByGroup.get(group.id) ?? []
              const isExpanded = expandedGroupId === group.id
              const optionsRegionId = `catalog-group-options-${group.id}`
              return <section className={`catalog-group-card${isExpanded ? ' expanded' : ''}`} key={group.id}>
                <div className="catalog-group-heading">
                  <button
                    className="catalog-group-toggle"
                    type="button"
                    aria-expanded={isExpanded}
                    aria-controls={optionsRegionId}
                    onClick={() => setExpandedGroupId(isExpanded ? null : group.id)}
                  >
                    <Layers3 size={20} aria-hidden="true" />
                    <span><strong>{group.name}</strong><small>{group.code} · {t('catalog.optionCount', { count: groupOptions.length })}</small></span>
                    <ChevronDown size={18} className="catalog-group-chevron" aria-hidden="true" />
                  </button>
                  <button className="catalog-group-add" type="button" onClick={() => openCreate('style', group.id)} aria-label={t('catalog.addOptionTo', { name: group.name })} title={t('catalog.addOptionTo', { name: group.name })}><Plus size={16} /></button>
                </div>
                {isExpanded && <div className="catalog-group-options" id={optionsRegionId}>
                  {groupOptions.length ? groupOptions.map(option => <button className={`catalog-option-card catalog-style-option${selectedStyle?.id === option.id ? ' selected' : ''}`} key={option.id} type="button" aria-pressed={selectedStyle?.id === option.id} onClick={() => selectStyle(option)}>
                    <Shirt size={18} aria-hidden="true" />
                    <div><strong>{option.name}</strong><small>{option.code}</small></div>
                    <span className="catalog-tag">{option.is_global ? t('catalog.global', 'Global') : t('catalog.shop', 'Shop')}</span>
                  </button>) : <div className="catalog-group-empty"><p>{t('catalog.noOptions', 'No options in this group yet.')}</p><button className="secondary-button" type="button" onClick={() => openCreate('style', group.id)}><Plus size={15} /> {t('catalog.addFirstOption', 'Add first option')}</button></div>}
                </div>}
              </section>
            })}
            {!groups.length && !isLoading && <p className="catalog-empty">No option groups found.</p>}
            </div>
            {selectedStyle && <aside className="catalog-style-editor" aria-label={t('catalog.stylePreview', 'Style option preview and editor')}>
              <div className="catalog-style-editor-heading"><div><p>{t('catalog.stylePreview', 'Style option preview')}</p><h2>{selectedStyle.name}</h2></div><button className="catalog-icon-button catalog-style-mobile-close" type="button" onClick={() => setSelectedStyleId(null)} aria-label={t('catalog.backToStyles', 'Back to style options')}><X size={18} /></button></div>
              <p className="catalog-style-code">{selectedStyle.code} · {selectedStyle.is_global ? t('catalog.global', 'Global') : t('catalog.shop', 'Shop')}</p>
              <div className="catalog-style-gallery" aria-label={t('catalog.referenceImages', 'Reference images')}>
                {selectedStyle.reference_images.map(image => <StyleReferenceThumbnail key={image.id} image={image} />)}
                {!selectedStyle.reference_images.length && <p className="catalog-style-empty">{t('catalog.noReferenceImages', 'No reference images have been added yet.')}</p>}
              </div>
              {!selectedStyle.is_global && <div className="catalog-style-edit-form">
                <label>{t('catalog.nameEnglish', 'Name (English)')}<input value={editStyleName} onChange={event => setEditStyleName(event.target.value)} maxLength={120} disabled={role === 'VIEWER'} /></label>
                <button className="primary-button" type="button" onClick={() => void saveStyleName()} disabled={isStyleSaving || !editStyleName.trim() || editStyleName.trim() === selectedStyle.name}>{isStyleSaving ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}{t('catalog.saveStyle', 'Save name')}</button>
                <label className="catalog-style-upload">{t('catalog.addReferenceImages', 'Add reference images')}<input type="file" accept="image/jpeg,image/png,image/webp" multiple disabled={role === 'VIEWER' || styleUploadProgress !== null} onChange={event => { void uploadStyleReferences(event.target.files); event.currentTarget.value = '' }} /></label>
                <small>{t('catalog.styleImageHint', 'Images are added to this Shop style option; existing references are kept.')}</small>
                {styleUploadProgress !== null && <div role="status" className="catalog-style-progress"><span>{t('catalog.uploading', 'Uploading…')} {styleUploadProgress}%</span><progress max="100" value={styleUploadProgress} /></div>}
                {role === 'VIEWER' && <small>{t('catalog.styleReadOnly', 'Your role can view this option but cannot edit or upload.')}</small>}
              </div>}
              {selectedStyle.is_global && <p className="catalog-style-readonly">{t('catalog.globalStyleReadonly', 'Global style defaults are managed by the Main Supplier.')}</p>}
              {styleNotice && <p className="catalog-style-success" role="status"><Check size={16} />{styleNotice}</p>}
            </aside>}
          </div>}
          {!families.length && activeTab === 'families' && !error && <p className="catalog-empty">{familySearch ? <>{t('catalog.noFamilyMatches', 'No families match your search.')} <button type="button" className="catalog-text-button" onClick={() => setFamilySearchInput('')}>{t('catalog.clearSearch', 'Clear search')}</button></> : t('catalog.noFamilies', 'No garment families available.')}</p>}
          {!styleOptions.length && activeTab === 'styles' && !groups.length && !isLoading && !error && <p className="catalog-empty">{t('catalog.noStyles', 'No style options found.')}</p>}
        </div>
      )}

      {activeTab === 'families' && !isLoading && !error && (familyHasPrevious || familyHasNext) && <nav className="catalog-family-pagination" aria-label={t('catalog.familyPages', 'Family pages')}><button className="secondary-button" type="button" disabled={!familyHasPrevious || isLoading} onClick={() => { setFamilyPage(page => page - 1); setIsLoading(true) }}><ChevronLeft size={16} /> {t('catalog.previous', 'Previous')}</button><span>{t('catalog.page', { page: familyPage })}</span><button className="secondary-button" type="button" disabled={!familyHasNext || isLoading} onClick={() => { setFamilyPage(page => page + 1); setIsLoading(true) }}>{t('catalog.next', 'Next')} <ChevronRight size={16} /></button></nav>}

      {(openedFamily || isFamilyDetailLoading || familyDetailError) && <div className="catalog-family-drawer-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setOpenedFamily(null) }}><section className="catalog-family-drawer" role="dialog" aria-modal="true" aria-labelledby="catalog-family-title"><div className="catalog-family-drawer-header"><div className="catalog-family-drawer-identity">{familyImage.objectUrl ? <img src={familyImage.objectUrl} alt="" /> : <Shirt size={22} aria-hidden="true" />}<div><h2 id="catalog-family-title">{openedFamily?.name ?? t('catalog.family', 'Garment family')}</h2><small>{openedFamily?.code}</small></div></div><button ref={closeDrawerRef} type="button" className="catalog-icon-button" aria-label={t('catalog.close', 'Close')} onClick={() => setOpenedFamily(null)}><X size={18} /></button></div>{(isFamilyDetailLoading || familyImage.isLoading) && <p role="status" className="catalog-drawer-muted"><Loader2 size={16} className="animate-spin" /> {t('catalog.loadingDetails', 'Loading family details…')}</p>}{familyDetailError && <p className="catalog-error" role="alert">{familyDetailError}</p>}{openedFamily && <><h3>{t('catalog.applicableGroups', 'Applicable style groups')}</h3><div className="catalog-family-groups">{openedFamily.option_groups.map(group => <button key={group.id} className="catalog-tag catalog-group-chip" type="button" onClick={() => browseStyles(group.id)}>{group.name}</button>)}{openedFamily.option_groups.length === 0 && <span className="catalog-drawer-muted">{t('catalog.noApplicableGroups', 'No style groups are configured for this family.')}</span>}</div><div className="catalog-family-drawer-actions"><button className="secondary-button" type="button" onClick={() => browseVariants(openedFamily.id)}>{t('catalog.viewVariants', 'View Variants')}</button><button className="primary-button" type="button" onClick={() => browseDesigns(openedFamily.id)}>{t('catalog.viewDesigns', 'View Designs')}</button></div></>}</section></div>}

      {createKind && <div className="catalog-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setCreateKind(null) }}>
        <form className="catalog-dialog" role="dialog" aria-modal="true" onSubmit={event => void submitCreate(event)} aria-labelledby="catalog-create-title">
          <div className="catalog-dialog-heading"><h2 id="catalog-create-title">{t('catalog.newItem', { item: createKind === 'variant' ? t('catalog.variant', 'Variant').toLowerCase() : t('catalog.styleOption', 'Style option').toLowerCase() })}</h2><button ref={closeDrawerRef} type="button" className="catalog-icon-button" onClick={() => setCreateKind(null)} aria-label={t('catalog.close', 'Close')}><X size={18} /></button></div>
          <label>{t('catalog.nameEnglish', 'Name (English)')}<input required maxLength={120} value={name} onChange={event => setName(event.target.value)} /></label>
          <label>{t('catalog.code', 'Code')}<input required maxLength={64} pattern="[a-zA-Z0-9_-]+" value={code} onChange={event => setCode(event.target.value)} /><small>{t('catalog.codeHint', 'Use letters, numbers, hyphens, or underscores.')}</small></label>
          {createKind === 'variant' ? <label>{t('catalog.family', 'Garment family')}<select required value={selectedFamily} onChange={event => setSelectedFamily(event.target.value)}>{families.map(family => <option value={family.id} key={family.id}>{family.name}</option>)}</select></label> : <label>{t('catalog.optionGroup', 'Option group')}<select required value={selectedGroup} onChange={event => setSelectedGroup(event.target.value)}>{groups.map(group => <option value={group.id} key={group.id}>{group.name}</option>)}</select></label>}
          {createKind === 'style' && <label>{t('catalog.referenceImagesOptional', 'Reference images (optional)')}<input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={event => setNewStyleImages(Array.from(event.target.files ?? []))} /><small>{t('catalog.referenceImagesR2Hint', 'Images upload privately after the style option is created.')}</small>{newStyleImages.length > 0 && <small>{t('catalog.selectedImageCount', '{{count}} image(s) selected', { count: newStyleImages.length })}</small>}</label>}
          <div className="catalog-dialog-actions"><button type="button" className="secondary-button" onClick={() => setCreateKind(null)}>{t('catalog.cancel', 'Cancel')}</button><button type="submit" className="primary-button" disabled={isSaving || !(createKind === 'variant' ? families.length : groups.length)}>{isSaving ? <Loader2 size={16} className="animate-spin" /> : null} {t('catalog.create', 'Create')}</button></div>
        </form>
      </div>}
    </div>
  )
}
