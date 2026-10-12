import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ChevronDown, ChevronRight, Copy, Download, GitCompareArrows, RotateCw, Trash2 } from 'lucide-react'
import { ApiError } from '../../services/apiClient'
import { getAllShopVariants, getFamilyDetail } from '../catalog/api'
import type { Variant } from '../catalog/types'
import { measurementApi } from '../measurements/api'
import type { MeasurementComparison, MeasurementPage, MeasurementProfile, MeasurementSet } from '../measurements/types'
import './client-workspace.css'

type ProfileHistory = { pages: Record<number, MeasurementPage<MeasurementSet>>; loadingPage?: number; errorPage?: number }

function formatDate(value: string, locale: string) {
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export function ClientMeasurementHistory({ shopId, clientId, locale }: { shopId: string; clientId: string; locale: string }) {
  const { t } = useTranslation()
  const [profiles, setProfiles] = useState<MeasurementProfile[]>([])
  const [profilesLoading, setProfilesLoading] = useState(true)
  const [profilesError, setProfilesError] = useState(false)
  const [profilesDenied, setProfilesDenied] = useState(false)
  const [expandedProfile, setExpandedProfile] = useState<string | null>(null)
  const [historyByProfile, setHistoryByProfile] = useState<Record<string, ProfileHistory>>({})
  const [activePageByProfile, setActivePageByProfile] = useState<Record<string, number>>({})
  const [details, setDetails] = useState<Record<string, MeasurementSet>>({})
  const [openingSet, setOpeningSet] = useState<string | null>(null)
  const [setError, setSetError] = useState<string | null>(null)
  const [copyingSet, setCopyingSet] = useState<string | null>(null)
  const [copyError, setCopyError] = useState(false)
  const [deletingSet, setDeletingSet] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [compareIds, setCompareIds] = useState<Record<string, [string, string]>>({})
  const [comparisons, setComparisons] = useState<Record<string, MeasurementComparison>>({})
  const [comparisonLoading, setComparisonLoading] = useState<string | null>(null)
  const [comparisonError, setComparisonError] = useState<string | null>(null)
  const [exportingSet, setExportingSet] = useState<string | null>(null)
  const [exportError, setExportError] = useState<string | null>(null)
  const [garmentLabels, setGarmentLabels] = useState<Record<string, { family: string; variant: string }>>({})
  const labelsByFamily = useRef(new Map<string, { family: string; variants: Variant[] }>())
  const labelsInFlight = useRef(new Map<string, Promise<{ family: string; variants: Variant[] }>>())
  const pageRequests = useRef(new Map<string, Promise<void>>())
  const mounted = useRef(true)
  const requestGeneration = useRef(0)

  useEffect(() => {
    const generation = ++requestGeneration.current
    mounted.current = true
    setProfilesLoading(true)
    setProfilesError(false)
    setProfilesDenied(false)
    measurementApi.profiles(shopId, clientId, { kind: 'client' })
      .then(result => { if (mounted.current && generation === requestGeneration.current) setProfiles(result) })
      .catch((error: unknown) => {
        if (mounted.current && generation === requestGeneration.current) {
          setProfilesError(true)
          if (error instanceof ApiError && error.status === 403) setProfilesDenied(true)
        }
      })
      .finally(() => { if (mounted.current && generation === requestGeneration.current) setProfilesLoading(false) })
    return () => { mounted.current = false; requestGeneration.current += 1 }
  }, [shopId, clientId])

  const loadPage = useCallback((profileId: string, page: number, retry = false) => {
    const key = `${profileId}:${page}`
    const generation = requestGeneration.current
    const existing = pageRequests.current.get(key)
    if (existing) return existing
    if (!retry && historyByProfile[profileId]?.pages[page]) return Promise.resolve()
    setHistoryByProfile(current => ({
      ...current,
      [profileId]: { ...current[profileId], pages: current[profileId]?.pages ?? {}, loadingPage: page, errorPage: undefined },
    }))
    const request = measurementApi.setsPage(shopId, clientId, { kind: 'client' }, profileId, page)
      .then(result => {
        if (mounted.current && generation === requestGeneration.current) setHistoryByProfile(current => ({
          ...current,
          [profileId]: { pages: { ...(current[profileId]?.pages ?? {}), [page]: result } },
        }))
      })
      .catch(() => {
        if (mounted.current && generation === requestGeneration.current) setHistoryByProfile(current => ({
          ...current,
          [profileId]: { ...current[profileId], pages: current[profileId]?.pages ?? {}, errorPage: page },
        }))
      })
      .finally(() => { pageRequests.current.delete(key) })
    pageRequests.current.set(key, request)
    return request
  }, [clientId, historyByProfile, shopId])

  const loadGarmentLabel = useCallback((profile: MeasurementProfile) => {
    const cached = garmentLabels[profile.id]
    if (cached) return Promise.resolve(cached)
    const familyKey = `${profile.family}:${locale}`
    let familyData = labelsByFamily.current.get(familyKey)
    let request = labelsInFlight.current.get(familyKey)
    if (!familyData && !request) {
      request = (async () => {
        const [family, variants] = await Promise.all([
          getFamilyDetail(profile.family, locale),
          profile.variant ? getAllShopVariants(shopId, profile.family, locale) : Promise.resolve([] as Variant[]),
        ])
        const result = { family: family.name, variants }
        labelsByFamily.current.set(familyKey, result)
        return result
      })()
      labelsInFlight.current.set(familyKey, request)
      request.finally(() => labelsInFlight.current.delete(familyKey)).catch(() => undefined)
    }
    const resolveLabel = async () => {
      familyData = familyData ?? await request!
      const label = { family: familyData.family, variant: familyData.variants.find(variant => variant.id === profile.variant)?.name ?? '' }
      if (mounted.current) setGarmentLabels(current => ({ ...current, [profile.id]: label }))
      return label
    }
    return resolveLabel()
  }, [garmentLabels, locale, shopId])

  const toggleProfile = (profile: MeasurementProfile) => {
    if (expandedProfile === profile.id) { setExpandedProfile(null); return }
    setExpandedProfile(profile.id)
    void loadPage(profile.id, 1)
    void loadGarmentLabel(profile).catch(() => undefined)
  }

  const openSet = async (profileId: string, setId: string) => {
    if (details[setId]) {
      setDetails(current => { const next = { ...current }; delete next[setId]; return next })
      return
    }
    setSetError(null)
    const generation = requestGeneration.current
    setOpeningSet(setId)
    try {
      const detail = await measurementApi.setDetail(shopId, clientId, { kind: 'client' }, profileId, setId)
      if (generation === requestGeneration.current) setDetails(current => ({ ...current, [setId]: detail }))
    } catch (error) {
      if (generation === requestGeneration.current) setSetError(error instanceof ApiError && error.status === 403 ? t('measurements.accessDenied') : t('clients.historyDetailError'))
    } finally { if (generation === requestGeneration.current) setOpeningSet(null) }
  }

  const copySet = async (profileId: string, set: MeasurementSet) => {
    if (!window.confirm(t('clients.confirmCopyMeasurement', { version: set.version }))) return
    setCopyError(false)
    const generation = requestGeneration.current
    setCopyingSet(set.id)
    try {
      const copied = await measurementApi.copySet(shopId, clientId, { kind: 'client' }, profileId, set.id)
      if (generation !== requestGeneration.current) return
      setDetails(current => ({ ...current, [copied.id]: copied }))
      setHistoryByProfile(current => ({
        ...current,
        [profileId]: {
          pages: {
            ...current[profileId]?.pages,
            1: current[profileId]?.pages[1]
              ? { ...current[profileId].pages[1], count: current[profileId].pages[1].count + 1, results: [copied, ...current[profileId].pages[1].results.filter(item => item.id !== copied.id)].slice(0, 20) }
              : { count: 1, next: null, previous: null, results: [copied] },
          },
          loadingPage: 1,
        },
      }))
      setActivePageByProfile(current => ({ ...current, [profileId]: 1 }))
      await loadPage(profileId, 1, true)
    } catch { if (generation === requestGeneration.current) setCopyError(true) }
    finally { if (generation === requestGeneration.current) setCopyingSet(null) }
  }

  const compareSets = async (profileId: string) => {
    const ids = compareIds[profileId]
    if (!ids || ids[0] === ids[1]) return
    setComparisonError(null)
    const generation = requestGeneration.current
    setComparisonLoading(profileId)
    try {
      const result = await measurementApi.compare(shopId, clientId, { kind: 'client' }, profileId, ids[0], ids[1])
      if (generation === requestGeneration.current) setComparisons(current => ({ ...current, [profileId]: result }))
    } catch { if (generation === requestGeneration.current) setComparisonError(profileId) }
    finally { if (generation === requestGeneration.current) setComparisonLoading(null) }
  }

  const deleteSet = async (profileId: string, set: MeasurementSet, activeCount: number) => {
    if (activeCount <= 1 || deletingSet) return
    if (!window.confirm(t('measurements.deleteVersionConfirm', { version: set.version }))) return
    setDeleteError(null)
    const generation = requestGeneration.current
    setDeletingSet(set.id)
    try {
      await measurementApi.deleteSet(shopId, clientId, { kind: 'client' }, profileId, set.id)
      if (generation !== requestGeneration.current) return
      setDetails(current => { const next = { ...current }; delete next[set.id]; return next })
      setComparisons(current => { const next = { ...current }; delete next[profileId]; return next })
      setCompareIds(current => { const next = { ...current }; delete next[profileId]; return next })
      setHistoryByProfile(current => ({
        ...current,
        [profileId]: { pages: {}, loadingPage: 1 },
      }))
      setActivePageByProfile(current => ({ ...current, [profileId]: 1 }))
      await loadPage(profileId, 1, true)
    } catch (error) {
      if (generation === requestGeneration.current) {
        setDeleteError(error instanceof Error ? error.message : t('measurements.deleteVersionError'))
      }
    } finally { if (generation === requestGeneration.current) setDeletingSet(null) }
  }

  const exportPdf = async (profileId: string, version: number, setId: string) => {
    setExportError(null)
    const generation = requestGeneration.current
    setExportingSet(setId)
    try {
      const blob = await measurementApi.exportWorksheet(shopId, clientId, { kind: 'client' }, profileId, setId)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = `measurement-version-${version}.pdf`
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (error) {
      if (generation === requestGeneration.current) setExportError(error instanceof ApiError && error.status === 403 ? t('measurements.accessDenied') : t('measurements.worksheetError'))
    } finally { if (generation === requestGeneration.current) setExportingSet(null) }
  }

  const profileViews = useMemo(() => profiles.map(profile => {
    const history = historyByProfile[profile.id]
    const page = history?.pages[1]
    return { profile, history, page, labels: garmentLabels[profile.id] }
  }), [profiles, historyByProfile, garmentLabels])

  return (
    <section className="client-workspace-panel client-measurement-history" aria-labelledby="client-measurement-heading">
      <div className="client-workspace-panel-heading">
        <div>
          <p className="client-workspace-eyebrow">{t('clients.measurementEyebrow')}</p>
          <h2 id="client-measurement-heading">{t('measurements.title')}</h2>
        </div>
        <span className="client-workspace-count">{profiles.length}</span>
      </div>
      {profilesLoading ? <p className="client-workspace-muted" aria-busy="true">{t('clients.loadingProfiles')}</p> : profilesError ? (
        <div className="client-workspace-inline-error" role="alert"><span>{profilesDenied ? t('measurements.accessDenied') : t('clients.historyLoadError')}</span><button type="button" className="client-workspace-text-button" onClick={() => {
          setProfilesLoading(true); setProfilesError(false); setProfilesDenied(false)
          measurementApi.profiles(shopId, clientId, { kind: 'client' }).then(setProfiles).catch((error: unknown) => { setProfilesError(true); if (error instanceof ApiError && error.status === 403) setProfilesDenied(true) }).finally(() => setProfilesLoading(false))
        }}><RotateCw size={15} /> {t('measurements.retry')}</button></div>
      ) : profiles.length === 0 ? <p className="client-workspace-muted">{t('clients.noMeasurementProfiles')}</p> : (
        <div className="client-profile-list">
          {profileViews.map(({ profile, history, page, labels }) => {
            const isOpen = expandedProfile === profile.id
            const select = compareIds[profile.id] ?? ['', '']
            const activePage = activePageByProfile[profile.id] ?? 1
            const allSets = Object.entries(history?.pages ?? {}).sort(([left], [right]) => Number(left) - Number(right)).flatMap(([, result]) => result.results)
            const availableSets = allSets
            return <article className={`client-profile-card${isOpen ? ' is-expanded' : ''}`} key={profile.id}>
              <button className="client-profile-toggle" type="button" aria-expanded={isOpen} onClick={() => toggleProfile(profile)}>
                <span className="client-profile-garment">{labels?.family ?? t('measurements.profile')}{labels?.variant ? ` · ${labels.variant}` : ''}</span>
                <span className="client-profile-meta">{t('clients.profileCreatedAt', { date: formatDate(profile.created_at, locale) })}</span>
                {isOpen ? <ChevronDown size={18} aria-hidden="true" /> : <ChevronRight size={18} aria-hidden="true" />}
              </button>
              {isOpen && <div className="client-profile-content">
                {history?.loadingPage === 1 && !page ? <p className="client-workspace-muted" aria-busy="true">{t('clients.loadingHistory')}</p> : null}
                {history?.loadingPage === activePage && activePage > 1 && !history.pages[activePage] ? <p className="client-workspace-muted" aria-busy="true">{t('clients.loadingHistory')}</p> : null}
                {history?.errorPage === 1 && <div className="client-workspace-inline-error" role="alert"><span>{t('clients.historyLoadError')}</span><button type="button" className="client-workspace-text-button" onClick={() => void loadPage(profile.id, 1, true)}><RotateCw size={15} /> {t('measurements.retry')}</button></div>}
                {page && page.results.length === 0 && <p className="client-workspace-muted">{t('measurements.noHistory')}</p>}
                  {page && page.results.length > 0 && <>
                  <p className="client-profile-latest">{t('clients.latestMeasurement', { version: page.results[0].version, date: formatDate(page.results[0].created_at, locale) })}</p>
                  <div className="client-version-list">
                    {(history?.pages[activePage]?.results ?? []).map(set => <div className="client-version-row" key={set.id}>
                      <div className="client-version-summary">
                        <button type="button" className="client-version-open" onClick={() => void openSet(profile.id, set.id)} aria-expanded={Boolean(details[set.id])} aria-busy={openingSet === set.id} disabled={openingSet === set.id}>
                          <strong>{t('measurements.version', { version: set.version })}</strong>
                          <span>{formatDate(set.created_at, locale)}</span>
                        </button>
                        {set.copied_from && <span className="client-version-provenance">{t('clients.copiedMeasurement')}</span>}
                      </div>
                      <div className="client-version-actions">
                        <button type="button" className="client-workspace-icon-button" onClick={() => void copySet(profile.id, set)} disabled={copyingSet === set.id} aria-label={t('measurements.copyVersion')} title={t('measurements.copyVersion')}><Copy size={16} /></button>
                        <button type="button" className="client-workspace-icon-button" onClick={() => void exportPdf(profile.id, set.version, set.id)} disabled={exportingSet === set.id} aria-label={t('measurements.exportWorksheet', { version: set.version })} title={t('measurements.exportWorksheet', { version: set.version })}><Download size={16} /></button>
                        <button type="button" className="client-workspace-icon-button is-danger" onClick={() => void deleteSet(profile.id, set, page.count)} disabled={page.count <= 1 || Boolean(deletingSet)} aria-label={page.count <= 1 ? t('measurements.lastVersionProtected') : t('measurements.deleteVersion')} title={page.count <= 1 ? t('measurements.lastVersionProtected') : t('measurements.deleteVersion')}><Trash2 size={16} /></button>
                      </div>
                    </div>)}
                  </div>
                  {setError && <p className="client-workspace-inline-error" role="alert">{setError}</p>}
                  {copyError && <p className="client-workspace-inline-error" role="alert">{t('measurements.copyError')}</p>}
                  {deleteError && <p className="client-workspace-inline-error" role="alert">{deleteError}</p>}
                  {exportError && <p className="client-workspace-inline-error" role="alert">{exportError}</p>}
                  {Object.values(details).filter(detail => detail.profile === profile.id).map(detail => <section className="client-version-detail" key={detail.id} aria-label={t('measurements.version', { version: detail.version })}>
                    <h4>{t('clients.measurementVersionDetail', { version: detail.version })}</h4>
                    {detail.copied_from && <p>{t('clients.copiedMeasurement')}</p>}
                    <dl className="client-measurement-values">{detail.values.map(value => <div key={value.id}><dt>{value.label || value.label_snapshot || value.definition_code_snapshot}</dt><dd>{value.value} {value.unit}</dd></div>)}</dl>
                  </section>)}
                  {availableSets.length > 1 && <div className="client-compare-controls">
                    <label>{t('measurements.previousVersion')}<select value={select[0]} onChange={event => setCompareIds(current => ({ ...current, [profile.id]: [event.target.value, select[1]] }))}><option value="">—</option>{availableSets.map(set => <option key={set.id} value={set.id}>{t('measurements.version', { version: set.version })}</option>)}</select></label>
                    <label>{t('measurements.currentVersion')}<select value={select[1]} onChange={event => setCompareIds(current => ({ ...current, [profile.id]: [select[0], event.target.value] }))}><option value="">—</option>{availableSets.map(set => <option key={set.id} value={set.id}>{t('measurements.version', { version: set.version })}</option>)}</select></label>
                    <button type="button" className="btn-secondary" disabled={!select[0] || !select[1] || select[0] === select[1] || comparisonLoading === profile.id} onClick={() => void compareSets(profile.id)}><GitCompareArrows size={15} /> {t('measurements.compare')}</button>
                  </div>}
                  {comparisonError === profile.id && <p className="client-workspace-inline-error" role="alert">{t('measurements.compareError')}</p>}
                  {comparisons[profile.id] && <div className="client-comparison-table" role="region" aria-label={t('measurements.compare')}>
                    {comparisons[profile.id].results.map(row => <div className="client-comparison-row" key={row.definition_id}><strong>{row.label}</strong><span>{row.from_value ?? '—'} {row.from_unit ?? ''}</span><span>{row.to_value ?? '—'} {row.to_unit ?? ''}</span><span>{row.unit_mismatch ? t('measurements.unitMismatch') : row.difference ?? '—'}</span></div>)}
                  </div>}
                  {history?.pages[activePage]?.previous && <button type="button" className="client-workspace-more" disabled={history?.loadingPage === activePage - 1} onClick={() => { setActivePageByProfile(current => ({ ...current, [profile.id]: activePage - 1 })); void loadPage(profile.id, activePage - 1) }}>{t('catalog.previous')}</button>}
                  {history?.pages[activePage]?.next && <button type="button" className="client-workspace-more" disabled={history?.loadingPage === activePage + 1} onClick={() => { setActivePageByProfile(current => ({ ...current, [profile.id]: activePage + 1 })); void loadPage(profile.id, activePage + 1) }}>{history?.loadingPage === activePage + 1 ? t('clients.loadingHistory') : t('clients.loadOlderVersions')}</button>}
                  {history?.errorPage && <div className="client-workspace-inline-error" role="alert"><span>{t('clients.historyLoadError')}</span><button type="button" className="client-workspace-text-button" onClick={() => void loadPage(profile.id, history.errorPage!, true)}><RotateCw size={15} /> {t('measurements.retry')}</button></div>}
                </>}
              </div>}
            </article>
          })}
        </div>
      )}
    </section>
  )
}
