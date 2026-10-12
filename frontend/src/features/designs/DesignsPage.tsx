import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { ApiError } from '../../services/apiClient'
import { getAllShopGarmentFamilies, getAllShopVariants } from '../catalog/api'
import type { CatalogFamily, Variant } from '../catalog/types'
import { archiveShopDesign, createShopDesign, getAllShopDesigns, restoreShopDefaultDesign } from './api'
import type { Design } from './types'
import { AlertCircle, ArrowLeft, ArrowRight, Loader2, Plus, Search, Shirt, Wand2, Archive, RotateCcw } from 'lucide-react'
import './Designs.css'

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : 'Could not load designs. Please try again.'
}

export function DesignsPage() {
  const { t } = useTranslation()
  const { shopId, isLoading: isShopLoading } = useCurrentShop()
  const [searchParams, setSearchParams] = useSearchParams()
  const familyFilter = searchParams.get('family') || ''
  const variantFilter = searchParams.get('variant') || ''
  const [designs, setDesigns] = useState<Design[]>([])
  const [families, setFamilies] = useState<CatalogFamily[]>([])
  const [variants, setVariants] = useState<Variant[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [familyId, setFamilyId] = useState('')
  const [variantId, setVariantId] = useState('')
  const [designName, setDesignName] = useState('')
  const [showArchived, setShowArchived] = useState(false)
  const [familySearch, setFamilySearch] = useState('')

  const loadDesigns = useCallback(async () => {
    if (!shopId) return
    try {
      const [designRows, familyRows, variantRows] = await Promise.all([
        getAllShopDesigns(shopId, { family: familyFilter || undefined, variant: variantFilter || undefined }, 'en', showArchived ? 'ARCHIVED' : 'ACTIVE'), getAllShopGarmentFamilies(shopId), getAllShopVariants(shopId),
      ])
      setError(null)
      setDesigns(designRows)
      setFamilies(familyRows)
      setVariants(variantRows)
    } catch (loadError) {
      setError(errorMessage(loadError))
    } finally {
      setIsLoading(false)
    }
  }, [shopId, familyFilter, variantFilter, showArchived])

  useEffect(() => {
    let active = true
    if (!isShopLoading && shopId) queueMicrotask(() => { if (active) { setIsLoading(true); void loadDesigns() } })
    return () => { active = false }
  }, [shopId, isShopLoading, loadDesigns])

  const familyVariants = useMemo(() => variants.filter(variant => variant.family === familyId), [variants, familyId])
  const familyNames = useMemo(() => new Map(families.map(family => [family.id, family.name])), [families])
  const variantNames = useMemo(() => new Map(variants.map(variant => [variant.id, variant.name])), [variants])
  const selectedFamily = families.find(family => family.id === familyFilter) ?? null
  const visibleFamilies = useMemo(() => families.filter(family => !familySearch.trim() || `${family.name} ${family.code}`.toLocaleLowerCase().includes(familySearch.trim().toLocaleLowerCase())), [families, familySearch])
  const canCreateDesign = families.length > 0

  function openCreate() {
    const firstFamily = familyFilter && families.some(family => family.id === familyFilter)
      ? familyFilter
      : families[0]?.id ?? ''
    setFamilyId(firstFamily)
    setVariantId(variants.find(variant => variant.family === firstFamily)?.id ?? '')
    setDesignName('')
    setCreateOpen(true)
  }

  async function submitCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!shopId || !familyId) return
    setIsSaving(true)
    setError(null)
    try {
      await createShopDesign(shopId, { family_id: familyId, variant_id: variantId || null, name: designName.trim() })
      setCreateOpen(false)
      await loadDesigns()
    } catch (saveError) {
      setError(errorMessage(saveError))
    } finally {
      setIsSaving(false)
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

  async function handleRestore(designId: string) {
    if (!shopId) return
    try {
      await restoreShopDefaultDesign(shopId, designId)
      await loadDesigns()
    } catch (restoreError) {
      setError(errorMessage(restoreError))
    }
  }

  if (isShopLoading) return <div className="content-wrap design-loading"><Loader2 className="animate-spin" /></div>
  if (!shopId) return <div className="content-wrap design-error"><AlertCircle /> No authorized Shop context found.</div>

  return (
    <div className="content-wrap design-page">
      <div className="design-page-heading">
        <div><h1>{selectedFamily?.name ?? t('designs.title', 'Designs')}</h1><p>{selectedFamily ? `Designs for ${selectedFamily.name}` : t('designs.subtitle', 'Manage your shop designs')}</p></div>
        <div className="design-heading-actions">{familyFilter && <button className="secondary-button" type="button" onClick={() => { const next = new URLSearchParams(searchParams); next.delete('family'); next.delete('variant'); setSearchParams(next) }}><ArrowLeft size={16} /> Garment families</button>}<button className="secondary-button" type="button" onClick={() => setShowArchived(value => !value)}>{showArchived ? 'Show active designs' : 'Show archived designs'}</button>{familyFilter && !showArchived && <button className="primary-button" onClick={openCreate} disabled={!canCreateDesign}><Plus size={16} /> New Design</button>}</div>
      </div>
      {error && <div className="design-error" role="alert">{error}<button onClick={() => { setIsLoading(true); setError(null); void loadDesigns() }} disabled={isLoading}>Retry</button></div>}
      {!isLoading && !error && !canCreateDesign && <div className="design-info-note" role="status"><AlertCircle size={18} /><span>{families.length === 0
        ? 'A Main Supplier must add garment families to the global catalog before this Shop can create designs.'
        : 'Create a Shop garment family in Catalog before adding a design.'}</span></div>}
      {isLoading ? <div className="design-loading"><Loader2 className="animate-spin" /></div> : !familyFilter ? <>
        <label className="design-family-search"><Search size={17} aria-hidden="true" /><span className="sr-only">Search garment families</span><input value={familySearch} onChange={event => setFamilySearch(event.target.value)} placeholder="Search garment families" /></label>
        <div className="design-family-grid">
          {visibleFamilies.map(family => {
            const count = designs.filter(design => design.family === family.id).length
            return <button key={family.id} type="button" className="design-family-card" onClick={() => { const next = new URLSearchParams(searchParams); next.set('family', family.id); next.delete('variant'); setSearchParams(next) }}>
              <Shirt size={22} aria-hidden="true" />
              <span><strong>{family.name}</strong><small>{family.code}</small></span>
              <span className="design-family-count">{count} {showArchived ? (count === 1 ? 'archived design' : 'archived designs') : (count === 1 ? 'design' : 'designs')}</span>
              <ArrowRight size={17} aria-hidden="true" />
            </button>
          })}
          {visibleFamilies.length === 0 && <div className="design-empty-state"><Shirt size={22} /><h2>{familySearch ? 'No garment families match' : 'No garment families yet'}</h2><p>{familySearch ? 'Try a different name or code.' : 'Add or enable garment families in Catalog, then create designs for them here.'}</p></div>}
        </div>
      </> : (
        <div className="design-grid">
          {designs.map(design => <article key={design.id} className="design-card">
            <div className="design-card-heading">
              <Wand2 size={20} />
              <Link to={`/designs/${design.id}`}>{design.name || `${familyNames.get(design.family) ?? design.family}${design.variant ? ` · ${variantNames.get(design.variant) ?? design.variant}` : ''}`}</Link>
              {showArchived ? (
                design.is_default_seeded ? (
                  <button className="icon-button" onClick={() => void handleRestore(design.id)} title="Restore latest default" aria-label={`Restore ${design.name || 'design'} from latest default`}><RotateCcw size={16} /></button>
                ) : null
              ) : (
                <button className="icon-button" onClick={() => void handleArchive(design.id)} title="Archive design" aria-label={`Archive ${design.name || 'design'}`}><Archive size={16} /></button>
              )}
            </div>
            <div className="design-card-details"><span>{familyNames.get(design.family) ?? 'Garment family'}{design.variant ? <> <b>·</b> {variantNames.get(design.variant) ?? 'Variant'}</> : ' · Family-level'}</span><span className={`design-status design-status-${design.status.toLowerCase()}`}>{design.status}</span></div>
            <p>{design.latest_version ? `Version ${design.latest_version.number} · ${design.latest_version.status.toLowerCase()}` : 'No version yet'}</p>
          </article>)}
          {designs.length === 0 && !error && <div className="design-empty-state"><Wand2 size={22} /><h2>{showArchived ? 'No archived designs for this garment' : 'No designs for this garment yet'}</h2>{!showArchived && <><p>Create a design to collect style selections and reference images for {selectedFamily?.name ?? 'this garment'}.</p>{canCreateDesign && <button className="secondary-button" onClick={openCreate}><Plus size={16} /> Create first design</button>}</>}</div>}
        </div>
      )}

      {createOpen && <div className="design-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setCreateOpen(false) }}>
        <form className="design-dialog" onSubmit={event => void submitCreate(event)} aria-labelledby="design-create-title">
          <div className="design-dialog-heading"><h2 id="design-create-title">Create design</h2><button type="button" className="icon-button" onClick={() => setCreateOpen(false)} aria-label="Close">×</button></div>
          <label>Design name<input required maxLength={160} value={designName} onChange={event => setDesignName(event.target.value)} placeholder="For example, Summer shirt" /></label>
          {selectedFamily ? <p className="design-selected-family"><Shirt size={17} /> {selectedFamily.name}</p> : <label>Garment family<select required value={familyId} onChange={event => { setFamilyId(event.target.value); setVariantId(variants.find(variant => variant.family === event.target.value)?.id ?? '') }}>{families.map(family => <option key={family.id} value={family.id}>{family.name}</option>)}</select></label>}
          <label>Variant (optional)<select value={variantId} onChange={event => setVariantId(event.target.value)}><option value="">Family-level design</option>{familyVariants.map(variant => <option key={variant.id} value={variant.id}>{variant.name} ({variant.code})</option>)}</select><small className="design-field-hint">Choose a variant to scope the design, or leave it at family level.</small></label>
          <div className="design-dialog-actions"><button type="button" className="secondary-button" onClick={() => setCreateOpen(false)}>Cancel</button><button type="submit" className="primary-button" disabled={isSaving || !familyId}>{isSaving ? <Loader2 size={16} className="animate-spin" /> : null} Create</button></div>
        </form>
      </div>}
    </div>
  )
}
