import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { usePrivateImage } from '../../hooks/usePrivateImage'
import { useAuth } from '../../services/useAuth'
import { ApiError } from '../../services/apiClient'
import { getOptionGroups, getAllShopStyleOptions } from '../catalog/api'
import type { OptionGroup, StyleOption } from '../catalog/types'
import { addShopDesignSelection, getShopDesign, publishShopDesignVersion, uploadShopDesignReferences } from './api'
import type { Design, DesignReference } from './types'
import { AlertCircle, ArrowLeft, Check, Loader2, Upload, X } from 'lucide-react'

function PrivateImage({ url }: { url: string }) {
  const { objectUrl, isLoading, error } = usePrivateImage(url)
  if (isLoading) return <div className="design-image-placeholder"><Loader2 className="animate-spin" /></div>
  if (error || !objectUrl) return <div className="design-image-placeholder"><AlertCircle size={20} /></div>
  return <img className="design-reference-image" src={objectUrl} alt="Design reference" />
}

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : 'Could not load the design.'
}

export function DesignEditor() {
  const { designId } = useParams()
  const { shopId, isLoading: isShopLoading } = useCurrentShop()
  const { user } = useAuth()
  const [design, setDesign] = useState<Design | null>(null)
  const [groups, setGroups] = useState<OptionGroup[]>([])
  const [styleOptions, setStyleOptions] = useState<StyleOption[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [isPublishing, setIsPublishing] = useState(false)
  const [isAddingSelection, setIsAddingSelection] = useState(false)
  const [selectionOpen, setSelectionOpen] = useState(false)
  const [selectedStyleId, setSelectedStyleId] = useState('')
  const [error, setError] = useState<string | null>(null)

  const loadDesign = useCallback(async () => {
    if (!shopId || !designId) return
    try {
      const [record, groupRows, options] = await Promise.all([
        getShopDesign(shopId, designId), getOptionGroups(), getAllShopStyleOptions(shopId),
      ])
      setError(null)
      setDesign(record)
      setGroups(groupRows)
      setStyleOptions(options)
    } catch (loadError) {
      setError(errorMessage(loadError))
      setDesign(null)
    } finally {
      setIsLoading(false)
    }
  }, [shopId, designId])

  useEffect(() => {
    let active = true
    if (!isShopLoading) queueMicrotask(() => { if (active) { setIsLoading(true); void loadDesign() } })
    return () => { active = false }
  }, [shopId, designId, isShopLoading, loadDesign])

  const latest = design?.latest_version
  const isDraft = latest?.status === 'DRAFT'
  const groupNames = useMemo(() => new Map(groups.map(group => [group.id, group.name])), [groups])
  const selectableGroups = useMemo(() => groups
    .filter(group => group.families.includes(design?.family ?? ''))
    .map(group => ({
      ...group,
      options: styleOptions.filter(option => option.is_active && option.option_group === group.id),
    })), [styleOptions, groups, design?.family])
  const selectableOptions = useMemo(() => selectableGroups.flatMap(group => group.options), [selectableGroups])

  async function handlePublish() {
    if (!shopId || !latest) return
    setIsPublishing(true)
    setError(null)
    try {
      const result = await publishShopDesignVersion(shopId, latest.id)
      setDesign(current => current ? { ...current, latest_version: result.next_draft } : current)
    } catch (publishError) {
      setError(errorMessage(publishError))
    } finally {
      setIsPublishing(false)
    }
  }

  async function handleAddSelection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!shopId || !latest || !selectedStyleId) return
    setIsAddingSelection(true)
    setError(null)
    try {
      await addShopDesignSelection(shopId, latest.id, { style_option_id: selectedStyleId })
      const refreshed = await getShopDesign(shopId, designId!)
      setDesign(refreshed)
      setSelectionOpen(false)
      setSelectedStyleId('')
    } catch (selectionError) {
      setError(errorMessage(selectionError))
    } finally {
      setIsAddingSelection(false)
    }
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? [])
    if (!files.length || !shopId || !latest) return
    setIsUploading(true)
    setError(null)
    try {
      await uploadShopDesignReferences(shopId, latest.id, files)
      setDesign(await getShopDesign(shopId, designId!))
    } catch (uploadError) {
      setError(errorMessage(uploadError))
    } finally {
      setIsUploading(false)
      event.target.value = ''
    }
  }

  if (isShopLoading || isLoading) return <div className="content-wrap design-loading"><Loader2 className="animate-spin" /></div>
  if (!shopId || !design || !latest) return <div className="content-wrap design-error" role="alert">{error ?? 'Design not found.'}</div>

  const canPublish = user?.is_main_supplier_admin === false
  const allReferences = latest.references

  return (
    <div className="content-wrap design-page">
      <div className="design-editor-heading">
        <Link to="/designs" className="icon-button" aria-label="Back to designs"><ArrowLeft size={20} /></Link>
        <div><h1>{design.name || 'Design'}</h1><p>Version {latest.number} · {latest.status}</p></div>
      </div>
      {error && <div className="design-error" role="alert">{error}<button onClick={() => { setIsLoading(true); setError(null); void loadDesign() }}>Retry</button></div>}

      <div className="design-editor-layout">
        <div className="design-editor-main">
          <section className="design-panel">
            <div className="design-panel-heading"><h2>Selections</h2>{isDraft && <button className="secondary-button" onClick={() => setSelectionOpen(true)}><Check size={15} /> Add selection</button>}</div>
            {latest.selections.length === 0 ? <p className="design-muted">No style selections yet.</p> : <ul className="design-selection-list">{latest.selections.map(selection => <li key={selection.id}><span>{groupNames.get(selection.option_group) ?? selection.option_group}</span><strong>{selection.style_option_name}</strong></li>)}</ul>}
          </section>

          <section className="design-panel">
            <div className="design-panel-heading"><h2>Reference images</h2>{isDraft && <label className="secondary-button design-upload">{isUploading ? <Loader2 className="animate-spin" size={16} /> : <Upload size={16} />} Upload<input type="file" accept="image/jpeg,image/png,image/webp" multiple hidden disabled={isUploading} onChange={event => void handleUpload(event)} /></label>}</div>
            {allReferences.length === 0 ? <p className="design-muted">No reference images yet.</p> : <div className="design-reference-grid">{allReferences.map((reference: DesignReference) => <PrivateImage key={reference.id} url={reference.content_url} />)}</div>}
          </section>
        </div>
        <aside className="design-panel design-actions-panel">
          <h2>Actions</h2>
          {isDraft ? <><button className="primary-button" onClick={() => void handlePublish()} disabled={isPublishing || !canPublish}>{isPublishing ? <Loader2 className="animate-spin" size={16} /> : <Check size={16} />} Publish version</button>{!canPublish && <p className="design-muted">Publishing is available to authorized Shop staff only.</p>}</> : <p className="design-muted">Published versions cannot be changed. Publishing creates a new draft snapshot.</p>}
        </aside>
      </div>

      {selectionOpen && <div className="design-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setSelectionOpen(false) }}>
        <form className="design-dialog" onSubmit={event => void handleAddSelection(event)} aria-labelledby="design-selection-title">
          <div className="design-dialog-heading"><h2 id="design-selection-title">Add style selection</h2><button type="button" className="icon-button" onClick={() => setSelectionOpen(false)} aria-label="Close"><X size={18} /></button></div>
          {selectableOptions.length ? <div className="design-choice-groups" aria-label="Available style options">
            {selectableGroups.filter(group => group.options.length > 0).map(group => <fieldset className="design-choice-group" key={group.id}>
              <legend>{group.name}<span>{group.options.length}</span></legend>
              <div className="design-choice-options">{group.options.map(option => <label className={`design-choice-option${selectedStyleId === option.id ? ' selected' : ''}`} key={option.id}>
                <input type="radio" name="style-option" required value={option.id} checked={selectedStyleId === option.id} onChange={() => setSelectedStyleId(option.id)} />
                <span><strong>{option.name}</strong><small>{option.code}</small></span>
              </label>)}</div>
            </fieldset>)}
          </div> : <div className="design-choice-empty" role="status">
            <AlertCircle size={19} />
            <p>{selectableGroups.length
              ? 'No active style options are available for this garment family yet.'
              : 'No option groups are linked to this garment family yet. Ask your Main Supplier to configure the family options.'}</p>
          </div>}
          <div className="design-dialog-actions"><button type="button" className="secondary-button" onClick={() => setSelectionOpen(false)}>Cancel</button><button className="primary-button" type="submit" disabled={isAddingSelection || !selectableOptions.length}>{isAddingSelection ? <Loader2 className="animate-spin" size={16} /> : null} Add</button></div>
        </form>
      </div>}
    </div>
  )
}
