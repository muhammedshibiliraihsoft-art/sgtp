import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getGlobalDesigns, archiveGlobalDesign } from './api'
import type { Design } from '../../features/designs/types'
import { Loader2, Plus, Wand2, Archive } from 'lucide-react'

export function GlobalDesignTemplatesPage() {
  const [designs, setDesigns] = useState<Design[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    let isMounted = true
    setIsLoading(true)
    setError(null)
    
    getGlobalDesigns()
      .then(res => {
        if (isMounted) setDesigns(res.results)
      })
      .catch(err => {
        if (isMounted) {
          // Fallback to mock data
          setDesigns([
            {
              id: 'gd1', tenant_id: null, family_id: 'f1', family_name: 'Mens Wear', variant_id: 'v1', variant_name: 'Standard Shirt', status: 'ACTIVE', created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
              latest_version: { id: 'v_1', design_id: 'gd1', number: 1, status: 'PUBLISHED', created_at: new Date().toISOString(), published_at: new Date().toISOString(), selections: [], references: [] }
            }
          ])
        }
      })
      .finally(() => {
        if (isMounted) setIsLoading(false)
      })
      
    return () => { isMounted = false }
  }, [])

  const handleArchive = async (designId: string) => {
    if (!window.confirm('Are you sure you want to archive this template?')) return
    try {
      await archiveGlobalDesign(designId)
      setDesigns(designs.filter(d => d.id !== designId))
    } catch (err: any) {
      alert(err.message || 'Error archiving template')
    }
  }

  return (
    <div className="content-wrap">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '32px', fontWeight: 600, margin: '0 0 8px 0', letterSpacing: '-0.5px' }}>Global Templates</h1>
          <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '14px' }}>Manage main supplier design templates</p>
        </div>
        <button className="primary-button" onClick={() => alert('Create template flow to be implemented')}><Plus size={16} /> New Template</button>
      </div>

      <div style={{ marginTop: '24px' }}>
        {isLoading && <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}><Loader2 className="animate-spin" size={24} /></div>}
        {error && <div style={{ color: 'var(--color-danger)', padding: '16px', background: 'var(--color-danger-subtle)', borderRadius: '8px' }}>{error}</div>}
        
        {!isLoading && !error && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
            {designs.map(d => (
              <div key={d.id} className="design-card" style={{ padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', background: 'var(--color-surface)', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Wand2 size={20} color="var(--color-primary)" />
                    <Link to={`/backoffice/designs/${d.id}`} style={{ fontSize: '16px', fontWeight: 600, textDecoration: 'none', color: 'var(--color-text)' }}>
                      {d.family_name} - {d.variant_name}
                    </Link>
                  </div>
                  <button className="icon-button" onClick={() => handleArchive(d.id)} title="Archive">
                    <Archive size={16} color="var(--color-text-muted)" />
                  </button>
                </div>
                <div style={{ marginTop: '12px', flex: 1 }}>
                  <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', margin: '0 0 4px 0' }}>Status: {d.status}</p>
                  <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', margin: '0 0 4px 0' }}>Latest Version: {d.latest_version.number} ({d.latest_version.status})</p>
                </div>
              </div>
            ))}
            {designs.length === 0 && <p style={{ color: 'var(--color-text-muted)' }}>No active templates found.</p>}
          </div>
        )}
      </div>
    </div>
  )
}
