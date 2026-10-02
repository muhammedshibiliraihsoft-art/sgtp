import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
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
        getAllShopDesigns(shopId), getAllFamilies(), getAllShopVariants(shopId),
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
  }, [shopId])

  useEffect(() => {
    let active = true
    if (!isShopLoading && shopId) queueMicrotask(() => { if (active) { setIsLoading(true); void loadDesigns() } })
    return () => { active = false }
  }, [shopId, isShopLoading, loadDesigns])

  const familyVariants = useMemo(() => variants.filter(variant => variant.family === familyId), [variants, familyId])
  const familyNames = useMemo(() => new Map(families.map(family => [family.id, family.name])), [families])
  const variantNames = useMemo(() => new Map(variants.map(variant => [variant.id, variant.name])), [variants])

  function openCreate() {
    const firstFamily = families[0]?.id ?? ''
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
    <div className="content-wrap">
      <div className="design-page-heading">
        <div><h1>{t('designs.title', 'Designs')}</h1><p>{t('designs.subtitle', 'Manage your shop designs')}</p></div>
        <button className="primary-button" onClick={openCreate}><Plus size={16} /> New Design</button>
      </div>
      {error && <div className="design-error" role="alert">{error}<button onClick={() => { setIsLoading(true); setError(null); void loadDesigns() }} disabled={isLoading}>Retry</button></div>}
      {isLoading ? <div className="design-loading"><Loader2 className="animate-spin" /></div> : (
        <div className="design-grid">
          {designs.map(design => <article key={design.id} className="design-card">
            <div className="design-card-heading"><Wand2 size={20} /><Link to={`/designs/${design.id}`}>{design.name || `${familyNames.get(design.family) ?? design.family} · ${variantNames.get(design.variant) ?? design.variant}`}</Link><button className="icon-button" onClick={() => void handleArchive(design.id)} title="Archive design" aria-label="Archive design"><Archive size={16} /></button></div>
            <p>Status: {design.status}</p>
            <p>Version: {design.latest_version ? `${design.latest_version.number} (${design.latest_version.status})` : 'No version'}</p>
          </article>)}
          {designs.length === 0 && <p className="design-empty">No designs found.</p>}
        </div>
      )}

      {createOpen && <div className="design-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setCreateOpen(false) }}>
        <form className="design-dialog" onSubmit={event => void submitCreate(event)} aria-labelledby="design-create-title">
          <div className="design-dialog-heading"><h2 id="design-create-title">Create design</h2><button type="button" className="icon-button" onClick={() => setCreateOpen(false)} aria-label="Close">×</button></div>
          <label>Design name<input required maxLength={160} value={designName} onChange={event => setDesignName(event.target.value)} /></label>
          <label>Garment family<select required value={familyId} onChange={event => { setFamilyId(event.target.value); setVariantId(variants.find(variant => variant.family === event.target.value)?.id ?? '') }}>{families.map(family => <option key={family.id} value={family.id}>{family.name}</option>)}</select></label>
          <label>Variant<select required value={variantId} onChange={event => setVariantId(event.target.value)}>{familyVariants.map(variant => <option key={variant.id} value={variant.id}>{variant.name} ({variant.code})</option>)}</select></label>
          <div className="design-dialog-actions"><button type="button" className="secondary-button" onClick={() => setCreateOpen(false)}>Cancel</button><button type="submit" className="primary-button" disabled={isSaving || !familyVariants.length}>{isSaving ? <Loader2 size={16} className="animate-spin" /> : null} Create</button></div>
        </form>
      </div>}
    </div>
  )
}
