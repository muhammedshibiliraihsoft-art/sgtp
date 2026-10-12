import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { usePrivateImage } from '../../hooks/usePrivateImage'
import { useAuth } from '../../services/useAuth'
import { ApiError } from '../../services/apiClient'
import { getShopFamilyOptionGroups, getAllShopStyleOptions } from '../catalog/api'
import type { FamilyOptionGroupConfig, OptionGroup, StyleOption } from '../catalog/types'
import { addShopDesignSelection, getShopDesign, publishShopDesignVersion, updateShopDesignDraft, updateShopDesignSelection, uploadShopDesignReferences } from './api'
import type { Design, DesignReference, DesignSelection } from './types'
import { AlertCircle, ArrowLeft, Check, Loader2, Pencil, Upload, X } from 'lucide-react'

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
  const { shopId, role, isLoading: isShopLoading } = useCurrentShop()
  const { user } = useAuth()
  const [design, setDesign] = useState<Design | null>(null)
  const [groups, setGroups] = useState<OptionGroup[]>([])
  const [styleOptions, setStyleOptions] = useState<StyleOption[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [isPublishing, setIsPublishing] = useState(false)
  const [isAddingSelection, setIsAddingSelection] = useState(false)
  const [isSavingName, setIsSavingName] = useState(false)
  const [selectionOpen, setSelectionOpen] = useState(false)
  const [editingSelection, setEditingSelection] = useState<DesignSelection | null>(null)
  const [selectedStyleId, setSelectedStyleId] = useState('')
  const [nameOpen, setNameOpen] = useState(false)
  const [nameDraft, setNameDraft] = useState('')
  const [error, setError] = useState<string | null>(null)

  const loadDesign = useCallback(async () => {
    if (!shopId || !designId) return
    try {
      const record = await getShopDesign(shopId, designId)
      const [groupConfigs, options]: [FamilyOptionGroupConfig[], StyleOption[]] = record.latest_version ? await Promise.all([
        getShopFamilyOptionGroups(shopId, record.family), getAllShopStyleOptions(shopId),
      ]) : [[], []]
      setError(null)
      setDesign(record)
      setGroups(groupConfigs.map(config => config.option_group))
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
  const canEditDraft = isDraft && (role === 'ADMIN' || role === 'STAFF')
  const groupNames = useMemo(() => new Map(groups.map(group => [group.id, group.name])), [groups])
  const selectableGroups = useMemo(() => groups
    .map(group => ({
      ...group,
      options: styleOptions.filter(option => option.is_active && option.option_group === group.id),
    })), [styleOptions, groups, design?.family])

  const currentSelectionGroup = editingSelection?.option_group
  const modalGroups = editingSelection
    ? selectableGroups.filter(group => group.id === currentSelectionGroup)
    : selectableGroups
  const modalOptions = modalGroups.flatMap(group => group.options)

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
      if (editingSelection) {
        await updateShopDesignSelection(shopId, latest.id, editingSelection.id, { style_option_id: selectedStyleId })
      } else {
        await addShopDesignSelection(shopId, latest.id, { style_option_id: selectedStyleId })
      }
      const refreshed = await getShopDesign(shopId, designId!)
      setDesign(refreshed)
      setSelectionOpen(false)
      setEditingSelection(null)
      setSelectedStyleId('')
    } catch (selectionError) {
      setError(errorMessage(selectionError))
    } finally {
      setIsAddingSelection(false)
    }
  }

  async function handleSaveName(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!shopId || !design || !nameDraft.trim()) return
    setIsSavingName(true)
    setError(null)
    try {
      setDesign(await updateShopDesignDraft(shopId, design.id, nameDraft.trim()))
      setNameOpen(false)
    } catch (saveError) {
      setError(errorMessage(saveError))
    } finally {
      setIsSavingName(false)
    }
  }

  function openSelectionEditor(selection?: DesignSelection) {
    setEditingSelection(selection ?? null)
    setSelectedStyleId(selection?.style_option ?? '')
    setSelectionOpen(true)
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
        <div className="design-editor-title"><div><h1>{design.name || 'Design'}</h1><p>Version {latest.number} · {latest.status}</p></div>{canEditDraft && <button type="button" className="secondary-button" onClick={() => { setNameDraft(design.name); setNameOpen(true) }}><Pencil size={15} /> Edit name</button>}</div>
      </div>
      {error && <div className="design-error" role="alert">{error}<button onClick={() => { setIsLoading(true); setError(null); void loadDesign() }}>Retry</button></div>}

      <div className="design-editor-layout">
        <div className="design-editor-main">
          <section className="design-panel">
            <div className="design-panel-heading"><div><h2>Selections</h2><p className="design-muted">Garment parts and their available options come from this Shop’s Catalog configuration.</p></div>{canEditDraft && <button type="button" className="secondary-button" onClick={() => openSelectionEditor()}><Check size={15} /> Add selection</button>}</div>
            {latest.selections.length === 0 ? <p className="design-muted">No style selections yet.</p> : <ul className="design-selection-list">{latest.selections.map(selection => <li key={selection.id}><span>{groupNames.get(selection.option_group) ?? selection.option_group}</span><strong>{selection.style_option_name}</strong>{canEditDraft && <button type="button" className="secondary-button" onClick={() => openSelectionEditor(selection)}><Pencil size={14} /> Edit</button>}</li>)}</ul>}
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

      {nameOpen && <div className="design-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setNameOpen(false) }}>
        <form className="design-dialog" onSubmit={event => void handleSaveName(event)} aria-labelledby="design-name-title">
          <div className="design-dialog-heading"><h2 id="design-name-title">Edit design name</h2><button type="button" className="icon-button" onClick={() => setNameOpen(false)} aria-label="Close"><X size={18} /></button></div>
          <label>Design name<input required maxLength={160} value={nameDraft} onChange={event => setNameDraft(event.target.value)} /></label>
          <div className="design-dialog-actions"><button type="button" className="secondary-button" onClick={() => setNameOpen(false)}>Cancel</button><button className="primary-button" type="submit" disabled={isSavingName || !nameDraft.trim()}>{isSavingName ? <Loader2 className="animate-spin" size={16} /> : null} Save</button></div>
        </form>
      </div>}

      {selectionOpen && <div className="design-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) { setSelectionOpen(false); setEditingSelection(null) } }}>
        <form className="design-dialog" onSubmit={event => void handleAddSelection(event)} aria-labelledby="design-selection-title">
          <div className="design-dialog-heading"><h2 id="design-selection-title">{editingSelection ? 'Edit style selection' : 'Add style selection'}</h2><button type="button" className="icon-button" onClick={() => { setSelectionOpen(false); setEditingSelection(null) }} aria-label="Close"><X size={18} /></button></div>
          {modalOptions.length ? <div className="design-choice-groups" aria-label="Available style options">
            {modalGroups.filter(group => group.options.length > 0).map(group => <fieldset className="design-choice-group" key={group.id}>
              <legend>{group.name}<span>{group.options.length}</span></legend>
              <div className="design-choice-options">{group.options.map(option => <label className={`design-choice-option${selectedStyleId === option.id ? ' selected' : ''}`} key={option.id}>
                <input type="radio" name="style-option" required value={option.id} checked={selectedStyleId === option.id} onChange={() => setSelectedStyleId(option.id)} />
                <span><strong>{option.name}</strong><small>{option.code}</small></span>
              </label>)}</div>
            </fieldset>)}
          </div> : <div className="design-choice-empty" role="status">
            <AlertCircle size={19} />
            <p>{editingSelection
              ? 'No active Catalog options are available for this garment part. Configure options in Catalog, then return here.'
              : groups.length
                ? 'No active Catalog options are available for this garment family yet.'
                : 'No option groups are linked to this garment family yet. Configure the family’s parts in Catalog, then return here.'}</p>
          </div>}
          <div className="design-dialog-actions"><button type="button" className="secondary-button" onClick={() => { setSelectionOpen(false); setEditingSelection(null) }}>Cancel</button><button className="primary-button" type="submit" disabled={isAddingSelection || !modalOptions.length}>{isAddingSelection ? <Loader2 className="animate-spin" size={16} /> : null} {editingSelection ? 'Save selection' : 'Add'}</button></div>
        </form>
      </div>}
    </div>
  )
}
