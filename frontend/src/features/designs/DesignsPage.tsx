import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { ApiError } from '../../services/apiClient'
import { createShopFamily, getAllShopFamilies } from '../catalog/api'
import type { CatalogFamily } from '../catalog/types'
import { archiveShopDesign, createShopDesign, getAllShopDesigns } from './api'
import type { Design } from './types'
import { hasUnpublishedChanges } from './versionState'
import { ResponsiveChoice } from '../../components/CustomSelect'
import { AlertCircle, ArrowLeft, ChevronRight, Loader2, Plus, Shirt, Wand2, Archive } from 'lucide-react'
import './Designs.css'

type DesignDraft = { designName: string; familyId: string }
type DesignNavigationState = { resumeDesignDraft?: DesignDraft }

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : 'Could not load designs. Please try again.'
}

export function DesignsPage() {
  const { t } = useTranslation()
  const { shopId, role, isLoading: isShopLoading } = useCurrentShop()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const familyFilter = searchParams.get('family') || ''
  const [designs, setDesigns] = useState<Design[]>([])
  const [families, setFamilies] = useState<CatalogFamily[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [familyId, setFamilyId] = useState('')
  const [designName, setDesignName] = useState('')
  const [isAddGarmentOpen, setIsAddGarmentOpen] = useState(false)
  const [garmentName, setGarmentName] = useState('')
  const [garmentCode, setGarmentCode] = useState('')
  const [isCreatingGarment, setIsCreatingGarment] = useState(false)
  const [garmentError, setGarmentError] = useState<string | null>(null)
  const [newlyCreatedFamilyId, setNewlyCreatedFamilyId] = useState('')
  const canManageGarments = role === 'ADMIN' || role === 'STAFF'

  const loadDesigns = useCallback(async () => {
    if (!shopId) return
    try {
      const [designRows, familyRows] = await Promise.all([
        familyFilter ? getAllShopDesigns(shopId, { family: familyFilter }) : Promise.resolve([]), getAllShopFamilies(shopId),
      ])
      setError(null)
      setDesigns(designRows)
      setFamilies(familyRows)
    } catch (loadError) {
      setError(errorMessage(loadError))
    } finally {
      setIsLoading(false)
    }
  }, [shopId, familyFilter])

  useEffect(() => {
    let active = true
    if (!isShopLoading && shopId) queueMicrotask(() => { if (active) { setIsLoading(true); void loadDesigns() } })
    return () => { active = false }
  }, [shopId, isShopLoading, loadDesigns])

  useEffect(() => {
    const draft = (location.state as DesignNavigationState | null)?.resumeDesignDraft
    if (!draft) return
    setDesignName(draft.designName)
    setFamilyId(draft.familyId)
    setCreateOpen(true)
    setNewlyCreatedFamilyId(draft.familyId)
    navigate(`${location.pathname}${location.search}`, { replace: true, state: null })
  }, [location.pathname, location.search, location.state, navigate])

  const familyNames = useMemo(() => new Map(families.map(family => [family.id, family.name])), [families])
  const selectedFamily = families.find(family => family.id === familyFilter) ?? null
  const visibleFamilyDesigns = selectedFamily ? designs.filter(design => design.family === selectedFamily.id) : []
  const canCreateDesign = families.length > 0

  function openCreate() {
    const firstFamily = familyFilter && families.some(family => family.id === familyFilter)
      ? familyFilter
      : families[0]?.id ?? ''
    setFamilyId(firstFamily)
    setDesignName('')
    setIsAddGarmentOpen(false)
    setGarmentName('')
    setGarmentCode('')
    setGarmentError(null)
    setNewlyCreatedFamilyId('')
    setCreateOpen(true)
  }

  async function submitCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!shopId || !familyId) return
    setIsSaving(true)
    setError(null)
    try {
      await createShopDesign(shopId, { family_id: familyId, name: designName.trim() })
      setCreateOpen(false)
      await loadDesigns()
    } catch (saveError) {
      setError(errorMessage(saveError))
    } finally {
      setIsSaving(false)
    }
  }

  async function submitGarmentCreate() {
    if (!shopId || !canManageGarments || !garmentName.trim() || !garmentCode.trim()) return
    setIsCreatingGarment(true)
    setGarmentError(null)
    try {
      const created = await createShopFamily(shopId, {
        code: garmentCode.trim(),
        translations: [{ locale: 'en', name: garmentName.trim() }],
      })
      setFamilies(current => current.some(family => family.id === created.id) ? current : [...current, created])
      setFamilyId(created.id)
      setNewlyCreatedFamilyId(created.id)
      setIsAddGarmentOpen(false)
      setGarmentName('')
      setGarmentCode('')
    } catch (createError) {
      setGarmentError(errorMessage(createError))
    } finally {
      setIsCreatingGarment(false)
    }
  }

  async function handleArchive(designId: string) {
    if (!shopId || !window.confirm('Archive this design?')) return
    try {
      await archiveShopDesign(shopId, designId)
      setDesigns(current => current.filter(design => design.id !== designId))
    } catch (archiveError) {
      setError(errorMessage(archiveError))
    }
  }

  function renderDesignCard(design: Design) {
    const draft = design.latest_version?.status === 'DRAFT' ? design.latest_version : null
    const visibleVersion = draft && !hasUnpublishedChanges(draft, design.latest_published_version ?? null) && design.latest_published_version
      ? design.latest_published_version
      : design.latest_version
    return <article key={design.id} className="design-card">
      <div className="design-card-heading"><Wand2 size={20} /><Link to={`/designs/${design.id}`}>{design.name || familyNames.get(design.family) || design.family}</Link><button className="icon-button" onClick={() => void handleArchive(design.id)} title="Archive design" aria-label={`Archive ${design.name || 'design'}`}><Archive size={16} /></button></div>
      <div className="design-card-details"><span>{familyNames.get(design.family) ?? 'Garment family'}</span><span className={`design-status design-status-${design.status.toLowerCase()}`}>{design.status}</span></div>
      <p>{visibleVersion ? `Version ${visibleVersion.number} · ${visibleVersion.status.toLowerCase()}` : 'No version yet'}</p>
    </article>
  }

  function openGarment(familyId: string) {
    const next = new URLSearchParams(searchParams)
    next.set('family', familyId)
    next.delete('variant')
    setSearchParams(next)
  }

  function returnToGarments() {
    const next = new URLSearchParams(searchParams)
    next.delete('family')
    next.delete('variant')
    setSearchParams(next)
  }

  if (isShopLoading) return <div className="content-wrap design-loading"><Loader2 className="animate-spin" /></div>
  if (!shopId) return <div className="content-wrap design-error"><AlertCircle /> No authorized Shop context found.</div>

  return (
    <div className="content-wrap design-page">
      <div className="design-page-heading">
        <div className="design-page-heading-copy">
          {selectedFamily ? <><button className="design-back-button" type="button" onClick={returnToGarments}><ArrowLeft size={17} /> Designs</button><h1>{selectedFamily.name}</h1><p>Manage designs for this garment</p></> : <><h1>{t('designs.title', 'Designs')}</h1><p>{t('designs.subtitle', 'Manage your shop designs')}</p></>}
        </div>
        <button className="primary-button" onClick={openCreate} disabled={!canCreateDesign && !canManageGarments}><Plus size={16} /> New Design</button>
      </div>
      {error && <div className="design-error" role="alert">{error}<button onClick={() => { setIsLoading(true); setError(null); void loadDesigns() }} disabled={isLoading}>Retry</button></div>}
      {!isLoading && !error && !canCreateDesign && !canManageGarments && <div className="design-info-note" role="status"><AlertCircle size={18} /><span>No garment families are available in this Shop yet.</span></div>}
      {isLoading ? <div className="design-loading"><Loader2 className="animate-spin" /></div> : (
        selectedFamily ? visibleFamilyDesigns.length > 0
          ? <div className="design-grid">{visibleFamilyDesigns.map(renderDesignCard)}</div>
          : !error && <div className="design-empty-state"><Wand2 size={22} /><h2>No designs yet</h2><p>Create a design for {selectedFamily.name} to collect style selections and reference images.</p><button className="secondary-button" onClick={openCreate}><Plus size={16} /> Create first design</button></div>
          : !error && families.length > 0
            ? <div className="design-garment-grid">{families.map(family => <button key={family.id} className="design-garment-card" type="button" onClick={() => openGarment(family.id)}><Shirt size={22} aria-hidden="true" /><span>{family.name}</span><ChevronRight size={18} aria-hidden="true" /></button>)}</div>
            : !error && <div className="design-empty-state"><Shirt size={22} /><h2>No garments yet</h2><p>Add a garment to start organizing its Designs here.</p></div>
      )}

      {createOpen && <div className="design-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setCreateOpen(false) }}>
        <form className="design-dialog" onSubmit={event => void submitCreate(event)} aria-labelledby="design-create-title">
          <div className="design-dialog-heading"><h2 id="design-create-title">Create design</h2><button type="button" className="icon-button" onClick={() => setCreateOpen(false)} aria-label="Close">×</button></div>
          <label>Design name<input required maxLength={160} value={designName} onChange={event => setDesignName(event.target.value)} placeholder="For example, Summer shirt" /></label>
          <div className="design-family-field">
            <label>Garment family<ResponsiveChoice className="design-family-choice" ariaLabel="Garment family" value={familyId} onChange={setFamilyId} options={families.map(family => ({ value: family.id, label: family.name }))} required previewLimit={5} /></label>
            {canManageGarments && <button type="button" className="secondary-button design-add-garment-button" onClick={() => { setGarmentError(null); setIsAddGarmentOpen(value => !value) }}><Plus size={15} /> Add garment</button>}
          </div>
          {isAddGarmentOpen && <div className="design-add-garment-panel" aria-label="Add garment">
            <label>Garment name (English)<input value={garmentName} onChange={event => setGarmentName(event.target.value)} maxLength={120} autoComplete="off" /></label>
            <label>Code<input value={garmentCode} onChange={event => setGarmentCode(event.target.value)} maxLength={48} autoComplete="off" /></label>
            {garmentError && <div className="design-error" role="alert">{garmentError}</div>}
            <div className="design-dialog-actions"><button type="button" className="secondary-button" onClick={() => { setIsAddGarmentOpen(false); setGarmentError(null) }} disabled={isCreatingGarment}>Cancel</button><button type="button" className="primary-button" onClick={() => void submitGarmentCreate()} disabled={isCreatingGarment || !garmentName.trim() || !garmentCode.trim()}>{isCreatingGarment ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />} Create garment</button></div>
          </div>}
          {newlyCreatedFamilyId === familyId && <div className="design-configure-garment-note" role="status"><span>Garment created. Configure its style groups and measurements in Catalog before continuing.</span><button type="button" className="secondary-button" onClick={() => navigate(`/catalog?family=${encodeURIComponent(familyId)}`, { state: { returnToDesignDraft: { designName, familyId } } })}>Configure garment</button></div>}
          <div className="design-dialog-actions"><button type="button" className="secondary-button" onClick={() => setCreateOpen(false)}>Cancel</button><button type="submit" className="primary-button" disabled={isSaving || !familyId}>{isSaving ? <Loader2 size={16} className="animate-spin" /> : null} Create</button></div>
        </form>
      </div>}
    </div>
  )
}
