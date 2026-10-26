import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { usePrivateImage } from '../../hooks/usePrivateImage'
import { useSelectAndAdvance } from '../../hooks/useSelectAndAdvance'
import { useAuth } from '../../services/useAuth'
import { ApiError } from '../../services/apiClient'
import { billingApi } from '../billing/api'
import { getShopFamilyOptionGroups, getAllShopStyleOptions } from '../catalog/api'
import type { FamilyOptionGroupConfig, StyleOption } from '../catalog/types'
import { addShopDesignSelection, getShopDesign, publishShopDesignVersion, removeUnmappedShopDesignSelection, updateShopDesignSelection, uploadShopDesignReferences } from './api'
import type { Design, DesignReference, DesignSelection } from './types'
import { hasUnpublishedChanges } from './versionState'
import { AlertCircle, ArrowLeft, Check, ImageOff, Loader2, Pencil, Upload, X } from 'lucide-react'
import './Designs.css'

type StyleImage = { content_url: string; alt_text?: string | null }

function StyleOptionThumbnail({ image, alt }: { image?: StyleImage; alt: string }) {
  const frameRef = useRef<HTMLSpanElement>(null)
  const [isNearViewport, setIsNearViewport] = useState(false)
  const { objectUrl, isLoading, error } = usePrivateImage(isNearViewport ? image?.content_url : null)

  useEffect(() => {
    if (!image?.content_url || isNearViewport) return
    const frame = frameRef.current
    if (!frame || typeof IntersectionObserver === 'undefined') {
      setIsNearViewport(true)
      return
    }
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsNearViewport(true)
        observer.disconnect()
      }
    }, { rootMargin: '120px' })
    observer.observe(frame)
    return () => observer.disconnect()
  }, [image?.content_url, isNearViewport])

  return <span ref={frameRef} className="design-option-thumbnail" aria-hidden="true">
    {objectUrl && !error
      ? <img src={objectUrl} alt={image?.alt_text || alt} loading="lazy" />
      : isLoading
        ? <span className="design-option-thumbnail-skeleton" />
        : <ImageOff size={17} />}
  </span>
}

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
  const { shop, shopId, role, workFunctions, isLoading: isShopLoading } = useCurrentShop()
  const { user } = useAuth()
  const [design, setDesign] = useState<Design | null>(null)
  const [groups, setGroups] = useState<FamilyOptionGroupConfig[]>([])
  const [styleOptions, setStyleOptions] = useState<StyleOption[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [isPublishing, setIsPublishing] = useState(false)
  const [isRemovingUnmapped, setIsRemovingUnmapped] = useState(false)
  const [isAddingSelection, setIsAddingSelection] = useState(false)
  const [selectionOpen, setSelectionOpen] = useState(false)
  const [editingSelectionId, setEditingSelectionId] = useState<string | null>(null)
  const [draftSelections, setDraftSelections] = useState<Record<string, string[]>>({})
  const [selectionStep, setSelectionStep] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [designPrice, setDesignPrice] = useState('')
  const [savedDesignPrice, setSavedDesignPrice] = useState<string | null>(null)
  const [priceError, setPriceError] = useState<string | null>(null)
  const [isPriceLoading, setIsPriceLoading] = useState(false)
  const [isPriceSaving, setIsPriceSaving] = useState(false)
  const canManagePrice = role === 'ADMIN' || (role === 'STAFF' && workFunctions.includes('CASHIER'))

  const loadPrice = useCallback(async () => {
    if (!shopId || !designId) return
    setIsPriceLoading(true)
    setPriceError(null)
    try {
      const current = await billingApi.getDesignPrice(shopId, designId)
      setSavedDesignPrice(current.amount)
      setDesignPrice(current.amount)
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 404) {
        setSavedDesignPrice(null)
        setDesignPrice('')
      } else {
        setPriceError(errorMessage(cause))
      }
    } finally { setIsPriceLoading(false) }
  }, [shopId, designId])

  const loadDesign = useCallback(async () => {
    if (!shopId || !designId) return
    try {
      const [record, options] = await Promise.all([
        getShopDesign(shopId, designId), getAllShopStyleOptions(shopId),
      ])
      const groupRows = await getShopFamilyOptionGroups(shopId, record.family)
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

  useEffect(() => { void loadPrice() }, [loadPrice])

  async function savePrice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!shopId || !designId || !shop?.default_currency || !designPrice.trim()) return
    setIsPriceSaving(true)
    setPriceError(null)
    try {
      const saved = await billingApi.setDesignPrice(shopId, designId, designPrice.trim())
      setSavedDesignPrice(saved.amount)
      setDesignPrice(saved.amount)
    } catch (cause) { setPriceError(errorMessage(cause)) }
    finally { setIsPriceSaving(false) }
  }

  const latest = design?.latest_version
  const isDraft = latest?.status === 'DRAFT'
  const draftHasChanges = hasUnpublishedChanges(isDraft ? latest ?? null : null, design?.latest_published_version ?? null)
  const displayVersion = isDraft && !draftHasChanges && design?.latest_published_version
    ? design.latest_published_version
    : latest
  const groupNames = useMemo(() => new Map(groups.map(group => [group.option_group.id, group.option_group.name])), [groups])
  const visibleSelections = useMemo(() => {
    const selections = latest?.selections ?? []
    return isDraft
      ? selections.filter(selection => groups.some(group => group.option_group.id === selection.option_group))
      : selections
  }, [latest?.selections, groups, isDraft])
  const hasUnmappedSelections = isDraft && visibleSelections.length !== (latest?.selections.length ?? 0)
  const unmappedSelections = isDraft ? (latest?.selections ?? []).filter(selection => !groups.some(group => group.option_group.id === selection.option_group)) : []
  const selectableGroups = useMemo(() => groups.map(config => ({
    id: config.option_group.id,
    name: config.option_group.name,
    code: config.option_group.code,
    sort_order: config.sort_order,
    selection_mode: config.selection_mode,
    is_required: config.is_required,
    options: styleOptions.filter(option => option.is_active && option.option_group === config.option_group.id),
  })), [styleOptions, groups])
  const editingSelection = latest?.selections.find(selection => selection.id === editingSelectionId) ?? null
  const flowGroups = editingSelection
    ? selectableGroups.filter(group => group.id === editingSelection.option_group)
    : selectableGroups
  const currentGroup = flowGroups[selectionStep]
  const savedSelectionIds = useMemo(() => new Set(latest?.selections.map(selection => selection.style_option) ?? []), [latest?.selections])
  const pendingSelectionCount = editingSelection
    ? (draftSelections[editingSelection.option_group] ?? []).length
    : Object.values(draftSelections).reduce((total, ids) => total + ids.length, 0)
  const previewRows = useMemo(() => {
    const rows: Array<{ key: string; groupName: string; name: string; code: string; image?: StyleImage }> = []
    for (const selection of visibleSelections) {
      if (editingSelection && selection.id === editingSelection.id) continue
      const option = styleOptions.find(item => item.id === selection.style_option)
      rows.push({
        key: selection.id,
        groupName: groupNames.get(selection.option_group) ?? selection.option_group,
        name: option?.name ?? selection.style_option_name,
        code: option?.code ?? selection.selected_code,
        image: option?.reference_images[0] ?? selection.style_option_images[0],
      })
    }
    for (const group of selectableGroups) {
      for (const optionId of draftSelections[group.id] ?? []) {
        const option = group.options.find(item => item.id === optionId)
        if (option) rows.push({ key: `draft-${group.id}-${option.id}`, groupName: group.name, name: option.name, code: option.code, image: option.reference_images[0] })
      }
    }
    return rows
  }, [visibleSelections, editingSelection, styleOptions, groupNames, selectableGroups, draftSelections])

  function openSelectionEditor(selection?: DesignSelection) {
    setEditingSelectionId(selection?.id ?? null)
    setDraftSelections(selection ? { [selection.option_group]: [selection.style_option] } : {})
    const targetIndex = selection ? selectableGroups.findIndex(group => group.id === selection.option_group) : 0
    setSelectionStep(Math.max(0, targetIndex))
    setError(null)
    setSelectionOpen(true)
  }

  function canAdvanceFrom(group: typeof selectableGroups[number]) {
    const hasSavedSelection = latest?.selections.some(selection => selection.option_group === group.id) ?? false
    const hasDraftSelection = (draftSelections[group.id]?.length ?? 0) > 0
    return !group.is_required || hasSavedSelection || hasDraftSelection
  }

  function advanceSelectionStep() {
    if (!currentGroup || !canAdvanceFrom(currentGroup)) return
    setSelectionStep(step => Math.min(step + 1, flowGroups.length))
  }

  const styleOptionInteractions = useSelectAndAdvance({
    selectionMode: editingSelection || currentGroup?.selection_mode === 'SINGLE' ? 'SINGLE' : 'MULTI',
    selectedItems: currentGroup ? draftSelections[currentGroup.id] ?? [] : [],
    onChange: selectedItems => {
      if (!currentGroup) return
      setDraftSelections(current => ({ ...current, [currentGroup.id]: selectedItems }))
    },
    onAdvance: () => setSelectionStep(step => Math.min(step + 1, flowGroups.length)),
    scopeKey: currentGroup?.id ?? `selection-step-${selectionStep}`,
  })

  function closeSelectionEditor() {
    if (isAddingSelection) return
    setSelectionOpen(false)
    setEditingSelectionId(null)
    setDraftSelections({})
    setSelectionStep(0)
  }

  async function handlePublish() {
    if (!shopId || !latest || !draftHasChanges) return
    setIsPublishing(true)
    setError(null)
    try {
      const result = await publishShopDesignVersion(shopId, latest.id)
      setDesign(current => current ? {
        ...current,
        latest_version: result.next_draft,
        latest_published_version: result.published,
      } : current)
    } catch (publishError) {
      setError(errorMessage(publishError))
    } finally {
      setIsPublishing(false)
    }
  }

  async function handleRemoveUnmappedSelections() {
    if (!shopId || !latest || !unmappedSelections.length || isRemovingUnmapped) return
    setIsRemovingUnmapped(true)
    setError(null)
    try {
      for (const selection of unmappedSelections) {
        await removeUnmappedShopDesignSelection(shopId, latest.id, selection.id)
      }
      setDesign(await getShopDesign(shopId, designId!))
    } catch (removeError) {
      setError(errorMessage(removeError))
    } finally {
      setIsRemovingUnmapped(false)
    }
  }

  async function handleSaveSelection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!shopId || !latest) return
    if (selectionStep < flowGroups.length) {
      advanceSelectionStep()
      return
    }
    const optionIds = editingSelection
      ? (draftSelections[editingSelection.option_group] ?? []).slice(0, 1)
      : flowGroups.flatMap(group => draftSelections[group.id] ?? [])
    if (!optionIds.length) {
      closeSelectionEditor()
      return
    }
    setIsAddingSelection(true)
    setError(null)
    try {
      if (editingSelection) {
        await updateShopDesignSelection(shopId, latest.id, editingSelection.id, { style_option_id: optionIds[0] })
      } else {
        for (const styleOptionId of optionIds) {
          await addShopDesignSelection(shopId, latest.id, { style_option_id: styleOptionId })
        }
      }
      const refreshed = await getShopDesign(shopId, designId!)
      setDesign(refreshed)
      setSelectionOpen(false)
      setEditingSelectionId(null)
      setDraftSelections({})
      setSelectionStep(0)
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
  const isReviewStep = selectionStep >= flowGroups.length

  return (
    <div className="content-wrap design-page">
      <div className="design-editor-heading">
        <Link to="/designs" className="icon-button" aria-label="Back to designs"><ArrowLeft size={20} /></Link>
        <div><h1>{design.name || 'Design'}</h1><p>Version {displayVersion?.number ?? latest.number} · {displayVersion?.status ?? latest.status}</p></div>
      </div>
      {error && <div className="design-error" role="alert">{error}<button onClick={() => { setIsLoading(true); setError(null); void loadDesign() }}>Retry</button></div>}

      <div className="design-editor-layout">
        <div className="design-editor-main">
          <section className="design-panel">
            <div className="design-panel-heading"><h2>Selections</h2>{isDraft && <button type="button" className="secondary-button design-add-selection-button" onClick={() => openSelectionEditor()}><Check size={15} /> Add selection</button>}</div>
            {visibleSelections.length === 0 ? <p className="design-muted">No style selections yet.</p> : <ul className="design-selection-list">{visibleSelections.map(selection => {
              const currentOptionImage = styleOptions.find(option => option.id === selection.style_option)?.reference_images[0]
              return <li key={selection.id}>
                <StyleOptionThumbnail image={currentOptionImage ?? selection.style_option_images[0]} alt={selection.style_option_name} />
                <span className="design-selection-group">{groupNames.get(selection.option_group) ?? selection.option_group}</span>
                <strong>{selection.style_option_name}</strong>
                {isDraft && <button type="button" className="secondary-button design-selection-edit" onClick={() => openSelectionEditor(selection)}><Pencil size={15} /><span>Edit</span></button>}
              </li>
            })}</ul>}
          </section>

          <section className="design-panel">
            <div className="design-panel-heading"><h2>Reference images</h2>{isDraft && <label className="secondary-button design-upload">{isUploading ? <Loader2 className="animate-spin" size={16} /> : <Upload size={16} />} Upload<input type="file" accept="image/jpeg,image/png,image/webp" multiple hidden disabled={isUploading} onChange={event => void handleUpload(event)} /></label>}</div>
            {allReferences.length === 0 ? <p className="design-muted">No reference images yet.</p> : <div className="design-reference-grid">{allReferences.map((reference: DesignReference) => <PrivateImage key={reference.id} url={reference.content_url} />)}</div>}
          </section>
        </div>
        <aside className="design-panel design-actions-panel">
          <h2>Actions</h2>
          {isDraft && draftHasChanges ? hasUnmappedSelections
            ? <div className="design-error" role="alert"><AlertCircle size={17} /><span>{`Publish is unavailable because ${unmappedSelections.length} saved choice${unmappedSelections.length === 1 ? '' : 's'} belong${unmappedSelections.length === 1 ? 's' : ''} to garment part${unmappedSelections.length === 1 ? '' : 's'} no longer configured for this family.`}</span><button type="button" className="secondary-button" disabled={isRemovingUnmapped} onClick={() => void handleRemoveUnmappedSelections()}>{isRemovingUnmapped ? 'Removing…' : 'Remove old choices from this draft'}</button></div>
            : isPublishing
              ? <p className="design-muted" role="status">Publishing version…</p>
              : canPublish
                ? <button type="button" className="primary-button design-publish-button" onClick={() => void handlePublish()}><Check size={16} /><span>Publish version</span></button>
              : <p className="design-muted">Publishing is available to authorized Shop staff only.</p>
            : isDraft
              ? <p className="design-muted">Published. Edit this draft to enable publishing again.</p>
              : <p className="design-muted">Published versions cannot be changed.</p>}
          {canManagePrice && <form className="design-price-form" onSubmit={event => void savePrice(event)}>
            <h3>Shop price</h3>
            {priceError && <p className="design-error" role="alert">{priceError}<button type="button" className="secondary-button" onClick={() => void loadPrice()}>Retry</button></p>}
            {!shop?.default_currency
              ? <p className="design-muted">Set the Shop default currency before adding a Design price.</p>
              : <><p className="design-muted">{savedDesignPrice === null ? 'No price saved for this Shop.' : `Current price: ${savedDesignPrice} ${shop.default_currency}`}</p><label htmlFor="shop-design-price">Price ({shop.default_currency})</label><input id="shop-design-price" inputMode="decimal" value={designPrice} onChange={event => setDesignPrice(event.target.value)} disabled={isPriceLoading || isPriceSaving} placeholder="0.00" /><button type="submit" className="primary-button" disabled={isPriceLoading || isPriceSaving || !designPrice.trim() || designPrice === savedDesignPrice}>{isPriceSaving ? <Loader2 size={16} className="animate-spin" /> : null}{savedDesignPrice === null ? 'Add price' : 'Save price'}</button></>}
          </form>}
        </aside>
      </div>

      {selectionOpen && <div className="design-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) closeSelectionEditor() }}>
        <form className="design-dialog design-guided-dialog" onSubmit={event => void handleSaveSelection(event)} aria-labelledby="design-selection-title" role="dialog" aria-modal="true">
          <div className="design-dialog-heading">
            <div><h2 id="design-selection-title">{editingSelection ? `Edit ${groupNames.get(editingSelection.option_group) ?? 'style'} selection` : 'Add style selection'}</h2>
              <p>{isReviewStep ? 'Review your choices before adding them to this Design.' : `Step ${selectionStep + 1} of ${flowGroups.length} · ${currentGroup?.name ?? ''}`}</p>
            </div>
            <button type="button" className="icon-button" onClick={closeSelectionEditor} aria-label="Close" disabled={isAddingSelection}><X size={18} /></button>
          </div>
          {flowGroups.length > 0 && <ol className="design-guided-progress" aria-label="Selection progress">
            {flowGroups.map((group, index) => <li key={group.id} className={index < selectionStep ? 'complete' : index === selectionStep && !isReviewStep ? 'current' : ''}>
              <button type="button" disabled={index >= selectionStep || isAddingSelection} onClick={() => setSelectionStep(index)} aria-current={index === selectionStep && !isReviewStep ? 'step' : undefined}>{group.name}</button>
            </li>)}
          </ol>}
          <div className="design-selection-workspace">
            <section className="design-guided-main" aria-live="polite">
              {isReviewStep ? <div className="design-selection-review">
                <h3>Review selections</h3>
                <p>Selections are saved when you finish this step.</p>
                {pendingSelectionCount ? flowGroups.map(group => {
                  const options = (draftSelections[group.id] ?? []).map(id => group.options.find(option => option.id === id)).filter((option): option is StyleOption => Boolean(option))
                  return options.length ? <div className="design-review-group" key={group.id}><h4>{group.name}</h4><ul>{options.map(option => <li key={option.id}><StyleOptionThumbnail image={option.reference_images[0]} alt={option.name} /><span><strong>{option.name}</strong><small>{option.code}</small></span></li>)}</ul></div> : null
                }) : <p className="design-muted">No new options selected. Finish to close this picker.</p>}
              </div> : currentGroup ? <div className="design-choice-groups" key={currentGroup.id} aria-label="Available style options">
                <fieldset className="design-choice-group">
                  <legend>{currentGroup.name}<span>{currentGroup.options.length}</span></legend>
                  <div className="design-current-group-hint"><span>{currentGroup.is_required ? 'Required group' : 'Optional group'}</span><small>{editingSelection || currentGroup.selection_mode === 'SINGLE' ? 'Choose one option' : 'Choose any number of options'}</small></div>
                  {!editingSelection && latest.selections.some(selection => selection.option_group === currentGroup.id) && <div className="design-saved-group-note">
                    <Check size={15} /><span>{currentGroup.selection_mode === 'SINGLE' ? 'This group already has a saved option. Use Edit in the Design to change it.' : 'Saved options are marked. Choose additional options if needed.'}</span>
                  </div>}
                  {currentGroup.options.length ? <div className="design-choice-options">
                    {currentGroup.options.map(option => {
                      const saved = !editingSelection && savedSelectionIds.has(option.id)
                      const duplicateSaved = Boolean(editingSelection && latest.selections.some(selection => selection.id !== editingSelection.id && selection.option_group === currentGroup.id && selection.style_option === option.id))
                      const lockedSingle = !editingSelection && currentGroup.selection_mode === 'SINGLE' && latest.selections.some(selection => selection.option_group === currentGroup.id)
                      const checked = saved || (draftSelections[currentGroup.id] ?? []).includes(option.id)
                      const disabled = saved || duplicateSaved || lockedSingle || isAddingSelection
                      const selectionMode = editingSelection || currentGroup.selection_mode === 'SINGLE' ? 'SINGLE' : 'MULTI'
                      const interaction = styleOptionInteractions.getItemProps(option.id, disabled)
                      return <label className={`design-choice-option${checked ? ' selected' : ''}${saved ? ' saved' : ''}`} key={option.id}
                        onPointerDown={interaction.onPointerDown}>
                        <input type={selectionMode === 'SINGLE' ? 'radio' : 'checkbox'} name={`style-option-${currentGroup.id}`} value={option.id} checked={checked} disabled={disabled}
                          onChange={interaction.onChange} onKeyDown={interaction.onKeyDown} />
                        <StyleOptionThumbnail image={option.reference_images[0]} alt={option.name} />
                        <span className="design-choice-option-copy"><strong>{option.name}</strong><small>{saved || duplicateSaved ? 'Already saved' : option.code}</small></span>
                      </label>
                    })}
                  </div> : <div className="design-choice-empty" role="status"><AlertCircle size={19} /><p>No active options are available for this group.</p></div>}
                </fieldset>
              </div> : <div className="design-choice-empty" role="status"><AlertCircle size={19} /><p>No option groups are linked to this garment family yet.</p></div>}
            </section>
            <aside className="design-selection-preview" aria-label="Selection preview">
              <div className="design-selection-preview-heading"><h3>Design preview</h3><span>{previewRows.length}</span></div>
              {previewRows.length ? <ul>{previewRows.map(row => <li key={row.key}>
                <StyleOptionThumbnail image={row.image} alt={row.name} />
                <span><small>{row.groupName}</small><strong>{row.name}</strong></span>
              </li>)}</ul> : <p className="design-muted">Your selected options will appear here.</p>}
            </aside>
          </div>
          <div className="design-dialog-actions design-guided-actions">
            <button type="button" className="secondary-button" onClick={closeSelectionEditor} disabled={isAddingSelection}>Cancel</button>
            {(selectionStep > 0 || isReviewStep) && <button type="button" className="secondary-button" onClick={() => setSelectionStep(step => Math.max(0, Math.min(step - 1, flowGroups.length)))} disabled={isAddingSelection}>Back</button>}
            {!isReviewStep
              ? <button className="primary-button" type="submit" disabled={isAddingSelection || !currentGroup || !canAdvanceFrom(currentGroup)}>{currentGroup && currentGroup.is_required && !canAdvanceFrom(currentGroup) ? 'Choose a required option' : currentGroup && !currentGroup.is_required && !(draftSelections[currentGroup.id]?.length) && !latest.selections.some(selection => selection.option_group === currentGroup.id) ? 'Skip group' : selectionStep === flowGroups.length - 1 ? 'Review selections' : 'Continue'}</button>
              : pendingSelectionCount > 0
                ? <button className="primary-button" type="submit" disabled={isAddingSelection}>{isAddingSelection ? <Loader2 className="animate-spin" size={16} /> : null}<span>{editingSelection ? 'Save selection' : `Add ${pendingSelectionCount} selection${pendingSelectionCount === 1 ? '' : 's'}`}</span></button>
                : <button className="primary-button" type="button" onClick={closeSelectionEditor} disabled={isAddingSelection}>Done</button>}
          </div>
        </form>
      </div>}
    </div>
  )
}
