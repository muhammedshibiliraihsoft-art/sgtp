import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { ApiError } from '../../services/apiClient'
import { getAllFamilies, getAllShopVariants } from '../catalog/api'
import type { CatalogFamily, Variant } from '../catalog/types'
import { archiveShopDesign, createShopDesign, getAllShopDesigns } from './api'
import type { Design } from './types'
import { AlertCircle, Loader2, Plus, Wand2, Archive } from 'lucide-react'
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

  const loadDesigns = useCallback(async () => {
    if (!shopId) return
    try {
      const [designRows, familyRows, variantRows] = await Promise.all([
        getAllShopDesigns(shopId, { family: familyFilter || undefined, variant: variantFilter || undefined }), getAllFamilies(), getAllShopVariants(shopId),
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
  }, [shopId, familyFilter, variantFilter])

  useEffect(() => {
    let active = true
    if (!isShopLoading && shopId) queueMicrotask(() => { if (active) { setIsLoading(true); void loadDesigns() } })
    return () => { active = false }
  }, [shopId, isShopLoading, loadDesigns])

  const familyVariants = useMemo(() => variants.filter(variant => variant.family === familyId), [variants, familyId])
  const familyNames = useMemo(() => new Map(families.map(family => [family.id, family.name])), [families])
  const variantNames = useMemo(() => new Map(variants.map(variant => [variant.id, variant.name])), [variants])
  const canCreateDesign = families.some(family => variants.some(variant => variant.family === family.id))

  function openCreate() {
    const firstFamily = familyFilter && families.some(family => family.id === familyFilter)
      ? familyFilter
      : families.find(family => variants.some(variant => variant.family === family.id))?.id ?? ''
    setFamilyId(firstFamily)
    setVariantId(variants.find(variant => variant.family === firstFamily)?.id ?? '')
    setDesignName('')
    setCreateOpen(true)
  }

  async function submitCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!shopId || !familyId || !variantId) return
    setIsSaving(true)
    setError(null)
    try {
      await createShopDesign(shopId, { family_id: familyId, variant_id: variantId, name: designName.trim() })
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

  if (isShopLoading) return <div className="content-wrap design-loading"><Loader2 className="animate-spin" /></div>
  if (!shopId) return <div className="content-wrap design-error"><AlertCircle /> No authorized Shop context found.</div>

  return (
    <div className="content-wrap design-page">
      <div className="design-page-heading">
        <div><h1>{t('designs.title', 'Designs')}</h1><p>{t('designs.subtitle', 'Manage your shop designs')}</p></div>
        <button className="primary-button" onClick={openCreate} disabled={!canCreateDesign}><Plus size={16} /> New Design</button>
      </div>
      {error && <div className="design-error" role="alert">{error}<button onClick={() => { setIsLoading(true); setError(null); void loadDesigns() }} disabled={isLoading}>Retry</button></div>}
      {familyFilter && <div className="design-info-note" role="status"><span>Showing designs for {familyNames.get(familyFilter) ?? 'selected garment family'}.</span><button className="secondary-button" type="button" onClick={() => { const next = new URLSearchParams(searchParams); next.delete('family'); setSearchParams(next) }}>Clear filter</button></div>}
      {!isLoading && !error && !canCreateDesign && <div className="design-info-note" role="status"><AlertCircle size={18} /><span>{families.length === 0
        ? 'A Main Supplier must add garment families to the global catalog before this Shop can create designs.'
        : <>This Shop needs at least one variant before it can create designs. Add a variant in <Link to="/catalog">Catalog</Link>.</>}</span></div>}
      {isLoading ? <div className="design-loading"><Loader2 className="animate-spin" /></div> : (
        <div className="design-grid">
          {designs.map(design => <article key={design.id} className="design-card">
            <div className="design-card-heading"><Wand2 size={20} /><Link to={`/designs/${design.id}`}>{design.name || `${familyNames.get(design.family) ?? design.family} · ${variantNames.get(design.variant) ?? design.variant}`}</Link><button className="icon-button" onClick={() => void handleArchive(design.id)} title="Archive design" aria-label={`Archive ${design.name || 'design'}`}><Archive size={16} /></button></div>
            <div className="design-card-details"><span>{familyNames.get(design.family) ?? 'Garment family'} <b>·</b> {variantNames.get(design.variant) ?? 'Variant'}</span><span className={`design-status design-status-${design.status.toLowerCase()}`}>{design.status}</span></div>
            <p>{design.latest_version ? `Version ${design.latest_version.number} · ${design.latest_version.status.toLowerCase()}` : 'No version yet'}</p>
          </article>)}
          {designs.length === 0 && !error && <div className="design-empty-state"><Wand2 size={22} /><h2>No designs yet</h2><p>Create a shop design to collect style selections and reference images.</p>{canCreateDesign && <button className="secondary-button" onClick={openCreate}><Plus size={16} /> Create first design</button>}</div>}
        </div>
      )}

      {createOpen && <div className="design-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setCreateOpen(false) }}>
        <form className="design-dialog" onSubmit={event => void submitCreate(event)} aria-labelledby="design-create-title">
          <div className="design-dialog-heading"><h2 id="design-create-title">Create design</h2><button type="button" className="icon-button" onClick={() => setCreateOpen(false)} aria-label="Close">×</button></div>
          <label>Design name<input required maxLength={160} value={designName} onChange={event => setDesignName(event.target.value)} placeholder="For example, Summer shirt" /></label>
          <label>Garment family<select required value={familyId} onChange={event => { setFamilyId(event.target.value); setVariantId(variants.find(variant => variant.family === event.target.value)?.id ?? '') }}>{families.map(family => <option key={family.id} value={family.id}>{family.name}</option>)}</select></label>
          <label>Variant<select required value={variantId} onChange={event => setVariantId(event.target.value)}>{familyVariants.map(variant => <option key={variant.id} value={variant.id}>{variant.name} ({variant.code})</option>)}</select>{familyId && !familyVariants.length && <small className="design-field-hint">No variants are available for this family. Choose another family or add a variant in Catalog.</small>}</label>
          <div className="design-dialog-actions"><button type="button" className="secondary-button" onClick={() => setCreateOpen(false)}>Cancel</button><button type="submit" className="primary-button" disabled={isSaving || !familyVariants.length}>{isSaving ? <Loader2 size={16} className="animate-spin" /> : null} Create</button></div>
        </form>
      </div>}
    </div>
  )
}
