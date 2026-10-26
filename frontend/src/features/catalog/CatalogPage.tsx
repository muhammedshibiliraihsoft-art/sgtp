import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { handleArrowKeyGrid, handleArrowKeyTabs } from '../../hooks/useArrowKeyGrid'
import { usePrivateImage } from '../../hooks/usePrivateImage'
import { ApiError } from '../../services/apiClient'
import { createShopFamilyOptionGroup, createShopStyleOption, getAllShopFamilies, getAllShopOptionGroups, getAllShopStyleOptions, getShopFamilyOptionGroups, materializeShopDefaultFamily, updateShopFamilyOptionGroups, updateShopStyleOptionTranslations, uploadShopStyleOptionImages } from './api'
import type { CatalogFamily, CatalogFamilyDetail, FamilyOptionGroupConfig, OptionGroup, StyleOption } from './types'
import { ResponsiveChoice } from '../../components/CustomSelect'
import { measurementApi } from '../measurements/api'
import type { MeasurementDefinition } from '../measurements/types'
import { useAuth } from '../../services/useAuth'
import { AlertCircle, ArrowRight, Check, ChevronDown, ImagePlus, Layers3, Loader2, Plus, Search, Shirt, X } from 'lucide-react'
import './Catalog.css'

type Tab = 'families' | 'styles'
type CreateKind = 'style' | 'group' | null
type FailedStyleUpload = { optionId: string; files: File[] }
type DesignDraft = { designName: string; familyId: string }
type CatalogNavigationState = { returnToDesignDraft?: DesignDraft }

function ShopFamilyCard({ family, onOpen }: { family: CatalogFamily; onOpen: (familyId: string) => void }) {
  const image = usePrivateImage(family.image_content_url)
  return <button data-arrow-grid-item className="catalog-card catalog-family-card" type="button" onClick={() => onOpen(family.id)}>
    {image.objectUrl ? <img className="catalog-family-thumbnail" src={image.objectUrl} alt="" /> : <Shirt size={20} aria-hidden="true" />}
    <span><strong>{family.name}</strong><small>{family.code}</small></span><ArrowRight size={17} aria-hidden="true" />
  </button>
}

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : 'Could not load the catalog. Please try again.'
}

function measurementCodeFromName(name: string, definitions: MeasurementDefinition[]) {
  const base = name.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
    .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 64).replace(/-+$/g, '')
  if (!base) return ''
  const usedCodes = new Set(definitions.map(definition => definition.code.toLowerCase()))
  if (!usedCodes.has(base)) return base
  for (let suffix = 2; suffix < 10000; suffix += 1) {
    const candidate = `${base.slice(0, 64 - String(suffix).length - 1).replace(/-+$/g, '')}-${suffix}`
    if (!usedCodes.has(candidate)) return candidate
  }
  return base
}

function StyleReferenceThumbnail({ image }: { image: StyleOption['reference_images'][number] }) {
  const { t } = useTranslation()
  const privateImage = usePrivateImage(image.content_url)
  const [failedObjectUrl, setFailedObjectUrl] = useState<string | null>(null)
  const cannotDisplay = Boolean(privateImage.error || (privateImage.objectUrl && failedObjectUrl === privateImage.objectUrl))
  return <div className="catalog-style-reference" aria-label={image.alt_text || 'Style reference image'}>
    {cannotDisplay ? <div role="status" className="catalog-style-image-error"><span>{t('catalog.imageUnavailable', 'Image unavailable')}</span><button type="button" onClick={() => { setFailedObjectUrl(null); privateImage.retry() }}>{t('catalog.retryImage', 'Retry image')}</button></div>
      : privateImage.objectUrl ? <img src={privateImage.objectUrl} alt={image.alt_text || 'Style reference'} loading="lazy" onError={() => setFailedObjectUrl(privateImage.objectUrl)} />
        : privateImage.isLoading ? <Loader2 size={22} className="animate-spin" aria-label="Loading image" /> : <ImagePlus size={22} aria-hidden="true" />}
  </div>
}

