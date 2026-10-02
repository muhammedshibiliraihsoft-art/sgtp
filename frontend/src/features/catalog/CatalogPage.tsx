import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { ApiError } from '../../services/apiClient'
import { createShopStyleOption, createShopVariant, getAllFamilies, getAllShopStyleOptions, getAllShopVariants, getOptionGroups } from './api'
import type { CatalogFamily, OptionGroup, StyleOption, Variant } from './types'
import { AlertCircle, Loader2, Plus, Shirt, X } from 'lucide-react'
import './Catalog.css'

type Tab = 'families' | 'variants' | 'styles'
type CreateKind = 'variant' | 'style' | null

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : 'Could not load the catalog. Please try again.'
}

export function CatalogPage() {
  const { t } = useTranslation()
  const { shopId, isLoading: isShopLoading } = useCurrentShop()
  const [activeTab, setActiveTab] = useState<Tab>('families')
  const [families, setFamilies] = useState<CatalogFamily[]>([])
  const [groups, setGroups] = useState<OptionGroup[]>([])
  const [variants, setVariants] = useState<Variant[]>([])
  const [styleOptions, setStyleOptions] = useState<StyleOption[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createKind, setCreateKind] = useState<CreateKind>(null)
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [selectedFamily, setSelectedFamily] = useState('')
  const [selectedGroup, setSelectedGroup] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  const loadCatalog = useCallback(async () => {
    if (!shopId) return
    try {
      const [familyRows, groupRows] = await Promise.all([getAllFamilies(), getOptionGroups()])
      setError(null)
      setFamilies(familyRows)
      setGroups(groupRows)
      if (activeTab === 'variants') {
        setVariants(await getAllShopVariants(shopId))
      } else if (activeTab === 'styles') {
        setStyleOptions(await getAllShopStyleOptions(shopId))
      }
    } catch (loadError) {
      setError(errorMessage(loadError))
    } finally {
      setIsLoading(false)
    }
  }, [activeTab, shopId])

  useEffect(() => {
    let active = true
    if (!isShopLoading && shopId) queueMicrotask(() => { if (active) { setIsLoading(true); void loadCatalog() } })
    return () => { active = false }
  }, [activeTab, shopId, isShopLoading, loadCatalog])

  function openCreate(kind: Exclude<CreateKind, null>) {
    setCreateKind(kind)
    setName('')
    setCode('')
    setSelectedFamily(families[0]?.id ?? '')
    setSelectedGroup(groups[0]?.id ?? '')
  }

  async function submitCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!shopId || !createKind) return
    setIsSaving(true)
    setError(null)
    setIsLoading(true)
    try {
      const translations = [{ locale: 'en' as const, name: name.trim() }]
      if (createKind === 'variant') {
        await createShopVariant(shopId, { family_id: selectedFamily, code: code.trim(), translations })
      } else {
        await createShopStyleOption(shopId, { option_group_id: selectedGroup, code: code.trim(), translations })
      }
      setCreateKind(null)
      await loadCatalog()
    } catch (saveError) {
      setError(errorMessage(saveError))
    } finally {
      setIsSaving(false)
    }
  }

  if (isShopLoading) return <div className="content-wrap catalog-loading"><Loader2 className="animate-spin" /></div>
  if (!shopId) return <div className="content-wrap catalog-message"><AlertCircle /> {t('catalog.noShop', 'No shop context found.')}</div>

  const groupNames = new Map(groups.map(group => [group.id, group.name]))
  const familyNames = new Map(families.map(family => [family.id, family.name]))

  return (
    <div className="content-wrap">
      <div className="catalog-heading">
        <div>
          <h1>{t('catalog.title', 'Catalog')}</h1>
          <p>{t('catalog.subtitle', 'Manage your shop variants and style options.')}</p>
        </div>
        {activeTab !== 'families' && <button className="primary-button" onClick={() => openCreate(activeTab === 'variants' ? 'variant' : 'style')}><Plus size={16} /> New {activeTab === 'variants' ? 'Variant' : 'Style option'}</button>}
      </div>

      {error && <div className="catalog-error" role="alert">{error}<button onClick={() => { setIsLoading(true); setError(null); void loadCatalog() }} disabled={isLoading}>Retry</button></div>}

      <div className="catalog-tabs" role="tablist" aria-label="Catalog sections">
        {(['families', 'variants', 'styles'] as const).map(tab => <button key={tab} role="tab" aria-selected={activeTab === tab} className={activeTab === tab ? 'active' : ''} onClick={() => { setIsLoading(true); setActiveTab(tab) }}>{tab === 'families' ? 'Garment Families' : tab === 'variants' ? 'Variants' : 'Style Options'}</button>)}
      </div>

      {isLoading ? <div className="catalog-loading"><Loader2 className="animate-spin" /></div> : (
        <div className="catalog-grid">
          {activeTab === 'families' && families.map(family => <article className="catalog-card" key={family.id}><Shirt size={20} /><div><strong>{family.name}</strong><small>{family.code}</small></div></article>)}
          {activeTab === 'variants' && variants.map(variant => <article className="catalog-card" key={variant.id}><Shirt size={20} /><div><strong>{variant.name}</strong><small>{familyNames.get(variant.family) ?? variant.family} · {variant.code}</small></div>{variant.is_default && <span className="catalog-tag">Default</span>}</article>)}
          {activeTab === 'styles' && styleOptions.map(option => <article className="catalog-card" key={option.id}><Shirt size={20} /><div><strong>{option.name}</strong><small>{groupNames.get(option.option_group) ?? option.option_group} · {option.code}</small></div><span className="catalog-tag">{option.is_global ? 'Global' : 'Shop'}</span></article>)}
          {!families.length && activeTab === 'families' && <p className="catalog-empty">No garment families found.</p>}
          {!variants.length && activeTab === 'variants' && !isLoading && <p className="catalog-empty">No variants found.</p>}
          {!styleOptions.length && activeTab === 'styles' && !isLoading && <p className="catalog-empty">No style options found.</p>}
        </div>
      )}

      {createKind && <div className="catalog-dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setCreateKind(null) }}>
        <form className="catalog-dialog" onSubmit={event => void submitCreate(event)} aria-labelledby="catalog-create-title">
          <div className="catalog-dialog-heading"><h2 id="catalog-create-title">New {createKind === 'variant' ? 'variant' : 'style option'}</h2><button type="button" className="catalog-icon-button" onClick={() => setCreateKind(null)} aria-label="Close"><X size={18} /></button></div>
          <label>Name (English)<input required maxLength={120} value={name} onChange={event => setName(event.target.value)} /></label>
          <label>Code<input required maxLength={64} pattern="[a-zA-Z0-9_-]+" value={code} onChange={event => setCode(event.target.value)} /><small>Use letters, numbers, hyphens, or underscores.</small></label>
          {createKind === 'variant' ? <label>Garment family<select required value={selectedFamily} onChange={event => setSelectedFamily(event.target.value)}>{families.map(family => <option value={family.id} key={family.id}>{family.name}</option>)}</select></label> : <label>Option group<select required value={selectedGroup} onChange={event => setSelectedGroup(event.target.value)}>{groups.map(group => <option value={group.id} key={group.id}>{group.name}</option>)}</select></label>}
          <div className="catalog-dialog-actions"><button type="button" className="secondary-button" onClick={() => setCreateKind(null)}>Cancel</button><button type="submit" className="primary-button" disabled={isSaving || !(createKind === 'variant' ? families.length : groups.length)}>{isSaving ? <Loader2 size={16} className="animate-spin" /> : null} Create</button></div>
        </form>
      </div>}
    </div>
  )
}
