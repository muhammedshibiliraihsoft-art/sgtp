import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Archive, ChevronRight, Copy, Download, Plus, Ruler, Save, Trash2 } from 'lucide-react'
import { apiRequest } from '../../services/apiClient'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { useAuth } from '../../services/useAuth'
import { CustomSelect } from '../../components/CustomSelect'
import { shopsService, type ShopSummary } from '../../services/shops'
import { clientsApi } from '../clients/api'
import type { Client, RelatedPerson } from '../clients/types'
import { getAllShopGarmentFamilies, getAllShopStyleOptions, getAllShopVariants, getShopFamilyOptionGroups } from '../catalog/api'
import type { CatalogFamily, FamilyOptionGroupConfig, OptionGroup, StyleOption, Variant } from '../catalog/types'
import { createShopDesign, getAllShopDesigns } from '../designs/api'
import { getAllGlobalDesigns } from '../../backoffice/designs/api'
import type { Design } from '../designs/types'
import { measurementApi } from './api'
import type { InventoryFabric, MeasurementComparison, MeasurementDefinition, MeasurementOwner, MeasurementPage, MeasurementProfile, MeasurementSet } from './types'
import { MeasurementEntryForm, type DraftValue } from './MeasurementEntryForm'
import { MeasurementReview } from './MeasurementReview'
import { StyleConfiguration } from './StyleConfiguration'
import './Measurements.css'

async function fetchAll<T>(path: string): Promise<T[]> {
  const items: T[] = []
  let next: string | null = path
  while (next) {
    const response: MeasurementPage<T> = await apiRequest<MeasurementPage<T>>(next)
    items.push(...response.results)
    if (!response.next) break
    const url: URL = new URL(response.next, window.location.origin)
    next = `${url.pathname}${url.search}`
  }
  return items
}

async function getAllShops() {
  const shops: ShopSummary[] = []
  let page = 1
  while (true) {
    const response = await shopsService.list('', page)
    shops.push(...response.results)
    if (!response.next) return shops
    page += 1
  }
}

function selectionToOption(selection: NonNullable<Design['latest_version']>['selections'][number], tenant: string | null): StyleOption {
  return {
    id: selection.style_option,
    option_group: selection.option_group,
    tenant,
    code: selection.selected_code,
    name: selection.style_option_name || selection.selected_name_en,
    is_active: true,
    is_global: tenant === null,
    reference_images: selection.style_option_images,
  }
}

function makeOwner(wearerId: string): MeasurementOwner {
  return wearerId === 'client' || !wearerId
    ? { kind: 'client' }
    : { kind: 'related_person', id: wearerId }
}

function createRequestId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, character => {
    const random = Math.floor(Math.random() * 16)
    const value = character === 'x' ? random : (random & 0x3) | 0x8
    return value.toString(16)
  })
}

