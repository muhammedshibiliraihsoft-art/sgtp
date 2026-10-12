import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Archive, Loader2, Plus, Shirt, Wand2, X } from 'lucide-react'
import { getAllFamilies, getAllGlobalVariants } from '../../features/catalog/api'
import type { CatalogFamily, Variant } from '../../features/catalog/types'
import { ApiError } from '../../services/apiClient'
import type { Design } from '../../features/designs/types'
import { archiveGlobalDesign, createGlobalDesign, getAllGlobalDesigns } from './api'
import '../../features/designs/Designs.css'

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : 'Could not load global templates.'
}

export function GlobalDesignTemplatesPage() {
  const navigate = useNavigate()
  const [designs, setDesigns] = useState<Design[]>([])
  const [families, setFamilies] = useState<CatalogFamily[]>([])
  const [variants, setVariants] = useState<Variant[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isLoadingFamilies, setIsLoadingFamilies] = useState(false)
  const [isLoadingVariants, setIsLoadingVariants] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [familyId, setFamilyId] = useState('')
  const [variantId, setVariantId] = useState('')
  const [designName, setDesignName] = useState('')
  const [error, setError] = useState<string | null>(null)

  const loadDesigns = useCallback(async () => {
    try {
      setDesigns(await getAllGlobalDesigns())
      setError(null)
    } catch (loadError) {
      setError(errorMessage(loadError))
    } finally {
      setIsLoading(false)
    }
  }, [])

  const familyVariants = useMemo(() => variants.filter(variant => variant.family === familyId), [variants, familyId])

  useEffect(() => {
    if (!isCreateOpen || !familyId) {
      setVariants([])
      setVariantId('')
      return
    }
    let active = true
    setIsLoadingVariants(true)
    setVariants([])
    setVariantId('')
    void getAllGlobalVariants(familyId).then(rows => {
      if (active) setVariants(rows)
    }).catch(loadError => {
      if (active) setError(errorMessage(loadError))
    }).finally(() => {
      if (active) setIsLoadingVariants(false)
    })
    return () => { active = false }
  }, [familyId, isCreateOpen])

  async function openCreate() {
    setError(null)
    setIsCreateOpen(true)
    setIsLoadingFamilies(true)
    try {
      const rows = await getAllFamilies()
      setFamilies(rows)
      setFamilyId(rows[0]?.id ?? '')
      setDesignName('')
    } catch (loadError) {
      setError(errorMessage(loadError))
    } finally {
      setIsLoadingFamilies(false)
    }
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!familyId || !designName.trim()) return
    setIsSaving(true)
    setError(null)
    try {
      const created = await createGlobalDesign({ family_id: familyId, variant_id: variantId || null, name: designName.trim() })
      setIsCreateOpen(false)
      navigate(`/backoffice/designs/${created.id}`)
    } catch (createError) {
      setError(errorMessage(createError))
    } finally {
      setIsSaving(false)
    }
  }

  useEffect(() => {
    let active = true
    queueMicrotask(() => { if (active) void loadDesigns() })
    return () => { active = false }
  }, [loadDesigns])

  async function handleArchive(designId: string) {
    if (!window.confirm('Archive this global template?')) return
    try {
      await archiveGlobalDesign(designId)
      setDesigns(current => current.filter(design => design.id !== designId))
    } catch (archiveError) {
      setError(errorMessage(archiveError))
    }
  }

  return (
    <div className="content-wrap">
      <div className="design-page-heading"><div><h1>Global Design Templates</h1><p>Published global templates are available to Shops.</p></div><button type="button" className="primary-button" onClick={() => void openCreate()} disabled={isLoadingFamilies}><Plus size={16} /> New Global Design</button></div>
      {error && <div className="design-error" role="alert">{error}<button onClick={() => { setIsLoading(true); setError(null); void loadDesigns() }} disabled={isLoading}>Retry</button></div>}
      {isLoading ? <div className="design-loading"><Loader2 className="animate-spin" /></div> : <div className="design-grid">
        {designs.map((design: Design) => <article key={design.id} className="design-card">
          <div className="design-card-heading"><Wand2 size={20} /><Link to={`/backoffice/designs/${design.id}`}>{design.name || design.id}</Link><button className="icon-button" onClick={() => void handleArchive(design.id)} title="Archive template" aria-label="Archive template"><Archive size={16} /></button></div>
          <p>Status: {design.status}</p><p>Version: {design.latest_version ? `${design.latest_version.number} (${design.latest_version.status})` : 'No version'}</p>
        </article>)}
        {designs.length === 0 && <p className="design-empty">No active global templates found.</p>}
      </div>}
      {isCreateOpen && <div className="design-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget && !isSaving) setIsCreateOpen(false) }}>
        <form className="design-dialog" onSubmit={event => void handleCreate(event)} aria-labelledby="global-design-create-title">
          <div className="design-dialog-heading"><h2 id="global-design-create-title">Create Global Design Template</h2><button type="button" className="icon-button" onClick={() => setIsCreateOpen(false)} disabled={isSaving} aria-label="Close"><X size={18} /></button></div>
          {error && <div className="design-error" role="alert">{error}</div>}
          {isLoadingFamilies ? <div className="design-loading"><Loader2 className="animate-spin" /></div> : families.length === 0 ? <p className="design-muted">No active global garment families are available. Add one in Global Catalog first.</p> : <>
            <label>Design name<input required maxLength={160} value={designName} onChange={event => setDesignName(event.target.value)} placeholder="For example, Classic Formal Shirt" /></label>
            <label>Garment family<select required value={familyId} onChange={event => setFamilyId(event.target.value)}>{families.map(family => <option key={family.id} value={family.id}>{family.name}</option>)}</select></label>
            <label>Variant (optional)<select value={variantId} onChange={event => setVariantId(event.target.value)} disabled={isLoadingVariants}><option value="">Family-level design</option>{familyVariants.map(variant => <option key={variant.id} value={variant.id}>{variant.name} ({variant.code})</option>)}</select><small className="design-field-hint">{isLoadingVariants ? 'Loading variants for this family…' : 'Choose a global variant or leave this as a family-level design.'}</small></label>
          </>}
          <div className="design-dialog-actions"><button type="button" className="secondary-button" onClick={() => setIsCreateOpen(false)} disabled={isSaving}>Cancel</button><button type="submit" className="primary-button" disabled={isSaving || isLoadingFamilies || isLoadingVariants || !families.length || !familyId || !designName.trim()}>{isSaving ? <Loader2 className="animate-spin" size={16} /> : <Shirt size={16} />} Create draft</button></div>
        </form>
      </div>}
    </div>
  )
}
