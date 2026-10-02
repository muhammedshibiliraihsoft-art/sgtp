import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { AlertCircle, Loader2, Plus, Shirt, ListTree, X } from 'lucide-react'
import { ApiError } from '../../services/apiClient'
import { getAllFamilies, getAllGlobalStyleOptions, getOptionGroups } from '../../features/catalog/api'
import type { CatalogFamily, OptionGroup, ShopStyleOptionInputRequest, StyleOption } from '../../features/catalog/types'
import { createGlobalStyleOption } from './api'

type Tab = 'families' | 'groups' | 'styles'

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : 'Could not load the global catalog.'
}

export function GlobalCatalogPage() {
  const [activeTab, setActiveTab] = useState<Tab>('families')
  const [families, setFamilies] = useState<CatalogFamily[]>([])
  const [groups, setGroups] = useState<OptionGroup[]>([])
  const [styleOptions, setStyleOptions] = useState<StyleOption[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [groupId, setGroupId] = useState('')

  const loadCatalog = useCallback(async () => {
    try {
      const [familyRows, groupRows, styleRows] = await Promise.all([
        getAllFamilies(), getOptionGroups(), getAllGlobalStyleOptions(),
      ])
      setError(null)
      setFamilies(familyRows)
      setGroups(groupRows)
      setStyleOptions(styleRows)
    } catch (loadError) {
      setError(errorMessage(loadError))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    queueMicrotask(() => { if (active) void loadCatalog() })
    return () => { active = false }
  }, [loadCatalog])

  async function submitStyle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!groupId) return
    setIsSaving(true)
    setError(null)
    const data: ShopStyleOptionInputRequest = {
      option_group_id: groupId,
      code: code.trim(),
      translations: [{ locale: 'en', name: name.trim() }],
    }
    try {
      await createGlobalStyleOption(data)
      setCreateOpen(false)
      setName('')
      setCode('')
      await loadCatalog()
    } catch (saveError) {
      setError(errorMessage(saveError))
    } finally {
      setIsSaving(false)
    }
  }

  const groupNames = new Map(groups.map(group => [group.id, group.name]))

  return (
    <div className="content-wrap">
      <div className="catalog-heading"><div><h1>Global Catalog</h1><p>Manage the shared garment families, option groups and style defaults.</p></div>{activeTab === 'styles' && <button className="primary-button" onClick={() => { setGroupId(groups[0]?.id ?? ''); setCreateOpen(true) }}><Plus size={16} /> New Style Option</button>}</div>
      <div className="catalog-info-note"><AlertCircle size={17} /> Garment families and option groups are read-only here because the backend currently exposes listing and family-group configuration, not create endpoints.</div>
      {error && <div className="catalog-error" role="alert">{error}<button onClick={() => { setIsLoading(true); setError(null); void loadCatalog() }} disabled={isLoading}>Retry</button></div>}
      <div className="catalog-tabs" role="tablist" aria-label="Global catalog sections">
        {(['families', 'groups', 'styles'] as const).map(tab => <button key={tab} role="tab" aria-selected={activeTab === tab} className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>{tab === 'families' ? 'Garment Families' : tab === 'groups' ? 'Option Groups' : 'Style Options'}</button>)}
      </div>
      {isLoading ? <div className="catalog-loading"><Loader2 className="animate-spin" /></div> : <div className="catalog-grid">
        {activeTab === 'families' && families.map(family => <article className="catalog-card" key={family.id}><Shirt size={20} /><div><strong>{family.name}</strong><small>{family.code}</small></div></article>)}
        {activeTab === 'groups' && groups.map(group => <article className="catalog-card" key={group.id}><ListTree size={20} /><div><strong>{group.name}</strong><small>{group.code}</small></div></article>)}
        {activeTab === 'styles' && styleOptions.map(option => <article className="catalog-card" key={option.id}><Shirt size={20} /><div><strong>{option.name}</strong><small>{groupNames.get(option.option_group) ?? option.option_group} · {option.code}</small></div><span className="catalog-tag">Active</span></article>)}
        {activeTab === 'families' && families.length === 0 && <p className="catalog-empty">No garment families found.</p>}
        {activeTab === 'groups' && groups.length === 0 && <p className="catalog-empty">No option groups found.</p>}
        {activeTab === 'styles' && styleOptions.length === 0 && <p className="catalog-empty">No global style options found.</p>}
      </div>}
      {createOpen && <div className="catalog-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setCreateOpen(false) }}>
        <form className="catalog-dialog" onSubmit={event => void submitStyle(event)} aria-labelledby="global-style-create-title">
          <div className="catalog-dialog-heading"><h2 id="global-style-create-title">Create global style option</h2><button type="button" className="catalog-icon-button" onClick={() => setCreateOpen(false)} aria-label="Close"><X size={18} /></button></div>
          <label>Name (English)<input required maxLength={120} value={name} onChange={event => setName(event.target.value)} /></label>
          <label>Code<input required maxLength={64} pattern="[a-zA-Z0-9_-]+" value={code} onChange={event => setCode(event.target.value)} /></label>
          <label>Option group<select required value={groupId} onChange={event => setGroupId(event.target.value)}>{groups.map(group => <option key={group.id} value={group.id}>{group.name}</option>)}</select></label>
          <div className="catalog-dialog-actions"><button type="button" className="secondary-button" onClick={() => setCreateOpen(false)}>Cancel</button><button className="primary-button" type="submit" disabled={isSaving || groups.length === 0}>{isSaving ? <Loader2 size={16} className="animate-spin" /> : null} Create</button></div>
        </form>
      </div>}
    </div>
  )
}