export function ClientMeasurementsPage({ embedded = false, initialClient, initialRelatedPersons, initialShopId }: {
  embedded?: boolean
  initialClient?: Client
  initialRelatedPersons?: RelatedPerson[]
  initialShopId?: string
} = {}) {
  const { clientId: routeClientId } = useParams<{ clientId?: string }>()
  const { t, i18n } = useTranslation()
  const { user } = useAuth()
  const { shopId: memberShopId, role, workFunctions, isLoading: shopContextLoading } = useCurrentShop()
  const isMainSupplier = user?.is_main_supplier_admin === true
  const locale = ['en', 'ar-KW', 'bn', 'ur'].includes(i18n.resolvedLanguage || '') ? i18n.resolvedLanguage! : 'en'

  const [supplierShops, setSupplierShops] = useState<ShopSummary[]>([])
  const [supplierShopsLoading, setSupplierShopsLoading] = useState(false)
  const [supplierShopId, setSupplierShopId] = useState(initialShopId ?? '')
  const shopId = isMainSupplier ? (embedded && initialShopId ? initialShopId : supplierShopId) : memberShopId || ''
  const canReadMeasurements = Boolean(shopId && (isMainSupplier || role === 'ADMIN' || (role === 'STAFF' && workFunctions.includes('MEASUREMENT'))))
  const canWriteMeasurements = canReadMeasurements

  const [activeClientId, setActiveClientId] = useState(routeClientId || '')
  const [client, setClient] = useState<Client | null>(initialClient ?? null)
  const [relatedPersons, setRelatedPersons] = useState<RelatedPerson[]>(initialRelatedPersons ?? [])
  const [wearerId, setWearerId] = useState('client')
  const [clientSearch, setClientSearch] = useState('')
  const [clientMatches, setClientMatches] = useState<Client[]>([])
  const [clientSearchLoading, setClientSearchLoading] = useState(false)
  const [clientLoading, setClientLoading] = useState(false)
  const [clientChooserOpen, setClientChooserOpen] = useState(!routeClientId)

  const [families, setFamilies] = useState<CatalogFamily[]>([])
  const [variants, setVariants] = useState<Variant[]>([])
  const [catalogLoading, setCatalogLoading] = useState(false)
  const [familyId, setFamilyId] = useState('')
  const [variantId, setVariantId] = useState('')
  const [groups, setGroups] = useState<OptionGroup[]>([])
  const [familyGroupConfigs, setFamilyGroupConfigs] = useState<FamilyOptionGroupConfig[]>([])
  const [groupsLoading, setGroupsLoading] = useState(false)
  const [groupsLoadFailed, setGroupsLoadFailed] = useState(false)
  const [selectedStyles, setSelectedStyles] = useState<Record<string, StyleOption[]>>({})
  const [activeGroupId, setActiveGroupId] = useState<string | null>(null)
  const [optionsByGroup, setOptionsByGroup] = useState<Record<string, StyleOption[]>>({})
  const [loadingGroupId, setLoadingGroupId] = useState<string | null>(null)
  const [groupErrorId, setGroupErrorId] = useState<string | null>(null)
  const [familyShopDesigns, setFamilyShopDesigns] = useState<Design[]>([])
  const [familyGlobalDesigns, setFamilyGlobalDesigns] = useState<Design[]>([])
  const [selectedDesign, setSelectedDesign] = useState<Design | null>(null)
  const [designName, setDesignName] = useState('')
  const [designCreateOpen, setDesignCreateOpen] = useState(false)
  const [designSaving, setDesignSaving] = useState(false)
  const [designMessage, setDesignMessage] = useState('')
  const [designSaveIncomplete, setDesignSaveIncomplete] = useState(false)

  const [profiles, setProfiles] = useState<MeasurementProfile[]>([])
  const [profileId, setProfileId] = useState('')
  const [profilesLoading, setProfilesLoading] = useState(false)
  const [profilesLoadFailed, setProfilesLoadFailed] = useState(false)
  const [definitions, setDefinitions] = useState<MeasurementDefinition[]>([])
  const [definitionsLoading, setDefinitionsLoading] = useState(false)
  const [definitionsLoadFailed, setDefinitionsLoadFailed] = useState(false)
  const [definitionCreateOpen, setDefinitionCreateOpen] = useState(false)
  const [definitionCode, setDefinitionCode] = useState('')
  const [definitionName, setDefinitionName] = useState('')
  const [definitionGroupCode, setDefinitionGroupCode] = useState('')
  const [definitionSaving, setDefinitionSaving] = useState(false)
  const [definitionError, setDefinitionError] = useState('')
  const [sets, setSets] = useState<MeasurementSet[]>([])
  const [selectedSetId, setSelectedSetId] = useState('')
  const [draftValues, setDraftValues] = useState<Record<string, DraftValue>>({})
  const [draftSeedVersion, setDraftSeedVersion] = useState(0)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [savingMeasurements, setSavingMeasurements] = useState(false)
  const [exportingWorksheet, setExportingWorksheet] = useState(false)
  const [copyingSetId, setCopyingSetId] = useState<string | null>(null)
  const [deletingSetId, setDeletingSetId] = useState<string | null>(null)
  const [compareFrom, setCompareFrom] = useState('')
  const [compareTo, setCompareTo] = useState('')
  const [comparison, setComparison] = useState<MeasurementComparison | null>(null)
  const [comparing, setComparing] = useState(false)
  const draftDirtyRef = useRef(false)

  const [showFabrics, setShowFabrics] = useState(false)
  const [fabrics, setFabrics] = useState<InventoryFabric[]>([])
  const [fabric, setFabric] = useState<InventoryFabric | null>(null)
  const [fabricsLoading, setFabricsLoading] = useState(false)
  const [fabricsLoadedForShop, setFabricsLoadedForShop] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  const [mobileStep, setMobileStep] = useState('context')
  const wizardRootRef = useRef<HTMLDivElement>(null)
  const touchStartRef = useRef<{ x: number; y: number } | null>(null)
  const suppressSwipeClickRef = useRef(false)

  const variantsForFamily = useMemo(() => variants.filter(item => item.family === familyId && item.is_active), [variants, familyId])
  const shopDesigns = useMemo(() => familyShopDesigns.filter(item => !variantId || !item.variant || item.variant === variantId), [familyShopDesigns, variantId])
  const globalDesigns = useMemo(() => familyGlobalDesigns.filter(item => !variantId || !item.variant || item.variant === variantId), [familyGlobalDesigns, variantId])
  const family = families.find(item => item.id === familyId) ?? null
  const variant = variants.find(item => item.id === variantId) ?? null
  const wearer = relatedPersons.find(item => item.id === wearerId) ?? null
  const owner = useMemo(() => makeOwner(wearerId), [wearerId])
  const selectedSet = sets.find(item => item.id === selectedSetId) ?? sets[0] ?? null
  const previousValues = useMemo(() => Object.fromEntries(
    (sets[0]?.values ?? []).map(value => [value.definition, { value: value.value, unit: value.unit }]),
  ), [sets])
  const optionScope = `${shopId}:${familyId}`
  const optionScopeRef = useRef(optionScope)
  const optionRequests = useRef(new Set<string>())
  const measurementSaveInFlight = useRef(false)
  const worksheetExportInFlight = useRef(false)
  const copyInFlight = useRef(false)
  const designSaveInFlight = useRef(false)
  const pendingDesignSave = useRef<{ fingerprint: string; key: string } | null>(null)
  const matchingProfile = profiles.find(item => item.family === familyId && item.variant === (variantId || null)) ?? null
  const mobileSteps = useMemo(() => [
    { id: 'context', label: `${t('measurements.chooseClient')} · ${t('measurements.garment')}` },
    { id: 'design', label: t('measurements.designs') },
    { id: 'configuration', label: t('measurements.style') },
    { id: 'measurements', label: t('measurements.measurements') },
    ...(profileId ? [{ id: 'history', label: t('measurements.history') }] : []),
    { id: 'review', label: t('measurements.finalReview') },
  ], [profileId, t])
  const currentMobileStepIndex = Math.max(0, mobileSteps.findIndex(step => step.id === mobileStep))

  useEffect(() => {
    if (!mobileSteps.some(step => step.id === mobileStep)) setMobileStep('context')
  }, [mobileStep, mobileSteps])

  const moveMobileStep = (offset: number) => {
    if (offset > 0 && mobileStep === 'context' && (!client || !familyId)) return
    const next = mobileSteps[Math.min(mobileSteps.length - 1, Math.max(0, currentMobileStepIndex + offset))]
    if (!next) return
    setMobileStep(next.id)
    window.setTimeout(() => wizardRootRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 0)
  }

  const handleWizardTouchStart = (event: React.TouchEvent<HTMLDivElement>) => {
    const target = event.target
    if (target instanceof Element && target.closest('input, select, textarea, [contenteditable="true"]')) {
      touchStartRef.current = null
      return
    }
    const touch = event.touches[0]
    touchStartRef.current = touch ? { x: touch.clientX, y: touch.clientY } : null
  }

  const handleWizardTouchEnd = (event: React.TouchEvent<HTMLDivElement>) => {
    const start = touchStartRef.current
    touchStartRef.current = null
    if (!start) return
    const touch = event.changedTouches[0]
    if (!touch) return
    const dx = touch.clientX - start.x
    const dy = touch.clientY - start.y
    if (Math.abs(dx) < 64 || Math.abs(dx) < Math.abs(dy) * 1.25) return
    event.preventDefault()
    suppressSwipeClickRef.current = true
    window.setTimeout(() => { suppressSwipeClickRef.current = false }, 450)
    moveMobileStep(dx < 0 ? 1 : -1)
  }

  const onDraftDirtyChange = useCallback((dirty: boolean) => {
    draftDirtyRef.current = dirty
  }, [])

  const replaceDraftValues = useCallback((next: Record<string, DraftValue>) => {
    draftDirtyRef.current = false
    setDraftValues(next)
    setDraftSeedVersion(version => version + 1)
  }, [])

  const confirmDiscardDraft = useCallback(() => {
    if (!draftDirtyRef.current) return true
    const discard = window.confirm(t('measurements.discardDraftConfirm', 'Discard unsaved measurement values?'))
    if (discard) draftDirtyRef.current = false
    return discard
  }, [t])

  useEffect(() => {
    const warnBeforeUnload = (event: BeforeUnloadEvent) => {
      if (!draftDirtyRef.current) return
      event.preventDefault()
      event.returnValue = ''
    }
    window.addEventListener('beforeunload', warnBeforeUnload)
    return () => window.removeEventListener('beforeunload', warnBeforeUnload)
  }, [])

  useEffect(() => {
    const confirmInternalNavigation = (event: MouseEvent) => {
      if (!draftDirtyRef.current || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
      if (!(event.target instanceof Element)) return
      const link = event.target.closest<HTMLAnchorElement>('a[href]')
      if (!link || (link.target && link.target !== '_self')) return
      if (link.href.startsWith('javascript:')) return
      if (!confirmDiscardDraft()) {
        event.preventDefault()
        event.stopImmediatePropagation()
      }
    }
    document.addEventListener('click', confirmInternalNavigation, true)
    return () => document.removeEventListener('click', confirmInternalNavigation, true)
  }, [confirmDiscardDraft])

  useEffect(() => {
    optionScopeRef.current = optionScope
  }, [optionScope])

  useEffect(() => {
    setActiveClientId(routeClientId || '')
    setClientChooserOpen(!routeClientId)
  }, [routeClientId])

  useEffect(() => {
    if (!isMainSupplier || embedded) return
    let active = true
    setSupplierShopsLoading(true)
    getAllShops().then(rows => {
      if (active) setSupplierShops(rows.filter(item => item.is_active))
    }).catch(cause => {
      if (active) setError(cause instanceof Error ? cause.message : t('measurements.loadError'))
    }).finally(() => {
      if (active) setSupplierShopsLoading(false)
    })
    return () => { active = false }
  }, [isMainSupplier, embedded, reloadKey, t])

  useEffect(() => {
    if (!shopId || !canReadMeasurements) return
    let active = true
    setCatalogLoading(true)
    Promise.all([getAllShopGarmentFamilies(shopId, locale), getAllShopVariants(shopId, undefined, locale)]).then(([familyRows, variantRows]) => {
      if (!active) return
      setFamilies(familyRows)
      setVariants(variantRows)
    }).catch(cause => {
      if (active) setError(cause instanceof Error ? cause.message : t('measurements.loadError'))
    }).finally(() => {
      if (active) setCatalogLoading(false)
    })
    return () => { active = false }
  }, [shopId, canReadMeasurements, locale, reloadKey, t])

  useEffect(() => {
    if (!shopId || !canReadMeasurements || !activeClientId) {
      setClient(null)
      setRelatedPersons([])
      return
    }
    if (embedded && initialClient?.id === activeClientId && initialRelatedPersons) {
      setClient(initialClient)
      setRelatedPersons(initialRelatedPersons)
      setClientLoading(false)
      return
    }
    let active = true
    setClientLoading(true)
    Promise.all([
      clientsApi.detail(shopId, activeClientId),
      fetchAll<RelatedPerson>(`/api/v1/shops/${encodeURIComponent(shopId)}/clients/${encodeURIComponent(activeClientId)}/related-persons/`),
    ]).then(([loadedClient, people]) => {
      if (!active) return
      setClient(loadedClient)
      setRelatedPersons(people)
    }).catch(cause => {
      if (active) {
        setClient(null)
        setRelatedPersons([])
        setError(cause instanceof Error ? cause.message : t('measurements.loadError'))
      }
    }).finally(() => {
      if (active) setClientLoading(false)
    })
    return () => { active = false }
  }, [shopId, canReadMeasurements, activeClientId, reloadKey, t, embedded, initialClient, initialRelatedPersons])

  useEffect(() => {
    if (!shopId || !canReadMeasurements || !clientChooserOpen) return
    let active = true
    const timer = window.setTimeout(() => {
      setClientSearchLoading(true)
      clientsApi.list(shopId, clientSearch, 1).then(response => {
        if (active) setClientMatches(response.results)
      }).catch(cause => {
        if (active) setError(cause instanceof Error ? cause.message : t('measurements.loadError'))
      }).finally(() => {
        if (active) setClientSearchLoading(false)
      })
    }, 250)
    return () => { active = false; window.clearTimeout(timer) }
  }, [shopId, canReadMeasurements, clientChooserOpen, clientSearch, reloadKey, t])

  useEffect(() => {
    if (!shopId || !canReadMeasurements || !activeClientId) {
      setProfiles([])
      setProfileId('')
      setProfilesLoading(false)
      setProfilesLoadFailed(false)
      return
    }
    let active = true
    setProfilesLoading(true)
    setProfilesLoadFailed(false)
    setProfileId('')
    setProfiles([])
    measurementApi.profiles(shopId, activeClientId, owner).then(rows => {
      if (active) {
        setProfiles(rows)
        setProfilesLoadFailed(false)
      }
    }).catch(cause => {
      if (active) {
        setProfilesLoadFailed(true)
        setError(cause instanceof Error ? cause.message : t('measurements.profileError'))
      }
    }).finally(() => {
      if (active) setProfilesLoading(false)
    })
    return () => { active = false }
  }, [shopId, canReadMeasurements, activeClientId, owner, reloadKey, t])

  useEffect(() => {
    if (!familyId || profilesLoading || profilesLoadFailed) return
    setProfileId(matchingProfile?.id ?? '')
  }, [familyId, variantId, matchingProfile, profilesLoading, profilesLoadFailed])

  useEffect(() => {
    if (!shopId || !canReadMeasurements || !familyId) {
      setDefinitions([])
      setDefinitionsLoading(false)
      setDefinitionsLoadFailed(false)
      return
    }
    let active = true
    setDefinitions([])
    setDefinitionsLoading(true)
    setDefinitionsLoadFailed(false)
    measurementApi.definitions(shopId, familyId, variantId || null, locale).then(rows => {
      if (active) {
        setDefinitions(rows)
        setDefinitionsLoadFailed(false)
      }
    }).catch(cause => {
      if (active) {
        setDefinitionsLoadFailed(true)
        setError(cause instanceof Error ? cause.message : t('measurements.loadError'))
      }
    }).finally(() => {
      if (active) setDefinitionsLoading(false)
    })
    return () => { active = false }
  }, [shopId, canReadMeasurements, familyId, variantId, locale, reloadKey, t])

  useEffect(() => {
    if (!shopId || !familyId) {
      setGroups([])
      setFamilyGroupConfigs([])
      setGroupsLoadFailed(false)
      return
    }
    let active = true
    setGroupsLoading(true)
    setGroupsLoadFailed(false)
    getShopFamilyOptionGroups(shopId, familyId, locale).then(configRows => {
      if (active) {
        setFamilyGroupConfigs(configRows)
        setGroups(configRows.map(row => row.option_group))
        setGroupsLoadFailed(false)
      }
    }).catch(cause => {
      if (active) {
        setGroupsLoadFailed(true)
        setError(cause instanceof Error ? cause.message : t('measurements.loadError'))
      }
    }).finally(() => {
      if (active) setGroupsLoading(false)
    })
    return () => { active = false }
  }, [shopId, familyId, locale, reloadKey, t])

  useEffect(() => {
    if (!shopId || !familyId || !canReadMeasurements) {
      setFamilyShopDesigns([])
      setFamilyGlobalDesigns([])
      return
    }
    let active = true
    Promise.all([
      getAllShopDesigns(shopId, { family: familyId }, locale),
      getAllGlobalDesigns(familyId, locale),
    ]).then(([localDesignRows, globalDesignRows]) => {
      if (!active) return
      setFamilyShopDesigns(localDesignRows)
      setFamilyGlobalDesigns(globalDesignRows)
    }).catch(cause => {
      if (active) setError(cause instanceof Error ? cause.message : t('measurements.loadError'))
    })
    return () => { active = false }
  }, [shopId, familyId, canReadMeasurements, locale, reloadKey, t])

  useEffect(() => {
    if (!shopId || !canReadMeasurements || !activeClientId || !profileId) {
      setSets([])
      setSelectedSetId('')
      setComparison(null)
      return
    }
    let active = true
    setHistoryLoading(true)
    measurementApi.sets(shopId, activeClientId, owner, profileId).then(rows => {
      if (!active) return
      setSets(rows)
      setSelectedSetId(current => rows.some(row => row.id === current) ? current : rows[0]?.id ?? '')
      setCompareFrom(rows[1]?.id ?? '')
      setCompareTo(rows[0]?.id ?? '')
    }).catch(cause => {
      if (active) setError(cause instanceof Error ? cause.message : t('measurements.loadError'))
    }).finally(() => {
      if (active) setHistoryLoading(false)
    })
    return () => { active = false }
  }, [shopId, canReadMeasurements, activeClientId, profileId, owner, reloadKey, t])

  const loadGroupOptions = useCallback(async (groupId: string, retry = false) => {
    if (!shopId) return
    const scope = `${shopId}:${familyId}`
    const requestKey = `${scope}:${groupId}`
    if (!retry && optionsByGroup[groupId]) return
    if (optionRequests.current.has(requestKey)) return
    optionRequests.current.add(requestKey)
    setLoadingGroupId(groupId)
    setGroupErrorId(null)
    try {
      const rows = await getAllShopStyleOptions(shopId, groupId, locale)
      if (optionScopeRef.current === scope) setOptionsByGroup(current => ({ ...current, [groupId]: rows }))
    } catch {
      if (optionScopeRef.current === scope) setGroupErrorId(groupId)
    } finally {
      optionRequests.current.delete(requestKey)
      setLoadingGroupId(current => current === groupId ? null : current)
    }
  }, [shopId, familyId, locale, optionsByGroup])

  const handleFamilyChange = (nextFamilyId: string) => {
    if (!confirmDiscardDraft()) return
    setFamilyId(nextFamilyId)
    setVariantId('')
    setProfileId('')
    setSets([])
    setSelectedSetId('')
    setDefinitions([])
    replaceDraftValues({})
    setGroups([])
    setFamilyGroupConfigs([])
    setOptionsByGroup({})
    setActiveGroupId(null)
    setSelectedStyles({})
    setSelectedDesign(null)
    setDesignName('')
    setDesignMessage('')
    setDesignSaveIncomplete(false)
    setComparison(null)
    setFabric(null)
    setError('')
  }

  const handleVariantChange = (nextVariantId: string) => {
    if (!confirmDiscardDraft()) return
    setVariantId(nextVariantId)
    setProfileId('')
    setSets([])
    setSelectedSetId('')
    replaceDraftValues({})
    setSelectedDesign(null)
    setSelectedStyles({})
    setDesignName('')
    setComparison(null)
    setError('')
  }

  const selectClient = (nextClient: Client) => {
    if (!confirmDiscardDraft()) return
    setActiveClientId(nextClient.id)
    setClient(nextClient)
    setWearerId('client')
    setClientChooserOpen(false)
    setProfileId('')
    setSets([])
    setSelectedSetId('')
    replaceDraftValues({})
    setDefinitions([])
    setGroups([])
    setFamilyGroupConfigs([])
    setOptionsByGroup({})
    setActiveGroupId(null)
    setFamilyId('')
    setVariantId('')
    setSelectedStyles({})
    setSelectedDesign(null)
    setFabric(null)
    setError('')
  }

  const saveMeasurements = useCallback(async (values: Record<string, DraftValue>): Promise<boolean> => {
    if (
      !shopId
      || !activeClientId
      || !familyId
      || !canWriteMeasurements
      || measurementSaveInFlight.current
    ) return false
    const entered = definitions.filter(definition => values[definition.id]?.value.trim())
    if (!entered.length || entered.some(definition => (
      !/^-?\d+(?:\.\d{1,4})?$/.test(values[definition.id].value.trim())
      || !values[definition.id].unit
    ))) {
      setError(t('measurements.enterValue'))
      return false
    }
    measurementSaveInFlight.current = true
    setSavingMeasurements(true)
    setError('')
    setNotice('')
    try {
      let targetProfile = matchingProfile
      const needsProfileResolution = !targetProfile
      if (!targetProfile) {
        try {
          targetProfile = await measurementApi.createProfile(shopId, activeClientId, owner, familyId, variantId || null)
        } catch (createError) {
          // Another tab may have created the unique profile after this page loaded.
          const latestProfiles = await measurementApi.profiles(shopId, activeClientId, owner).catch(() => null)
          targetProfile = latestProfiles?.find(item => item.family === familyId && item.variant === (variantId || null)) ?? null
          if (!targetProfile) throw createError
        }
      }
      const valuesToSave = entered.map(definition => ({
        definition_id: definition.id,
        value: values[definition.id].value.trim(),
        unit: values[definition.id].unit as 'CM' | 'INCH',
      }))
      const designVersionId = selectedDesign?.latest_version?.status === 'PUBLISHED' ? selectedDesign.latest_version.id : null
      const created = designVersionId
        ? await measurementApi.saveSet(shopId, activeClientId, owner, targetProfile.id, valuesToSave, designVersionId)
        : await measurementApi.saveSet(shopId, activeClientId, owner, targetProfile.id, valuesToSave)
      if (needsProfileResolution) {
        setProfiles(current => [targetProfile!, ...current.filter(item => item.id !== targetProfile!.id)])
        setProfileId(targetProfile.id)
      }
      setSets(current => [created, ...current.filter(item => item.id !== created.id)])
      setSelectedSetId(created.id)
      replaceDraftValues({})
      setNotice(t('measurements.versionSaved'))
      return true
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t('measurements.saveError'))
      return false
    } finally {
      measurementSaveInFlight.current = false
      setSavingMeasurements(false)
    }
  }, [shopId, activeClientId, familyId, variantId, matchingProfile, canWriteMeasurements, definitions, owner, replaceDraftValues, selectedDesign, t])

  async function createMeasurementDefinition(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!shopId || !familyId || !canWriteMeasurements || definitionSaving) return
    setDefinitionSaving(true)
    setDefinitionError('')
    try {
      const created = await measurementApi.createDefinition(shopId, {
        code: definitionCode.trim(),
        group_code: definitionGroupCode.trim(),
        sort_order: definitions.length,
        translations: [{ locale: 'en', name: definitionName.trim() }],
        mappings: [{ family_id: familyId, variant_id: null }],
      })
      setDefinitions(current => [...current, created].sort((a, b) => a.sort_order - b.sort_order || a.code.localeCompare(b.code)))
      setDefinitionCreateOpen(false)
      setDefinitionCode('')
      setDefinitionName('')
      setDefinitionGroupCode('')
    } catch (cause) {
      setDefinitionError(cause instanceof Error ? cause.message : t('measurements.definitionCreateError', 'Could not add this measurement.'))
    } finally {
      setDefinitionSaving(false)
    }
  }

  const exportMeasurementWorksheet = async () => {
    if (!shopId || !activeClientId || !profileId || !selectedSet || worksheetExportInFlight.current) return
    worksheetExportInFlight.current = true
    setExportingWorksheet(true)
    setError('')
    try {
      const pdf = await measurementApi.exportWorksheet(
        shopId,
        activeClientId,
        owner,
        profileId,
        selectedSet.id,
        selectedDesign?.id,
      )
      const objectUrl = URL.createObjectURL(pdf)
      const link = document.createElement('a')
      link.href = objectUrl
      link.download = `measurement-worksheet-v${selectedSet.version}.pdf`
      document.body.append(link)
      link.click()
      link.remove()
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t('measurements.worksheetError'))
    } finally {
      worksheetExportInFlight.current = false
      setExportingWorksheet(false)
    }
  }

  const copyMeasurementSet = async (set: MeasurementSet) => {
    if (
      !shopId
      || !activeClientId
      || !profileId
      || !canWriteMeasurements
      || copyInFlight.current
    ) return
    if (!confirmDiscardDraft()) return
    replaceDraftValues({})
    copyInFlight.current = true
    setCopyingSetId(set.id)
    setError('')
    setNotice('')
    try {
      const copied = await measurementApi.copySet(shopId, activeClientId, owner, profileId, set.id)
      setSets(current => [copied, ...current.filter(item => item.id !== copied.id)])
      setSelectedSetId(copied.id)
      replaceDraftValues(Object.fromEntries(copied.values.map(value => [value.definition, { value: value.value, unit: value.unit }])))
      setNotice(t('measurements.copySaved'))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t('measurements.copyError'))
    } finally {
      copyInFlight.current = false
      setCopyingSetId(null)
    }
  }

  const setDraftFromMeasurementSet = (set: MeasurementSet) => {
    if (!confirmDiscardDraft()) return
    replaceDraftValues(Object.fromEntries(set.values.map(value => [value.definition, { value: value.value, unit: value.unit }])))
    setNotice(t('measurements.useAsStartingPoint'))
  }

  const compareMeasurementSets = async () => {
    if (!shopId || !activeClientId || !profileId || !compareFrom || !compareTo || compareFrom === compareTo) {
      setError(t('measurements.noCompare'))
      return
    }
    setComparing(true)
    setError('')
    try {
      setComparison(await measurementApi.compare(shopId, activeClientId, owner, profileId, compareFrom, compareTo))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t('measurements.compareError'))
    } finally {
      setComparing(false)
    }
  }

  const openStyleGroup = (groupId: string) => {
    if (activeGroupId === groupId) {
      setActiveGroupId(null)
      return
    }
    setActiveGroupId(groupId)
    void loadGroupOptions(groupId)
  }

  const chooseStyleOption = (groupId: string, option: StyleOption) => {
    const selectionMode = familyGroupConfigs.find(item => item.option_group.id === groupId)?.selection_mode ?? 'SINGLE'
    setSelectedStyles(current => {
      const selected = current[groupId] ?? []
      const next = selectionMode === 'MULTI'
        ? selected.some(item => item.id === option.id) ? selected.filter(item => item.id !== option.id) : [...selected, option]
        : selected.some(item => item.id === option.id) ? [] : [option]
      const result = { ...current }
      if (next.length) result[groupId] = next
      else delete result[groupId]
      return result
    })
    setSelectedDesign(null)
    setDesignSaveIncomplete(false)
    setActiveGroupId(null)
    setDesignMessage('')
  }

  const chooseExistingDesign = (designId: string) => {
    const design = [...shopDesigns, ...globalDesigns].find(item => item.id === designId) ?? null
    setDesignCreateOpen(false)
    setSelectedDesign(design)
    setDesignSaveIncomplete(false)
    setDesignName(design?.name ?? '')
    setDesignMessage('')
    setActiveGroupId(null)
    const styles = design?.latest_version?.selections.reduce<Record<string, StyleOption[]>>((result, selection) => {
      const options = result[selection.option_group] ?? []
      result[selection.option_group] = [...options, selectionToOption(selection, design.tenant)]
      return result
    }, {}) ?? {}
    setSelectedStyles(styles)
  }

  const saveShopDesign = async () => {
    if (
      !shopId
      || !familyId
      || !canWriteMeasurements
      || groupsLoading
      || groupsLoadFailed
      || designSaveInFlight.current
    ) return
    const selectedOptions = Object.values(selectedStyles).flat()
    const missingRequiredGroup = familyGroupConfigs.find(item => item.is_required && !(selectedStyles[item.option_group.id]?.length))
    if (missingRequiredGroup) {
      setError(t('measurements.requiredDesignGroup', 'Choose an option for the required {{group}} group.', { group: missingRequiredGroup.option_group.name }))
      return
    }
    const name = designName.trim() || t('measurements.defaultDesignName', {
      clientName: client?.name ?? t('measurements.chooseClient'),
      garmentName: family?.name ?? t('measurements.garment'),
    })
    const selectionIds = selectedOptions.map(option => option.id).sort()
    const fingerprint = JSON.stringify({ familyId, variantId, name, selectionIds })
    if (!pendingDesignSave.current || pendingDesignSave.current.fingerprint !== fingerprint) {
      pendingDesignSave.current = { fingerprint, key: createRequestId() }
    }
    designSaveInFlight.current = true
    setDesignSaving(true)
    setError('')
    setDesignMessage('')
    setDesignSaveIncomplete(false)
    try {
      const saved = await createShopDesign(shopId, {
        family_id: familyId,
        variant_id: variantId || null,
        name,
        selection_ids: selectionIds,
        idempotency_key: pendingDesignSave.current.key,
      })
      if (!saved.latest_version?.id) throw new Error(t('measurements.designDraftUnavailable'))
      setFamilyShopDesigns(current => [saved, ...current.filter(item => item.id !== saved.id)])
      setSelectedDesign(saved)
      setDesignName(saved.name)
      setDesignMessage(t('measurements.designSaved'))
      setDesignSaveIncomplete(false)
      setDesignCreateOpen(false)
      pendingDesignSave.current = null
    } catch (cause) {
      setDesignSaveIncomplete(true)
      setDesignMessage(t('measurements.designSaveRetrySafe'))
      setError(cause instanceof Error ? cause.message : t('measurements.loadError'))
    } finally {
      designSaveInFlight.current = false
      setDesignSaving(false)
    }
  }

  const deleteMeasurementSet = async (set: MeasurementSet) => {
    if (!shopId || !activeClientId || !profileId || sets.length <= 1 || deletingSetId) return
    if (!window.confirm(t('measurements.deleteVersionConfirm', { version: set.version }))) return
    setDeletingSetId(set.id)
    setError('')
    try {
      await measurementApi.deleteSet(shopId, activeClientId, owner, profileId, set.id)
      const remaining = sets.filter(item => item.id !== set.id)
      setSets(remaining)
      setSelectedSetId(current => current === set.id ? (remaining[0]?.id ?? '') : current)
      setCompareFrom(current => current === set.id ? (remaining.at(-1)?.id ?? '') : current)
      setCompareTo(current => current === set.id ? (remaining[0]?.id ?? '') : current)
      setComparison(null)
      setNotice(t('measurements.versionDeleted', { version: set.version }))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t('measurements.deleteVersionError'))
    } finally {
      setDeletingSetId(null)
    }
  }

  const loadFabrics = async () => {
    if (!shopId) return
    if (fabricsLoadedForShop === shopId) {
      setShowFabrics(current => !current)
      return
    }
    setShowFabrics(true)
    setFabricsLoading(true)
    setError('')
    try {
      const rows = await measurementApi.fabrics(shopId)
      setFabrics(rows)
      setFabricsLoadedForShop(shopId)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t('measurements.loadError'))
    } finally {
      setFabricsLoading(false)
    }
  }

  const selectSupplierShop = (nextShopId: string) => {
    if (!confirmDiscardDraft()) return
    setSupplierShopId(nextShopId)
    setActiveClientId('')
    setClient(null)
    setRelatedPersons([])
    setClientChooserOpen(true)
    setClientSearch('')
    setFamilyId('')
    setVariantId('')
    setProfileId('')
    setProfiles([])
    setSets([])
    setSelectedSetId('')
    replaceDraftValues({})
    setGroups([])
    setFamilyGroupConfigs([])
    setSelectedStyles({})
    setSelectedDesign(null)
    setDesignSaveIncomplete(false)
    setFabric(null)
    setOptionsByGroup({})
    setFabricsLoadedForShop('')
    setFabrics([])
  }

  const isContextLoading = isMainSupplier ? supplierShopsLoading : shopContextLoading
  const setCount = sets.length
  const missingRequiredStyleGroup = familyGroupConfigs.some(item => item.is_required && !(selectedStyles[item.option_group.id]?.length))
  const canSaveDesign = canWriteMeasurements && Boolean(familyId) && !groupsLoading && !groupsLoadFailed && !missingRequiredStyleGroup
  const handleRetryPage = () => {
    setError('')
    setReloadKey(value => value + 1)
  }

  return <div className="content-wrap measurement-workspace" ref={wizardRootRef} onTouchStart={handleWizardTouchStart} onTouchEnd={handleWizardTouchEnd} onClickCapture={event => {
    if (!suppressSwipeClickRef.current) return
    event.preventDefault()
    event.stopPropagation()
  }}>
    <div className="measurement-page-heading">
      <div><span className="backoffice-eyebrow"><Ruler size={14} /> {t('measurements.title')}</span><h1>{t('measurements.title')}{client ? ` · ${client.name}` : ''}</h1><p>{t('measurements.subtitle')}</p></div>
      {routeClientId && !embedded && <Link className="btn-secondary" to={`/clients/${routeClientId}`}>← {t('clients.title')}</Link>}
    </div>

    {isMainSupplier && !embedded && <section className="measurement-context-card info-card">
      <label htmlFor="measurement-shop-select">{t('measurements.chooseShop')}</label>
      <CustomSelect id="measurement-shop-select" className="measurement-select" ariaLabel={t('measurements.chooseShop')} value={supplierShopId} onChange={selectSupplierShop} options={[
        { value: '', label: t('measurements.chooseShop') },
        ...supplierShops.map(item => ({ value: item.id, label: item.name })),
      ]} />
      <small>{t('measurements.chooseShopHint')}</small>
    </section>}

    {error && <div className="login-error-message" role="alert">{error}<button type="button" className="measurement-inline-retry" onClick={handleRetryPage}>{t('measurements.retryPage')}</button></div>}
    {notice && <div className="duplicate-warning" role="status">{notice}</div>}
    {designMessage && <div className="measurement-notice" role="status">{designMessage}{designSaveIncomplete && selectedDesign && <> <Link to={`/designs/${selectedDesign.id}`}>{t('measurements.reviewDraft')}</Link></>}</div>}

    {isContextLoading ? <div className="measurement-empty" aria-busy="true">{t('measurements.loading')}</div>
      : !shopId ? <div className="measurement-empty" role="status">{t('measurements.noShop')}</div>
        : !canReadMeasurements ? <div className="measurement-empty" role="alert">{t('measurements.accessDenied')}</div>
          : <div className="measurement-unified-card">
            <div className="measurement-context-pair" data-mobile-step="context" data-mobile-active={mobileStep === 'context'}>
            <section className="measurement-workflow-card info-card" aria-labelledby="measurement-client-heading">
              <div className="measurement-section-heading"><span className="measurement-step-number">01</span><div><h2 id="measurement-client-heading">{t('measurements.chooseClient')}</h2><p>{client ? `${client.name}${wearer ? ` · ${wearer.name}` : ''}` : t('measurements.searchClients')}</p></div></div>
              {clientChooserOpen || !client ? <div className="measurement-client-picker">
                <input aria-label={t('measurements.searchClients')} placeholder={t('measurements.searchClients')} value={clientSearch} onChange={event => setClientSearch(event.target.value)} />
                {clientSearchLoading ? <p aria-busy="true">{t('measurements.loading')}</p>
                  : clientMatches.length ? <div className="measurement-client-results">{clientMatches.map(item => <button type="button" key={item.id} onClick={() => selectClient(item)}><strong>{item.name}</strong><span>{item.phone || item.email || t('measurements.noContactDetails')}</span><ChevronRight size={18} /></button>)}</div>
                    : clientSearch.trim() ? <p>{t('measurements.noClientMatches')}</p> : null}
              </div> : <div className="measurement-client-selected"><div><strong>{client?.name}</strong><small>{wearer ? `${t('measurements.primaryClient')}: ${client?.name} · ${wearer.name}` : client?.phone || client?.email || ''}</small></div>{!embedded && <button type="button" className="btn-secondary" onClick={() => { setClientChooserOpen(true); setClientSearch(''); setActiveClientId(''); setClient(null); setProfileId(''); setSets([]) }}>{t('measurements.chooseClient')}</button>}</div>}
              {client && !clientChooserOpen && <label className="measurement-wearer-select">
                {t('measurements.wearer')}
                <CustomSelect className="measurement-select" ariaLabel={t('measurements.wearer')} value={wearerId} onChange={nextWearerId => {
                  if (!confirmDiscardDraft()) return
                  setWearerId(nextWearerId)
                  setProfileId('')
                  setProfiles([])
                  setSets([])
                  setSelectedSetId('')
                  replaceDraftValues({})
                }} options={[
                  { value: 'client', label: `${t('measurements.primaryClient')} - ${client.name}` },
                  ...relatedPersons.map(person => ({ value: person.id, label: `${t('measurements.relatedPerson')} - ${person.name}` })),
                ]} />
              </label>}
            </section>
            {client && !clientChooserOpen && (clientLoading ? <div className="measurement-context-pair-loading" data-mobile-step="context" data-mobile-active={mobileStep === 'context'} aria-busy="true">{t('measurements.loading')}</div> : <section className="measurement-workflow-card info-card" aria-labelledby="measurement-garment-heading">
              <div className="measurement-section-heading"><span className="measurement-step-number">02</span><div><h2 id="measurement-garment-heading">{t('measurements.garment')}</h2><p>{family ? `${family.name}${variant ? ` · ${variant.name}` : ''}` : t('measurements.chooseFamily')}</p></div></div>
              <div className="measurement-garment-selectors">
                <label>{t('measurements.family')}<CustomSelect className="measurement-select" ariaLabel={t('measurements.family')} value={familyId} onChange={handleFamilyChange} disabled={catalogLoading} options={[{ value: '', label: t('measurements.chooseFamily') }, ...families.map(item => ({ value: item.id, label: item.name }))]} /></label>
                <label>{t('measurements.variant')}<CustomSelect className="measurement-select" ariaLabel={t('measurements.variant')} value={variantId} onChange={handleVariantChange} disabled={!familyId || catalogLoading} options={[{ value: '', label: t('measurements.noVariant') }, ...variantsForFamily.map(item => ({ value: item.id, label: `${item.name}${item.is_default ? ` · ${t('measurements.defaultVariant')}` : ''}` }))]} /></label>
              </div>
              {catalogLoading && <small aria-busy="true">{t('measurements.loading')}</small>}
              {!catalogLoading && familyId && variantsForFamily.length === 0 && <div className="measurement-empty">{t('catalog.noVariants')}</div>}
            </section>)}
            </div>

            {client && !clientChooserOpen && !clientLoading && <>
                {familyId && <section className="measurement-workflow-card info-card" data-mobile-step="design" data-mobile-active={mobileStep === 'design' || mobileStep === 'configuration'} aria-labelledby="measurement-style-heading">
                  <div className="measurement-section-heading"><span className="measurement-step-number">03</span><div><h2 id="measurement-style-heading">{t('measurements.designs')}</h2><p>{t('measurements.styleHint')}</p></div></div>
                  <section className="measurement-design-library" data-mobile-step="design" data-mobile-active={mobileStep === 'design'} aria-label={t('measurements.designs')}>
                      <div className="measurement-design-library-heading"><h3>{t('measurements.designs')}</h3>{canWriteMeasurements && <button type="button" className="btn-primary" onClick={() => { setSelectedDesign(null); setDesignName(''); setDesignSaveIncomplete(false); setDesignMessage(''); setDesignCreateOpen(current => !current) }} aria-expanded={designCreateOpen}>{designCreateOpen ? t('catalog.cancel') : t('measurements.addNewDesign')}</button>}</div>
                      {shopDesigns.length + globalDesigns.length === 0 ? <div className="measurement-empty">{t('measurements.noSavedDesigns')}</div> : <div className="measurement-design-list">{[
                        ...globalDesigns.map(item => ({ item, source: t('measurements.sourceGlobal') })),
                        ...shopDesigns.map(item => ({ item, source: t('measurements.sourceShop') })),
                      ].map(({ item, source }) => <button type="button" key={item.id} className={`measurement-design-card${selectedDesign?.id === item.id ? ' is-selected' : ''}`} onClick={() => chooseExistingDesign(item.id)} aria-pressed={selectedDesign?.id === item.id}>
                        <span><strong>{item.name}</strong><small>{variants.find(row => row.id === item.variant)?.name ?? t('measurements.variant')}</small></span><span className="measurement-design-source">{source}</span>
                      </button>)}</div>}
                      {designCreateOpen && <div className="measurement-design-create-form">
                        <label>{t('measurements.designName')}<input maxLength={160} value={designName} onChange={event => { setDesignName(event.target.value); setSelectedDesign(null); setDesignSaveIncomplete(false) }} placeholder={`${client.name} · ${family?.name ?? t('measurements.garment')}`} /></label>
                        <button type="button" className="btn-primary" onClick={() => void saveShopDesign()} disabled={!canSaveDesign || designSaving}><Save size={16} />{designSaving ? t('measurements.saving') : t('measurements.saveDesign')}</button>
                        <small>{t('measurements.designSessionOnly')}</small>
                      </div>}
                  </section>
                  <section className="measurement-style-configuration" data-mobile-step="configuration" data-mobile-active={mobileStep === 'configuration'} aria-label={t('measurements.style')}>
                    <h3>{t('measurements.style')}</h3>
                    {groupsLoading ? <div className="measurement-empty" aria-busy="true">{t('measurements.loading')}</div> : groupsLoadFailed ? <div className="measurement-error-inline" role="alert"><span>{t('measurements.groupsLoadError')}</span><button type="button" className="btn-secondary" onClick={handleRetryPage}>{t('measurements.retry')}</button></div> : <StyleConfiguration
                      groups={groups}
                      groupConfigs={familyGroupConfigs}
                      selected={selectedStyles}
                      activeGroupId={activeGroupId}
                      optionsByGroup={optionsByGroup}
                      loadingGroupId={loadingGroupId}
                      groupErrorId={groupErrorId}
                      onOpenGroup={openStyleGroup}
                      onSelectOption={chooseStyleOption}
                      onRetryGroup={groupId => void loadGroupOptions(groupId, true)}
                      canWrite={canWriteMeasurements}
                    />}
                  </section>
                </section>}

                {familyId && <>
                  <section className="measurement-workflow-card info-card" data-mobile-step="measurements" data-mobile-active={mobileStep === 'measurements'} aria-labelledby="measurement-entry-heading">
                    <div className="measurement-section-heading"><span className="measurement-step-number">04</span><div><h2 id="measurement-entry-heading">{t('measurements.measurements')}</h2><p>{t('measurements.unitNote')}</p></div>{canWriteMeasurements && <button type="button" className="btn-secondary measurement-add-definition" onClick={() => { setDefinitionError(''); setDefinitionCreateOpen(open => !open) }} disabled={definitionsLoading}><Plus size={16} />{t('measurements.addDefinition', 'Add measurement')}</button>}</div>
                    {definitionCreateOpen && <form className="measurement-definition-create" onSubmit={event => void createMeasurementDefinition(event)}>
                      <strong>{t('measurements.addDefinitionTitle', 'Add a measurement for this garment')}</strong>
                      <p>{t('measurements.addDefinitionScope', 'This measurement will be available for every {{garment}} variant.', { garment: family?.name ?? t('measurements.garment') })}</p>
                      <div className="measurement-definition-fields">
                        <label>{t('measurements.definitionName', 'Measurement name')}<input required maxLength={120} value={definitionName} onChange={event => setDefinitionName(event.target.value)} /></label>
                        <label>{t('measurements.definitionCode', 'Code')}<input required maxLength={64} pattern="[a-zA-Z0-9_-]+" value={definitionCode} onChange={event => setDefinitionCode(event.target.value)} /><small>{t('measurements.definitionCodeHint', 'Use letters, numbers, hyphens, or underscores.')}</small></label>
                        <label>{t('measurements.definitionGroup', 'Group (optional)')}<input maxLength={48} value={definitionGroupCode} onChange={event => setDefinitionGroupCode(event.target.value)} /></label>
                      </div>
                      {definitionError && <p role="alert" className="measurement-error-inline">{definitionError}</p>}
                      <div className="measurement-definition-actions"><button type="button" className="btn-secondary" onClick={() => setDefinitionCreateOpen(false)} disabled={definitionSaving}>{t('catalog.cancel', 'Cancel')}</button><button type="submit" className="btn-primary" disabled={definitionSaving || !definitionName.trim() || !definitionCode.trim()}>{definitionSaving ? t('measurements.saving') : t('measurements.addDefinition', 'Add measurement')}</button></div>
                    </form>}
                    {historyLoading || definitionsLoading ? <div className="measurement-empty" aria-busy="true">{t('measurements.loading')}</div> : definitionsLoadFailed ? <div className="measurement-error-inline" role="alert"><span>{t('measurements.definitionsLoadError')}</span><button type="button" className="btn-secondary" onClick={handleRetryPage}>{t('measurements.retry')}</button></div> : <MeasurementEntryForm
                      definitions={definitions}
                      key={draftSeedVersion}
                      seedValues={draftValues}
                      previousValues={previousValues}
                      onDirtyChange={onDraftDirtyChange}
                      onSave={saveMeasurements}
                      saving={savingMeasurements}
                      canWrite={canWriteMeasurements}
                      locale={locale}
                    />}
                  </section>

                  {profileId && <section className="measurement-workflow-card info-card" data-mobile-step="history" data-mobile-active={mobileStep === 'history'} aria-labelledby="measurement-history-heading">
                    <div className="measurement-section-heading"><span className="measurement-step-number">05</span><div><h2 id="measurement-history-heading">{t('measurements.history')}</h2><p>{t('measurements.correctionRule', 'Old measurement records stay unchanged. Save a new version for corrections.')}</p></div>{selectedSet && canReadMeasurements && <button type="button" className="btn-secondary measurement-export-button" onClick={() => void exportMeasurementWorksheet()} disabled={exportingWorksheet}><Download size={16} />{exportingWorksheet ? t('measurements.exportingWorksheet') : t('measurements.exportWorksheet', { version: selectedSet.version })}</button>}</div>
                    {historyLoading ? <div className="measurement-empty" aria-busy="true">{t('measurements.loading')}</div> : sets.length === 0 ? <div className="measurement-empty">{t('measurements.noHistory')}</div> : <div className="measurement-history-list">{sets.map(set => <article className={`measurement-history-card${selectedSetId === set.id ? ' is-selected' : ''}`} key={set.id}>
                      <button type="button" className="measurement-history-select" onClick={() => setSelectedSetId(set.id)} aria-pressed={selectedSetId === set.id}><strong>{t('measurements.version', { version: set.version })}</strong><span>{new Date(set.created_at).toLocaleString(locale)}</span><small>{t('measurements.measurementsCount', { count: set.values.length })}{set.copied_from ? ` · ${t('measurements.copyProvenance', { version: sets.find(item => item.id === set.copied_from)?.version ?? '—' })}` : ''}</small></button>
                      <div className="measurement-history-values">{set.values.map(value => <div key={value.id}><span>{value.label}</span><strong>{value.value} {value.unit}</strong></div>)}</div>
                      {canWriteMeasurements && <div className="measurement-history-actions"><button type="button" className="btn-secondary" onClick={() => setDraftFromMeasurementSet(set)} disabled={Boolean(copyingSetId) || Boolean(deletingSetId)}><Copy size={15} />{t('measurements.useAsStartingPoint')}</button><button type="button" className="btn-secondary" onClick={() => void copyMeasurementSet(set)} disabled={Boolean(copyingSetId) || Boolean(deletingSetId)}><Archive size={15} />{copyingSetId === set.id ? t('measurements.saving') : t('measurements.copyVersion')}</button><button type="button" className="btn-secondary measurement-delete-version" onClick={() => void deleteMeasurementSet(set)} disabled={sets.length <= 1 || Boolean(deletingSetId)} aria-label={sets.length <= 1 ? t('measurements.lastVersionProtected') : t('measurements.deleteVersion')} title={sets.length <= 1 ? t('measurements.lastVersionProtected') : t('measurements.deleteVersion')}><Trash2 size={15} />{deletingSetId === set.id ? t('measurements.deleting') : t('measurements.deleteVersion')}</button></div>}
                    </article>)}</div>}
                    {sets.length > 1 && <div className="measurement-compare-controls"><label>{t('measurements.previousVersion')}<CustomSelect className="measurement-select" ariaLabel={t('measurements.previousVersion')} value={compareFrom} onChange={setCompareFrom} options={sets.map(set => ({ value: set.id, label: t('measurements.version', { version: set.version }) }))} /></label><label>{t('measurements.currentVersion')}<CustomSelect className="measurement-select" ariaLabel={t('measurements.currentVersion')} value={compareTo} onChange={setCompareTo} options={sets.map(set => ({ value: set.id, label: t('measurements.version', { version: set.version }) }))} /></label><button type="button" className="btn-secondary" onClick={() => void compareMeasurementSets()} disabled={comparing}>{comparing ? t('measurements.loading') : t('measurements.compare')}</button></div>}
                    {comparison && <div className="measurement-comparison" role="region" aria-label={t('measurements.compare')}><div className="measurement-comparison-heading"><strong>{t('measurements.previousVersion')} → {t('measurements.currentVersion')}</strong><button type="button" className="btn-secondary" onClick={() => setComparison(null)}>{t('catalog.close')}</button></div><div className="measurement-comparison-table"><div className="measurement-comparison-row is-header"><span>{t('measurements.measurements')}</span><span>{t('measurements.previousVersion')}</span><span>{t('measurements.currentVersion')}</span><span>{t('measurements.difference')}</span></div>{comparison.results.map(row => <div className="measurement-comparison-row" key={row.definition_id}><span>{row.label}</span><span>{row.from_value ?? '—'} {row.from_unit ?? ''}</span><span>{row.to_value ?? '—'} {row.to_unit ?? ''}</span><span>{row.unit_mismatch ? t('measurements.unitMismatch') : row.difference ?? '—'}</span></div>)}</div></div>}
                  </section>}
                </>}

                {familyId && <section className="measurement-workflow-card info-card" data-mobile-step="review" data-mobile-active={mobileStep === 'review'} aria-labelledby="measurement-fabric-heading">
                  <div className="measurement-section-heading"><span className="measurement-step-number">06</span><div><h2 id="measurement-fabric-heading">{t('measurements.fabric')}</h2><p>{fabric ? `${fabric.name} · ${fabric.available} ${fabric.unit} ${t('measurements.available')}` : t('measurements.noFabricSelected')}</p></div></div>
                  <button type="button" className="btn-secondary" onClick={() => void loadFabrics()}>{showFabrics ? t('measurements.hideFabrics', 'Close fabric list') : t('measurements.loadFabrics')}</button>
                  <p className="measurement-unit-note">{t('measurements.fabricNote')}</p>
                  {showFabrics && (fabricsLoading ? <div className="measurement-empty" aria-busy="true">{t('measurements.loading')}</div> : fabrics.length === 0 ? <div className="measurement-empty">{t('measurements.noFabrics')}</div> : <div className="measurement-fabric-list">{fabrics.map(item => <button type="button" key={item.material_id} className={`measurement-fabric-option${fabric?.material_id === item.material_id ? ' is-selected' : ''}`} onClick={() => setFabric(item)} aria-pressed={fabric?.material_id === item.material_id}><span><strong>{item.name}</strong><small>{item.code} · {item.unit} · {item.on_hand} {t('measurements.onHand')} · {item.reserved} {t('measurements.reserved')}</small></span><b>{item.available} {item.unit} {t('measurements.available')}</b></button>)}</div>)}
                </section>}

                {client && <div className="measurement-mobile-review" data-mobile-step="review" data-mobile-active={mobileStep === 'review'}><MeasurementReview
                  client={client}
                  wearer={wearer}
                  family={family}
                  variant={variant}
                  groups={groups}
                  selectedStyles={selectedStyles}
                  designName={selectedDesign?.name ?? designName}
                  designSaved={Boolean(selectedDesign) && !designSaveIncomplete}
                  measurementSet={selectedSet}
                  historyCount={setCount}
                  fabric={fabric}
                /></div>}
            </>}
            <nav className="measurement-mobile-nav" aria-label={t('measurements.title')}>
              <div className="measurement-mobile-progress-copy"><span>{mobileSteps[currentMobileStepIndex]?.label}</span><strong>{currentMobileStepIndex + 1} / {mobileSteps.length}</strong></div>
              <div className="measurement-mobile-progress-track" role="progressbar" aria-valuemin={1} aria-valuemax={mobileSteps.length} aria-valuenow={currentMobileStepIndex + 1}><span style={{ width: `${((currentMobileStepIndex + 1) / mobileSteps.length) * 100}%` }} /></div>
              <div className="measurement-mobile-nav-actions">
                {currentMobileStepIndex > 0 && <button type="button" className="btn-secondary" onClick={() => moveMobileStep(-1)}>{t('common.back', 'Back')}</button>}
                {currentMobileStepIndex < mobileSteps.length - 1 && <button type="button" className="btn-primary" onClick={() => moveMobileStep(1)} disabled={mobileStep === 'context' && (!client || !familyId)}>{t('common.next', 'Next')} <ChevronRight size={17} /></button>}
              </div>
            </nav>
          </div>}
  </div>
}