export function CatalogPage() {
  const { t } = useTranslation()
  const { shopId, role, workFunctions, isLoading: isShopLoading } = useCurrentShop()
  const { user } = useAuth()
  const isMainSupplier = user?.is_main_supplier_admin === true
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedTab = searchParams.get('tab')
  const activeTab: Tab = requestedTab === 'styles' ? 'styles' : 'families'
  const [familySearchInput, setFamilySearchInput] = useState('')
  const [familySearch, setFamilySearch] = useState('')
  const [openedFamily, setOpenedFamily] = useState<CatalogFamilyDetail | null>(null)
  const [familyGroupConfigs, setFamilyGroupConfigs] = useState<FamilyOptionGroupConfig[]>([])
  const [isSavingFamilyGroups, setIsSavingFamilyGroups] = useState(false)
  const [measurementDefinitions, setMeasurementDefinitions] = useState<MeasurementDefinition[]>([])
  const [familyMeasurements, setFamilyMeasurements] = useState<MeasurementDefinition[]>([])
  const [measurementDefinitionId, setMeasurementDefinitionId] = useState('')
  const [measurementName, setMeasurementName] = useState('')
  const [measurementCode, setMeasurementCode] = useState('')
  const [measurementGroupCode, setMeasurementGroupCode] = useState('')
  const [isMeasurementCodeEdited, setIsMeasurementCodeEdited] = useState(false)
  const [showNewMeasurementForm, setShowNewMeasurementForm] = useState(false)
  const [isMeasurementLoading, setIsMeasurementLoading] = useState(false)
  const [isMeasurementSaving, setIsMeasurementSaving] = useState(false)
  const [measurementError, setMeasurementError] = useState<string | null>(null)
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
  const [createGroupForFamilyId, setCreateGroupForFamilyId] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [selectedGroup, setSelectedGroup] = useState('')
  const [newStyleImages, setNewStyleImages] = useState<File[]>([])
  const [failedStyleUpload, setFailedStyleUpload] = useState<FailedStyleUpload | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const closeDrawerRef = useRef<HTMLButtonElement>(null)
  const closeCreateDialogRef = useRef<HTMLButtonElement>(null)
  const familyDetailRequestId = useRef(0)
  const createKindRef = useRef<CreateKind>(createKind)
  const drawerOpenRef = useRef(false)
  createKindRef.current = createKind
  drawerOpenRef.current = Boolean(openedFamily || isFamilyDetailLoading || familyDetailError)
  const legacyVariantFamilyOpenedRef = useRef<string | null>(null)
  const autoOpenedFamilyRef = useRef<string | null>(null)
  const groupFilter = searchParams.get('option_group') || ''
  const requestedFamilyId = searchParams.get('family') || ''
  const familyImage = usePrivateImage(openedFamily?.image_content_url)
  const selectedStyle = styleOptions.find(option => option.id === selectedStyleId) ?? null
  const canEditFamilyGroups = Boolean(role !== 'VIEWER' && openedFamily && openedFamily.tenant === shopId && openedFamily.status === 'ACTIVE')
  const canConfigureMeasurements = Boolean(shopId && (isMainSupplier || role === 'ADMIN' || (role === 'STAFF' && workFunctions.includes('MEASUREMENT'))))
  const canEditMeasurements = Boolean(shopId && openedFamily?.tenant === shopId && openedFamily.status === 'ACTIVE' && !isMainSupplier && (role === 'ADMIN' || (role === 'STAFF' && workFunctions.includes('MEASUREMENT'))))
  const returnToDesignDraft = (location.state as CatalogNavigationState | null)?.returnToDesignDraft
  const filteredFamilies = useMemo(() => families.filter(family => !familySearch || family.name.toLocaleLowerCase().includes(familySearch.toLocaleLowerCase()) || family.code.toLocaleLowerCase().includes(familySearch.toLocaleLowerCase())), [families, familySearch])

  function closeFamilyDetails() {
    familyDetailRequestId.current += 1
    setOpenedFamily(null)
    setFamilyDetailError(null)
    setIsFamilyDetailLoading(false)
    setIsMeasurementLoading(false)
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setFamilySearch(familySearchInput.trim())
    }, 250)
    return () => window.clearTimeout(timer)
  }, [familySearchInput])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (createKindRef.current) setCreateKind(null)
        else if (drawerOpenRef.current) closeFamilyDetails()
        else return
        event.preventDefault()
        event.stopPropagation()
        return
      }
      if (event.key === 'Tab') {
        const dialog = document.querySelector(createKindRef.current ? '.catalog-dialog' : '.catalog-family-drawer')
        const focusable = dialog?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [href], [tabindex]:not([tabindex="-1"])')
        if (!focusable?.length) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [])

  useEffect(() => {
    const isDrawerOpen = Boolean(openedFamily || isFamilyDetailLoading || familyDetailError)
    if (!isDrawerOpen) return
    const returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
    closeDrawerRef.current?.focus()
    return () => {
      if (returnFocus?.isConnected) returnFocus.focus()
    }
  }, [Boolean(openedFamily || isFamilyDetailLoading || familyDetailError)])

  useEffect(() => {
    if (!createKind) return
    const returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
    closeCreateDialogRef.current?.focus()
    return () => {
      if (returnFocus?.isConnected) returnFocus.focus()
    }
  }, [createKind])

  const loadCatalog = useCallback(async () => {
    if (!shopId) return
    try {
      const [familyRows, groupRows, optionRows] = await Promise.all([
        activeTab === 'families' ? getAllShopFamilies(shopId, 'en') : Promise.resolve([]),
        getAllShopOptionGroups(shopId, 'en'),
        activeTab === 'styles' ? getAllShopStyleOptions(shopId, groupFilter || undefined) : Promise.resolve([]),
      ])
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
  }, [activeTab, groupFilter, shopId])

  useEffect(() => {
    let active = true
    if (!isShopLoading && shopId) queueMicrotask(() => { if (active) { setIsLoading(true); void loadCatalog() } })
    return () => { active = false }
  }, [activeTab, groupFilter, shopId, isShopLoading, loadCatalog])

  const optionsByGroup = useMemo(() => {
    const grouped = new Map<string, StyleOption[]>()
    for (const option of styleOptions) {
      const groupOptions = grouped.get(option.option_group) ?? []
      groupOptions.push(option)
      grouped.set(option.option_group, groupOptions)
    }
    return grouped
  }, [styleOptions])

  function openCreate(kind: Exclude<CreateKind, null>, groupId?: string, familyId?: string) {
    setCreateKind(kind)
    setCreateGroupForFamilyId(familyId ?? null)
    setName('')
    setCode('')
    setSelectedGroup(groupId ?? groups[0]?.id ?? '')
    setNewStyleImages([])
  }

  function openFamilyGroupCreate(familyId: string) {
    openCreate('group', undefined, familyId)
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
    const requestId = ++familyDetailRequestId.current
    setIsFamilyDetailLoading(true)
    setFamilyDetailError(null)
    setOpenedFamily(null)
    setIsMeasurementLoading(canConfigureMeasurements)
    setFamilyMeasurements([])
    setMeasurementDefinitions([])
    setMeasurementError(null)
    setShowNewMeasurementForm(false)
    setMeasurementName('')
    setMeasurementCode('')
    setMeasurementGroupCode('')
    setIsMeasurementCodeEdited(false)
    try {
      const family = families.find(item => item.id === familyId)
      if (!family) throw new Error('This garment family is no longer available. Refresh the catalog and try again.')
      const [configs, availableGroups, measurementRows] = await Promise.all([
        getShopFamilyOptionGroups(shopId!, familyId),
        getAllShopOptionGroups(shopId!),
        canConfigureMeasurements
          ? Promise.all([
            measurementApi.allDefinitions(shopId!),
            measurementApi.definitions(shopId!, familyId, 'en'),
          ])
          : Promise.resolve(null),
      ])
      if (requestId !== familyDetailRequestId.current) return
      setFamilyGroupConfigs(configs)
      setGroups(availableGroups)
      if (measurementRows) {
        const [allDefinitions, familyRows] = measurementRows
        setMeasurementDefinitions(allDefinitions.filter(definition => !definition.is_global))
        setFamilyMeasurements(familyRows)
      }
      setIsMeasurementLoading(false)
      setOpenedFamily({ ...family, translations: [], option_groups: configs.map(config => config.option_group) })
    } catch (loadError) {
      if (requestId === familyDetailRequestId.current) {
        setIsMeasurementLoading(false)
        setFamilyDetailError(errorMessage(loadError))
      }
    } finally {
      if (requestId === familyDetailRequestId.current) setIsFamilyDetailLoading(false)
    }
  }

  useEffect(() => {
    if (!requestedFamilyId || isLoading || !families.length || autoOpenedFamilyRef.current === requestedFamilyId || openedFamily?.id === requestedFamilyId) return
    if (families.some(family => family.id === requestedFamilyId)) {
      autoOpenedFamilyRef.current = requestedFamilyId
      void openFamily(requestedFamilyId)
    }
  }, [families, isLoading, openedFamily?.id, requestedFamilyId])

  async function saveFamilyGroups() {
    if (!shopId || !openedFamily || !canEditFamilyGroups || isSavingFamilyGroups) return
    setIsSavingFamilyGroups(true)
    setFamilyDetailError(null)
    try {
      const saved = await updateShopFamilyOptionGroups(shopId, openedFamily.id, familyGroupConfigs.map((item, index) => ({
        option_group_id: item.option_group.id,
        selection_mode: item.selection_mode,
        is_required: item.is_required,
        sort_order: index,
      })))
      setFamilyGroupConfigs(saved)
      setOpenedFamily(current => current ? { ...current, option_groups: saved.map(item => item.option_group) } : current)
    } catch (saveError) {
      setFamilyDetailError(errorMessage(saveError))
    } finally {
      setIsSavingFamilyGroups(false)
    }
  }

  async function editGlobalFamilyInShop() {
    if (!shopId || !openedFamily || openedFamily.tenant !== null || role === 'VIEWER' || isSavingFamilyGroups) return
    setIsSavingFamilyGroups(true)
    setFamilyDetailError(null)
    try {
      const localFamily = await materializeShopDefaultFamily(shopId, openedFamily.id)
      const configs = await getShopFamilyOptionGroups(shopId, localFamily.id)
      setFamilies(current => [...current.filter(item => item.id !== openedFamily.id && item.id !== localFamily.id), localFamily])
      setFamilyGroupConfigs(configs)
      setOpenedFamily({ ...localFamily, translations: [], option_groups: configs.map(item => item.option_group) })
    } catch (copyError) {
      setFamilyDetailError(errorMessage(copyError))
    } finally {
      setIsSavingFamilyGroups(false)
    }
  }

  async function reloadFamilyMeasurements() {
    if (!shopId || !openedFamily || !canConfigureMeasurements) return
    const familyRows = await measurementApi.definitions(shopId, openedFamily.id, 'en')
    setFamilyMeasurements(familyRows)
  }

  async function mapMeasurementDefinition() {
    if (!shopId || !openedFamily || !canEditMeasurements || !measurementDefinitionId || isMeasurementSaving) return
    setIsMeasurementSaving(true)
    setMeasurementError(null)
    try {
      await measurementApi.attachDefinitionMapping(
        shopId,
        measurementDefinitionId,
        openedFamily.id,
      )
      setMeasurementDefinitionId('')
      await reloadFamilyMeasurements()
    } catch (saveError) {
      setMeasurementError(errorMessage(saveError))
    } finally {
      setIsMeasurementSaving(false)
    }
  }

  async function createMeasurementDefinition(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!shopId || !openedFamily || !canEditMeasurements || !measurementName.trim() || !measurementCode.trim() || isMeasurementSaving) return
    setIsMeasurementSaving(true)
    setMeasurementError(null)
    try {
      await measurementApi.createDefinition(shopId, {
        code: measurementCode.trim(),
        group_code: measurementGroupCode.trim(),
        sort_order: measurementDefinitions.length
          ? Math.max(...measurementDefinitions.map(definition => definition.sort_order)) + 1
          : 0,
        translations: [{ locale: 'en', name: measurementName.trim() }],
        mappings: [{ family_id: openedFamily.id }],
      })
      setMeasurementName('')
      setMeasurementCode('')
      setMeasurementGroupCode('')
      setIsMeasurementCodeEdited(false)
      setShowNewMeasurementForm(false)
      setMeasurementDefinitions(await measurementApi.allDefinitions(shopId))
      await reloadFamilyMeasurements()
    } catch (saveError) {
      setMeasurementError(errorMessage(saveError))
    } finally {
      setIsMeasurementSaving(false)
    }
  }

  useEffect(() => {
    if (requestedTab !== 'variants') {
      legacyVariantFamilyOpenedRef.current = null
      return
    }
    const legacyFamilyId = searchParams.get('family')
    const next = new URLSearchParams(searchParams)
    next.set('tab', 'families')
    next.delete('family')
    setSearchParams(next, { replace: true })
    if (legacyFamilyId && legacyVariantFamilyOpenedRef.current !== legacyFamilyId) {
      legacyVariantFamilyOpenedRef.current = legacyFamilyId
      void openFamily(legacyFamilyId)
    }
  }, [requestedTab, searchParams, setSearchParams])

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
      if (createKind === 'group' && createGroupForFamilyId) {
        const created = await createShopFamilyOptionGroup(shopId, createGroupForFamilyId, { code: code.trim(), translations })
        setGroups(current => current.some(group => group.id === created.option_group.id) ? current : [...current, created.option_group])
        setFamilyGroupConfigs(current => [...current, created])
        setOpenedFamily(current => current && current.id === createGroupForFamilyId
          ? { ...current, option_groups: current.option_groups.some(group => group.id === created.option_group.id) ? current.option_groups : [...current.option_groups, created.option_group] }
          : current)
        setCreateKind(null)
        setCreateGroupForFamilyId(null)
        setIsLoading(false)
        return
      }
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
          <p>{t('catalog.subtitle', 'Manage garments, style groups, and style options.')}</p>
        </div>
        {activeTab === 'styles' && <button className="primary-button" onClick={() => openCreate('style')} disabled={!groups.length}><Plus size={16} />{t('catalog.newItem', { item: t('catalog.styleOption', 'Style option') })}</button>}
      </div>

      {error && <div className="catalog-error" role="alert">{error}<button onClick={() => { if (failedStyleUpload) void retryFailedStyleUpload(); else { setIsLoading(true); setError(null); void loadCatalog() } }} disabled={isLoading || isSaving}>Retry</button></div>}

      {activeTab === 'families' && <div className="catalog-family-toolbar"><label className="catalog-search"><Search size={17} aria-hidden="true" /><span className="sr-only">{t('catalog.searchFamilies', 'Search garment families')}</span><input type="search" value={familySearchInput} onChange={event => setFamilySearchInput(event.target.value)} placeholder={t('catalog.searchPlaceholder', 'Search families by name or code')} /></label><span className="catalog-family-count">{t('catalog.familyCount', { count: filteredFamilies.length })}</span></div>}

      <div className="catalog-tabs" role="tablist" aria-label="Catalog sections" onKeyDown={handleArrowKeyTabs}>
        {(['families', 'styles'] as const).map(tab => <button key={tab} role="tab" tabIndex={activeTab === tab ? 0 : -1} aria-selected={activeTab === tab} className={activeTab === tab ? 'active' : ''} onClick={() => { setIsLoading(true); const next = new URLSearchParams(searchParams); next.set('tab', tab); next.delete('family'); if (tab !== 'styles') next.delete('option_group'); setSearchParams(next) }}>{tab === 'families' ? t('catalog.families', 'Garment Families') : t('catalog.styles', 'Style Options')}</button>)}
      </div>

      {!isLoading && !error && activeTab === 'styles' && !groups.length && <div className="catalog-info-note" role="status"><AlertCircle size={18} /><span>{t('catalog.noGroupsHint', 'No option groups are available for this Shop. Ask your Main Supplier to configure the global catalog.')}</span></div>}
      {isLoading ? <div className="catalog-loading"><Loader2 className="animate-spin" /></div> : (
        <div className={`catalog-grid${activeTab === 'styles' ? ' catalog-styles-grid' : ''}`} data-arrow-key-grid={activeTab === 'families' ? '' : undefined} onKeyDown={activeTab === 'families' ? handleArrowKeyGrid : undefined}>
        {activeTab === 'families' && filteredFamilies.map(family => <ShopFamilyCard family={family} key={family.id} onOpen={familyId => void openFamily(familyId)} />)}
          {activeTab === 'styles' && <div className={`catalog-style-workspace${selectedStyle ? ' has-selection' : ''}`}>
            <div className={`catalog-group-grid${selectedStyle ? ' catalog-style-list' : ''}`} data-arrow-key-grid onKeyDown={handleArrowKeyGrid}>
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
                {isExpanded && <div className="catalog-group-options" id={optionsRegionId} data-arrow-key-grid onKeyDown={handleArrowKeyGrid}>
                  {groupOptions.length ? groupOptions.map(option => <button data-arrow-grid-item className={`catalog-option-card catalog-style-option${selectedStyle?.id === option.id ? ' selected' : ''}`} key={option.id} type="button" aria-pressed={selectedStyle?.id === option.id} onClick={() => selectStyle(option)}>
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

      {(openedFamily || isFamilyDetailLoading || familyDetailError) && <div className="catalog-family-drawer-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) closeFamilyDetails() }}><section className="catalog-family-drawer" role="dialog" aria-modal={!createKind} aria-labelledby="catalog-family-title">
        <div className="catalog-family-drawer-header"><div className="catalog-family-drawer-identity">{familyImage.objectUrl ? <img src={familyImage.objectUrl} alt="" /> : <Shirt size={22} aria-hidden="true" />}<div><h2 id="catalog-family-title">{openedFamily?.name ?? t('catalog.family', 'Garment family')}</h2><small>{openedFamily?.code}</small></div></div><button ref={closeDrawerRef} type="button" className="catalog-icon-button" aria-label={t('catalog.close', 'Close')} onClick={closeFamilyDetails}><X size={18} /></button></div>
        {(isFamilyDetailLoading || familyImage.isLoading) && <p role="status" className="catalog-drawer-muted"><Loader2 size={16} className="animate-spin" /> {t('catalog.loadingDetails', 'Loading family details…')}</p>}
        {familyDetailError && <p className="catalog-error" role="alert">{familyDetailError}</p>}
        {openedFamily && <>
          <h3>{t('catalog.applicableGroups', 'Applicable style groups')}</h3>
          {openedFamily.tenant === null && <div className="catalog-style-readonly"><p>{t('catalog.globalFamilyReadonly', 'This is a Back Office default. Create a Shop-local copy to edit it without changing other Shops.')}</p>{role !== 'VIEWER' && <button className="primary-button" type="button" onClick={() => void editGlobalFamilyInShop()} disabled={isSavingFamilyGroups}>{isSavingFamilyGroups ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}{isSavingFamilyGroups ? t('catalog.preparingShopCopy', 'Preparing Shop copy…') : t('catalog.editInThisShop', 'Edit in this Shop')}</button>}</div>}
          {openedFamily.status === 'ARCHIVED' && <p className="catalog-style-readonly">{t('catalog.archivedFamilyReadonly', 'This garment family is archived.')}</p>}
            {canEditFamilyGroups && <button className="primary-button catalog-add-family-group" type="button" onClick={() => openFamilyGroupCreate(openedFamily.id)}><Plus size={16} />{t('catalog.addShopLocalGroup', 'Add Shop-local style group')}</button>}
          <div className="catalog-family-group-configs">
            {groups.map(group => {
              const current = familyGroupConfigs.find(item => item.option_group.id === group.id)
                return <div className={`catalog-family-group-config${current ? ' is-configured' : ''}`} key={group.id}>
                <label><input type="checkbox" checked={Boolean(current)} disabled={!canEditFamilyGroups} onChange={event => setFamilyGroupConfigs(items => event.target.checked
                  ? [...items, { id: `pending-${group.id}`, option_group: group, sort_order: items.length, selection_mode: 'SINGLE', is_required: false }]
                  : items.filter(item => item.option_group.id !== group.id))} /><span>{group.name}<small>{group.code} · {group.is_global ? t('catalog.global', 'Global') : t('catalog.shop', 'Shop')}</small></span></label>
                {current && <div className="catalog-family-group-options">
                  <label className="catalog-family-group-mode"><span>{t('catalog.selectionMode', 'Selection')}</span><select aria-label={`${group.name} ${t('catalog.selectionMode', 'Selection')}`} value={current.selection_mode} disabled={!canEditFamilyGroups} onChange={event => setFamilyGroupConfigs(items => items.map(item => item.option_group.id === group.id ? { ...item, selection_mode: event.target.value as 'SINGLE' | 'MULTI' } : item))}><option value="SINGLE">{t('catalog.singleSelection', 'Single')}</option><option value="MULTI">{t('catalog.multipleSelection', 'Multiple')}</option></select></label>
                  <label><input type="checkbox" checked={current.is_required} disabled={!canEditFamilyGroups} onChange={event => setFamilyGroupConfigs(items => items.map(item => item.option_group.id === group.id ? { ...item, is_required: event.target.checked } : item))} />{t('catalog.requiredGroup', 'Required')}</label>
                </div>}
              </div>
            })}
            {!groups.length && <span className="catalog-drawer-muted">{t('catalog.noGroupsHint', 'No option groups are available for this Shop.')}</span>}
          </div>
          {canEditFamilyGroups && <button className="primary-button catalog-save-family-groups" type="button" onClick={() => void saveFamilyGroups()} disabled={isSavingFamilyGroups}>{isSavingFamilyGroups ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}{isSavingFamilyGroups ? t('catalog.saving', 'Saving…') : t('catalog.saveGroupConfiguration', 'Save style groups')}</button>}
          <div className="catalog-family-groups">{openedFamily.option_groups.map(group => <button key={group.id} className="catalog-tag catalog-group-chip" type="button" onClick={() => browseStyles(group.id)}>{group.name}</button>)}{openedFamily.option_groups.length === 0 && <span className="catalog-drawer-muted">{t('catalog.noApplicableGroups', 'No style groups are configured for this family.')}</span>}</div>
          <section className="catalog-setup-section" aria-labelledby="catalog-measurements-title">
            <div className="catalog-setup-heading"><div><h3 id="catalog-measurements-title">{t('measurements.title', 'Measurements')}</h3><p>{t('catalog.measurementSetupHint', 'Configure the measurement fields available for this garment.')}</p></div></div>
            {!canConfigureMeasurements ? <p className="catalog-drawer-muted">{t('catalog.measurementAccessRequired', 'Measurement access is required to view this setup.')}</p>
              : openedFamily.tenant !== shopId ? <div className="catalog-info-note"><AlertCircle size={17} /><span>{t('catalog.materializeForMeasurements', 'Customize this garment in the Shop before configuring its measurements.')}</span></div>
                : isMeasurementLoading ? <p role="status" className="catalog-drawer-muted"><Loader2 size={15} className="animate-spin" />{t('catalog.loadingMeasurements', 'Loading measurements…')}</p>
                  : <>
                    {measurementError && <p className="catalog-error" role="alert">{measurementError}</p>}
                    <div className="catalog-measurement-list">
                      {familyMeasurements.map(definition => <div className="catalog-measurement-row" key={definition.id}><span><strong>{definition.translations.find(item => item.locale === 'en')?.name || definition.code}</strong><small>{definition.code}{definition.group_code ? ` · ${definition.group_code}` : ''}{definition.is_global ? ` · ${t('catalog.global', 'Global')}` : ''}</small></span><span className="catalog-tag">{t('catalog.familyLevel', 'Garment')}</span></div>)}
                      {!familyMeasurements.length && <p className="catalog-drawer-muted">{t('catalog.noMeasurementsConfigured', 'No active measurement fields are mapped here yet.')}</p>}
                    </div>
                    {canEditMeasurements && <div className="catalog-measurement-tools">
                      <div className="catalog-measurement-tools-heading"><h4>{t('catalog.addMeasurementFields', 'Add measurement fields')}</h4><p>{t('catalog.addMeasurementFieldsHint', 'Add an existing Shop measurement to this garment, or create a new field.')}</p></div>
                      <div className="catalog-measurement-map"><label>{t('catalog.existingMeasurement', 'Existing measurement')}<ResponsiveChoice ariaLabel={t('catalog.mapExistingMeasurement', 'Add existing Shop measurement')} value={measurementDefinitionId} onChange={setMeasurementDefinitionId} options={measurementDefinitions.filter(definition => definition.is_active && !familyMeasurements.some(mapped => mapped.id === definition.id)).map(definition => ({ value: definition.id, label: `${definition.translations.find(item => item.locale === 'en')?.name || definition.code} (${definition.code})` }))} placeholder={t('catalog.chooseMeasurement', 'Choose a measurement')} preserveScrollOnDialogChoice /></label></div>
                      <div className="catalog-measurement-actions">
                        <button className="secondary-button" type="button" onClick={() => void mapMeasurementDefinition()} disabled={!measurementDefinitionId || isMeasurementSaving}>{isMeasurementSaving ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />}{t('catalog.mapMeasurement', 'Add mapping')}</button>
                        <button className="secondary-button" type="button" onClick={() => setShowNewMeasurementForm(value => !value)}>{showNewMeasurementForm ? <X size={15} /> : <Plus size={15} />}{showNewMeasurementForm ? t('catalog.cancelNewMeasurement', 'Cancel new field') : t('catalog.createMeasurement', 'Create a measurement field')}</button>
                        <button className="primary-button" type="button" onClick={() => browseDesigns(openedFamily.id)}><ArrowRight size={16} />{t('catalog.viewDesigns', 'View Designs')}</button>
                      </div>
                      {showNewMeasurementForm && <form className="catalog-measurement-create" onSubmit={event => void createMeasurementDefinition(event)}>
                        <label>{t('catalog.measurementName', 'Name (English)')}<input required maxLength={120} value={measurementName} onChange={event => { const nextName = event.target.value; setMeasurementName(nextName); if (!isMeasurementCodeEdited) setMeasurementCode(measurementCodeFromName(nextName, measurementDefinitions)) }} /></label>
                        <label>{t('catalog.measurementCode', 'Code')}<input required maxLength={64} pattern="[a-zA-Z0-9_-]+" value={measurementCode} onChange={event => { setMeasurementCode(event.target.value); setIsMeasurementCodeEdited(true) }} /><small>{t('catalog.measurementCodeAutoHint', 'Generated from the name. You can edit it.')}</small></label>
                        <label>{t('catalog.measurementGroupCode', 'Group code (optional)')}<input maxLength={48} value={measurementGroupCode} onChange={event => setMeasurementGroupCode(event.target.value)} /></label>
                        <button className="primary-button" type="submit" disabled={isMeasurementSaving || !measurementName.trim() || !measurementCode.trim()}>{isMeasurementSaving ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />}{t('catalog.createAndMapMeasurement', 'Create and map')}</button>
                      </form>}
                    </div>}
                    {!canEditMeasurements && <p className="catalog-drawer-muted">{t('catalog.measurementReadOnly', 'Your role can view measurement setup but cannot change it.')}</p>}
                  </>}
          </section>
          {(returnToDesignDraft || !canEditMeasurements) && <div className="catalog-family-drawer-actions">{returnToDesignDraft && <button className="secondary-button" type="button" onClick={() => navigate(`/designs?family=${encodeURIComponent(openedFamily.id)}`, { state: { resumeDesignDraft: { ...returnToDesignDraft, familyId: openedFamily.id } } })}>{t('catalog.returnToDesign', 'Return to Design')}</button>}{!canEditMeasurements && <button className="primary-button" type="button" onClick={() => browseDesigns(openedFamily.id)}><ArrowRight size={16} />{t('catalog.viewDesigns', 'View Designs')}</button>}</div>}
        </>}
      </section></div>}

      {createKind && <div className="catalog-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setCreateKind(null) }}>
        <form className="catalog-dialog" role="dialog" aria-modal="true" onSubmit={event => void submitCreate(event)} aria-labelledby="catalog-create-title">
          <div className="catalog-dialog-heading"><h2 id="catalog-create-title">{createKind === 'group' ? t('catalog.createGroup', 'Create style group') : t('catalog.newItem', { item: t('catalog.styleOption', 'Style option').toLowerCase() })}</h2><button ref={closeCreateDialogRef} type="button" className="catalog-icon-button" onClick={() => setCreateKind(null)} aria-label={t('catalog.close', 'Close')}><X size={18} /></button></div>
          <label>{t('catalog.nameEnglish', 'Name (English)')}<input required maxLength={120} value={name} onChange={event => setName(event.target.value)} /></label>
          <label>{t('catalog.code', 'Code')}<input required maxLength={64} pattern="[a-zA-Z0-9_-]+" value={code} onChange={event => setCode(event.target.value)} /><small>{t('catalog.codeHint', 'Use letters, numbers, hyphens, or underscores.')}</small></label>
          {createKind === 'style' && <label>{t('catalog.optionGroup', 'Option group')}<ResponsiveChoice ariaLabel={t('catalog.optionGroup', 'Option group')} required value={selectedGroup} onChange={setSelectedGroup} options={groups.map(group => ({ value: group.id, label: group.name }))} /></label>}
          {createKind === 'style' && <label>{t('catalog.referenceImagesOptional', 'Reference images (optional)')}<input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={event => setNewStyleImages(Array.from(event.target.files ?? []))} /><small>{t('catalog.referenceImagesR2Hint', 'Images upload privately after the style option is created.')}</small>{newStyleImages.length > 0 && <small>{t('catalog.selectedImageCount', '{{count}} image(s) selected', { count: newStyleImages.length })}</small>}</label>}
          <div className="catalog-dialog-actions"><button type="button" className="secondary-button" onClick={() => setCreateKind(null)}>{t('catalog.cancel', 'Cancel')}</button><button type="submit" className="primary-button" disabled={isSaving || (createKind === 'style' && !groups.length)}>{isSaving ? <Loader2 size={16} className="animate-spin" /> : null} {t('catalog.create', 'Create')}</button></div>
        </form>
      </div>}
    </div>
  )
}
