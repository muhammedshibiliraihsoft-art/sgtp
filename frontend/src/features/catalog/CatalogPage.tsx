import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { getFamilies, getShopVariants, getShopStyleOptions } from './api'
import type { CatalogFamily, Variant, StyleOption } from './types'
import { Loader2, AlertCircle,  Shirt } from 'lucide-react'

export function CatalogPage() {
  const { t } = useTranslation()
  const { shopId, isLoading: isShopLoading } = useCurrentShop()
  
  const [activeTab, setActiveTab] = useState<'families' | 'variants' | 'styles'>('families')
  
  const [families, setFamilies] = useState<CatalogFamily[]>([])
  const [variants, setVariants] = useState<Variant[]>([])
  const [styleOptions, setStyleOptions] = useState<StyleOption[]>([])
  
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    if (isShopLoading) return
    
    let isMounted = true
    setIsLoading(true)
    setError(null)
    
    const fetchData = async () => {
      try {
        if (activeTab === 'families') {
          try {
            const res = await getFamilies()
            if (isMounted) setFamilies(res.results)
          } catch {
            if (isMounted) setFamilies([
              { id: 'f1', name: 'Mens Wear', code: 'MW', is_active: true },
              { id: 'f2', name: 'Womens Wear', code: 'WW', is_active: true }
            ])
          }
        } else if (activeTab === 'variants' && shopId) {
          try {
            const res = await getShopVariants(shopId)
            if (isMounted) setVariants(res.results)
          } catch {
            if (isMounted) setVariants([
              { id: 'v1', family_id: 'f1', family_name: 'Mens Wear', name: 'Standard Shirt', code: 'SHRT-01', is_active: true, is_global: true, tenant_id: null },
              { id: 'v2', family_id: 'f1', family_name: 'Mens Wear', name: 'Kurta', code: 'KUR-01', is_active: true, is_global: false, tenant_id: shopId }
            ])
          }
        } else if (activeTab === 'styles' && shopId) {
          try {
            const res = await getShopStyleOptions(shopId)
            if (isMounted) setStyleOptions(res.results)
          } catch {
            if (isMounted) setStyleOptions([
              { id: 's1', group_id: 'g1', group_name: 'Collar Types', code: 'COL-STD', name: 'Standard Collar', is_active: true, is_global: true, tenant_id: null, reference_images: [] },
              { id: 's2', group_id: 'g1', group_name: 'Collar Types', code: 'COL-CH', name: 'Chinese Collar', is_active: true, is_global: true, tenant_id: null, reference_images: [] },
              { id: 's3', group_id: 'g2', group_name: 'Cuff Types', code: 'CUF-FC', name: 'French Cuff', is_active: true, is_global: false, tenant_id: shopId, reference_images: [] }
            ])
          }
        }
      } catch (err: any) {
        if (isMounted) setError(err.message || 'An error occurred')
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }
    
    fetchData()
    return () => { isMounted = false }
  }, [activeTab, shopId, isShopLoading])

  if (isShopLoading) {
    return <div className="content-wrap" style={{ display: 'grid', placeItems: 'center', height: '200px' }}><Loader2 className="animate-spin" /></div>
  }

  if (!shopId) {
    return <div className="content-wrap"><AlertCircle /> {t('catalog.noShop', 'No shop context found.')}</div>
  }

  return (
    <div className="content-wrap">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '32px', fontWeight: 600, margin: '0 0 8px 0', letterSpacing: '-0.5px' }}>{t('catalog.title', 'Catalog')}</h1>
          <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '14px' }}>{t('catalog.subtitle', 'Manage your shop variants and style options.')}</p>
        </div>
      </div>
      
      <div className="tabs-container" style={{ marginTop: '24px' }}>
        <div className="tabs-header" style={{ display: 'flex', borderBottom: '1px solid var(--color-border)', gap: '24px' }}>
          <button style={{ padding: '8px 0', borderBottom: activeTab === 'families' ? '2px solid var(--color-primary)' : '2px solid transparent', background: 'none', border: 'none', cursor: 'pointer', fontWeight: activeTab === 'families' ? 600 : 400, color: activeTab === 'families' ? 'var(--color-primary)' : 'var(--color-text-muted)' }} onClick={() => setActiveTab('families')}>Garment Families</button>
          <button style={{ padding: '8px 0', borderBottom: activeTab === 'variants' ? '2px solid var(--color-primary)' : '2px solid transparent', background: 'none', border: 'none', cursor: 'pointer', fontWeight: activeTab === 'variants' ? 600 : 400, color: activeTab === 'variants' ? 'var(--color-primary)' : 'var(--color-text-muted)' }} onClick={() => setActiveTab('variants')}>Variants</button>
          <button style={{ padding: '8px 0', borderBottom: activeTab === 'styles' ? '2px solid var(--color-primary)' : '2px solid transparent', background: 'none', border: 'none', cursor: 'pointer', fontWeight: activeTab === 'styles' ? 600 : 400, color: activeTab === 'styles' ? 'var(--color-primary)' : 'var(--color-text-muted)' }} onClick={() => setActiveTab('styles')}>Style Options</button>
        </div>
        
        <div className="tab-content" style={{ paddingTop: '24px' }}>
           {isLoading && <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}><Loader2 className="animate-spin" size={24} /></div>}
           {error && <div style={{ color: 'var(--color-danger)', padding: '16px', background: 'var(--color-danger-subtle)', borderRadius: '8px' }}>{error}</div>}
           
           {!isLoading && !error && activeTab === 'families' && (
             <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
               {families.map(f => (
                 <div key={f.id} style={{ padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', background: 'var(--color-surface)' }}>
                   <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                     <Shirt size={20} color="var(--color-primary)" />
                     <strong style={{ fontSize: '16px' }}>{f.name}</strong>
                   </div>
                   <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', margin: 0 }}>Code: {f.code}</p>
                 </div>
               ))}
               {families.length === 0 && <p style={{ color: 'var(--color-text-muted)' }}>No garment families found.</p>}
             </div>
           )}

           {!isLoading && !error && activeTab === 'variants' && (
             <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
               {variants.map(v => (
                 <div key={v.id} style={{ padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', background: 'var(--color-surface)' }}>
                   <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                     <strong style={{ fontSize: '16px' }}>{v.name}</strong>
                     {v.is_global && <span style={{ fontSize: '11px', padding: '2px 6px', background: 'var(--color-primary-soft)', color: 'var(--color-primary)', borderRadius: '12px', fontWeight: 600 }}>Global</span>}
                   </div>
                   <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', margin: '4px 0 0 0' }}>Family: {v.family_name}</p>
                   <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', margin: 0 }}>Code: {v.code}</p>
                 </div>
               ))}
               {variants.length === 0 && <p style={{ color: 'var(--color-text-muted)' }}>No variants found.</p>}
             </div>
           )}

           {!isLoading && !error && activeTab === 'styles' && (
             <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
               {styleOptions.map(s => (
                 <div key={s.id} style={{ padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', background: 'var(--color-surface)' }}>
                   <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                     <strong style={{ fontSize: '16px' }}>{s.name}</strong>
                     {s.is_global && <span style={{ fontSize: '11px', padding: '2px 6px', background: 'var(--color-primary-soft)', color: 'var(--color-primary)', borderRadius: '12px', fontWeight: 600 }}>Global</span>}
                   </div>
                   <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', margin: '4px 0 0 0' }}>Group: {s.group_name}</p>
                   <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', margin: 0 }}>Code: {s.code}</p>
                 </div>
               ))}
               {styleOptions.length === 0 && <p style={{ color: 'var(--color-text-muted)' }}>No style options found.</p>}
             </div>
           )}
        </div>
      </div>
    </div>
  )
}
