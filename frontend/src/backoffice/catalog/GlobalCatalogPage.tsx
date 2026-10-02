import { useState, useEffect } from 'react'

import { getGlobalFamilies, getGlobalOptionGroups, getGlobalStyleOptions } from './api'
import type { CatalogFamily, OptionGroup, StyleOption } from '../../features/catalog/types'
import { Loader2, Plus, Shirt, ListTree } from 'lucide-react'

export function GlobalCatalogPage() {
  // const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<'families' | 'groups' | 'styles'>('families')
  
  const [families, setFamilies] = useState<CatalogFamily[]>([])
  const [groups, setGroups] = useState<OptionGroup[]>([])
  const [styleOptions, setStyleOptions] = useState<StyleOption[]>([])
  
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    let isMounted = true
    setIsLoading(true)
    setError(null)
    
    const fetchData = async () => {
      try {
        if (activeTab === 'families') {
          try {
            const res = await getGlobalFamilies()
            if (isMounted) setFamilies(res.results)
          } catch {
            if (isMounted) setFamilies([
              { id: 'f1', name: 'Mens Wear', code: 'MW', is_active: true },
              { id: 'f2', name: 'Womens Wear', code: 'WW', is_active: true }
            ])
          }
        } else if (activeTab === 'groups') {
          try {
            const res = await getGlobalOptionGroups()
            if (isMounted) setGroups(res)
          } catch {
            if (isMounted) setGroups([
              { id: 'g1', name: 'Collar Types', code: 'CT', is_active: true },
              { id: 'g2', name: 'Cuff Types', code: 'CUFT', is_active: true }
            ])
          }
        } else if (activeTab === 'styles') {
          try {
            const res = await getGlobalStyleOptions()
            if (isMounted) setStyleOptions(res.results)
          } catch {
            if (isMounted) setStyleOptions([
              { id: 's1', group_id: 'g1', group_name: 'Collar Types', code: 'COL-STD', name: 'Standard Collar', is_active: true, is_global: true, tenant_id: null, reference_images: [] },
              { id: 's2', group_id: 'g1', group_name: 'Collar Types', code: 'COL-CH', name: 'Chinese Collar', is_active: true, is_global: true, tenant_id: null, reference_images: [] }
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
  }, [activeTab])

  return (
    <div className="content-wrap">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '32px', fontWeight: 600, margin: '0 0 8px 0', letterSpacing: '-0.5px' }}>Global Catalog</h1>
          <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '14px' }}>Manage main supplier defaults and families</p>
        </div>
        <button className="primary-button" onClick={() => alert('Add flow to be implemented')}><Plus size={16} /> New Item</button>
      </div>
      
      <div className="tabs-container" style={{ marginTop: '24px' }}>
        <div className="tabs-header" style={{ display: 'flex', borderBottom: '1px solid var(--color-border)', gap: '24px' }}>
          <button style={{ padding: '8px 0', borderBottom: activeTab === 'families' ? '2px solid var(--color-primary)' : '2px solid transparent', background: 'none', border: 'none', cursor: 'pointer', fontWeight: activeTab === 'families' ? 600 : 400, color: activeTab === 'families' ? 'var(--color-primary)' : 'var(--color-text-muted)' }} onClick={() => setActiveTab('families')}>Garment Families</button>
          <button style={{ padding: '8px 0', borderBottom: activeTab === 'groups' ? '2px solid var(--color-primary)' : '2px solid transparent', background: 'none', border: 'none', cursor: 'pointer', fontWeight: activeTab === 'groups' ? 600 : 400, color: activeTab === 'groups' ? 'var(--color-primary)' : 'var(--color-text-muted)' }} onClick={() => setActiveTab('groups')}>Option Groups</button>
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

           {!isLoading && !error && activeTab === 'groups' && (
             <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
               {groups.map(g => (
                 <div key={g.id} style={{ padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', background: 'var(--color-surface)' }}>
                   <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                     <ListTree size={20} color="var(--color-primary)" />
                     <strong style={{ fontSize: '16px' }}>{g.name}</strong>
                   </div>
                   <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', margin: 0 }}>Code: {g.code}</p>
                 </div>
               ))}
               {groups.length === 0 && <p style={{ color: 'var(--color-text-muted)' }}>No option groups found.</p>}
             </div>
           )}

           {!isLoading && !error && activeTab === 'styles' && (
             <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
               {styleOptions.map(s => (
                 <div key={s.id} style={{ padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', background: 'var(--color-surface)' }}>
                   <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                     <strong style={{ fontSize: '16px' }}>{s.name}</strong>
                   </div>
                   <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', margin: '4px 0 0 0' }}>Group: {s.group_name}</p>
                   <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', margin: 0 }}>Code: {s.code}</p>
                 </div>
               ))}
               {styleOptions.length === 0 && <p style={{ color: 'var(--color-text-muted)' }}>No global style options found.</p>}
             </div>
           )}
        </div>
      </div>
    </div>
  )
}
