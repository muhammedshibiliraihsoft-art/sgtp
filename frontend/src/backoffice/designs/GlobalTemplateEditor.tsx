import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { AlertCircle, ArrowLeft, Check, ImagePlus, Loader2, Upload, X } from 'lucide-react'
import { usePrivateImage } from '../../hooks/usePrivateImage'
import { ApiError } from '../../services/apiClient'
import { getAllGlobalStyleOptions, getOptionGroups, uploadGlobalStyleOptionImages } from '../../features/catalog/api'
import type { OptionGroup, StyleOption } from '../../features/catalog/types'
import type { Design, DesignReference } from '../../features/designs/types'
import { addGlobalDesignSelection, getGlobalDesign, getGlobalDesignReferences, publishGlobalDesignVersion, uploadGlobalDesignReferences } from './api'

function PrivateImage({ url }: { url: string }) {
  const { objectUrl, isLoading, error } = usePrivateImage(url)
  if (isLoading) return <div className="design-image-placeholder"><Loader2 className="animate-spin" /></div>
  if (error || !objectUrl) return <div className="design-image-placeholder"><AlertCircle size={20} /></div>
  return <img className="design-reference-image" src={objectUrl} alt="Template reference" />
}

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : 'Could not load the global template.'
}

export function GlobalTemplateEditor() {
  const { designId } = useParams()
  const [design, setDesign] = useState<Design | null>(null)
  const [groups, setGroups] = useState<OptionGroup[]>([])
  const [styleOptions, setStyleOptions] = useState<StyleOption[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadingStyleOptionId, setUploadingStyleOptionId] = useState<string | null>(null)
  const [isPublishing, setIsPublishing] = useState(false)
  const [isAdding, setIsAdding] = useState(false)
  const [selectionOpen, setSelectionOpen] = useState(false)
  const [selectedStyleId, setSelectedStyleId] = useState('')
  const [error, setError] = useState<string | null>(null)

  const loadDesign = useCallback(async () => {
    if (!designId) return
    try {
      const [record, groupRows, stylePage] = await Promise.all([
        getGlobalDesign(designId), getOptionGroups(), getAllGlobalStyleOptions(),
      ])
      setError(null)
      setDesign(record)
      setGroups(groupRows)
      setStyleOptions(stylePage)
    } catch (loadError) {
      setError(errorMessage(loadError))
      setDesign(null)
    } finally {
      setIsLoading(false)
    }
  }, [designId])

  useEffect(() => {
    let active = true
    queueMicrotask(() => { if (active) { setIsLoading(true); void loadDesign() } })
    return () => { active = false }
  }, [loadDesign])

  const latest = design?.latest_version
  const isDraft = latest?.status === 'DRAFT'
  const groupNames = useMemo(() => new Map(groups.map(group => [group.id, group.name])), [groups])
  const selectableOptions = useMemo(() => styleOptions.filter(option => {
    const optionGroup = groups.find(group => group.id === option.option_group)
    return option.is_active && Boolean(optionGroup?.families.includes(design?.family ?? ''))
  }), [styleOptions, groups, design?.family])

  async function handlePublish() {
    if (!designId || !latest) return
    setIsPublishing(true)
    setError(null)
    try {
      const result = await publishGlobalDesignVersion(designId, latest.id)
      setDesign(current => current ? { ...current, latest_version: result.next_draft } : current)
    } catch (publishError) {
      setError(errorMessage(publishError))
    } finally {
      setIsPublishing(false)
    }
  }

  async function handleAddSelection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!designId || !latest || !selectedStyleId) return
    setIsAdding(true)
    setError(null)
    try {
      await addGlobalDesignSelection(designId, latest.id, { style_option_id: selectedStyleId })
      setDesign(await getGlobalDesign(designId))
      setSelectionOpen(false)
      setSelectedStyleId('')
    } catch (selectionError) {
      setError(errorMessage(selectionError))
    } finally {
      setIsAdding(false)
    }
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? [])
    if (!files.length || !designId || !latest) return
    setIsUploading(true)
    setError(null)
    try {
      await uploadGlobalDesignReferences(designId, latest.id, files)
      const [record, references] = await Promise.all([getGlobalDesign(designId), getGlobalDesignReferences(designId, latest.id)])
      setDesign(record.latest_version ? { ...record, latest_version: { ...record.latest_version, references } } : record)
    } catch (uploadError) {
      setError(errorMessage(uploadError))
    } finally {
      setIsUploading(false)
      event.target.value = ''
    }
  }

  async function handleStyleOptionImageUpload(styleOptionId: string, event: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? [])
    if (!files.length) return
    setUploadingStyleOptionId(styleOptionId)
    setError(null)
    try {
      await uploadGlobalStyleOptionImages(styleOptionId, files)
      setStyleOptions(await getAllGlobalStyleOptions())
    } catch (uploadError) {
      setError(errorMessage(uploadError))
    } finally {
      setUploadingStyleOptionId(null)
      event.target.value = ''
    }
  }

  if (isLoading) return <div className="content-wrap design-loading"><Loader2 className="animate-spin" /></div>
  if (!design || !latest) return <div className="content-wrap design-error" role="alert">{error ?? 'Global template not found.'}</div>

  return (
    <div className="content-wrap">
      <div className="design-editor-heading"><Link to="/backoffice/designs" className="icon-button" aria-label="Back to templates"><ArrowLeft size={20} /></Link><div><h1>{design.name || 'Global template'}</h1><p>Version {latest.number} · {latest.status}</p></div></div>
      {error && <div className="design-error" role="alert">{error}<button onClick={() => { setIsLoading(true); setError(null); void loadDesign() }}>Retry</button></div>}
      <div className="design-editor-layout">
        <div className="design-editor-main">
          <section className="design-panel">
            <div className="design-panel-heading"><h2>Selections</h2>{isDraft && <button className="secondary-button" onClick={() => setSelectionOpen(true)}><Check size={15} /> Add selection</button>}</div>
            {latest.selections.length === 0 ? <p className="design-muted">No style selections yet.</p> : <ul className="design-selection-list">{latest.selections.map(selection => <li key={selection.id}><span>{groupNames.get(selection.option_group) ?? selection.option_group}</span><strong>{selection.style_option_name}</strong>{isDraft && <label className="secondary-button design-upload">{uploadingStyleOptionId === selection.style_option ? <Loader2 className="animate-spin" size={15} /> : <ImagePlus size={15} />} Add reusable image<input aria-label={`Add reusable image for ${selection.style_option_name}`} type="file" accept="image/jpeg,image/png,image/webp" multiple hidden disabled={uploadingStyleOptionId === selection.style_option} onChange={event => void handleStyleOptionImageUpload(selection.style_option, event)} /></label>}</li>)}</ul>}
          </section>
          <section className="design-panel">
            <div className="design-panel-heading"><h2>Reference images</h2>{isDraft && <label className="secondary-button design-upload">{isUploading ? <Loader2 className="animate-spin" size={16} /> : <Upload size={16} />} Upload<input type="file" accept="image/jpeg,image/png,image/webp" multiple hidden disabled={isUploading} onChange={event => void handleUpload(event)} /></label>}</div>
            {latest.references.length === 0 ? <p className="design-muted">No reference images yet.</p> : <div className="design-reference-grid">{latest.references.map((reference: DesignReference) => <PrivateImage key={reference.id} url={reference.content_url} />)}</div>}
          </section>
        </div>
        <aside className="design-panel design-actions-panel"><h2>Actions</h2>{isDraft ? <button className="primary-button" onClick={() => void handlePublish()} disabled={isPublishing}>{isPublishing ? <Loader2 className="animate-spin" size={16} /> : <Check size={16} />} Publish template</button> : <p className="design-muted">Published versions are immutable. Publishing creates a new draft.</p>}</aside>
      </div>
      {selectionOpen && <div className="design-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setSelectionOpen(false) }}>
        <form className="design-dialog" onSubmit={event => void handleAddSelection(event)} aria-labelledby="global-selection-title">
          <div className="design-dialog-heading"><h2 id="global-selection-title">Add style selection</h2><button type="button" className="icon-button" onClick={() => setSelectionOpen(false)} aria-label="Close"><X size={18} /></button></div>
          <label>Global style option<select required value={selectedStyleId} onChange={event => setSelectedStyleId(event.target.value)}><option value="">Choose an option</option>{selectableOptions.map(option => <option key={option.id} value={option.id}>{groupNames.get(option.option_group) ?? option.option_group} · {option.name}</option>)}</select></label>
          <div className="design-dialog-actions"><button type="button" className="secondary-button" onClick={() => setSelectionOpen(false)}>Cancel</button><button type="submit" className="primary-button" disabled={isAdding || !selectableOptions.length}>{isAdding ? <Loader2 className="animate-spin" size={16} /> : null} Add</button></div>
        </form>
      </div>}
    </div>
  )
}
