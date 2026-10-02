import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getGlobalDesign, publishGlobalDesignVersion, uploadGlobalDesignReference } from './api'
import type { Design } from '../../features/designs/types'
import { usePrivateImage } from '../../hooks/usePrivateImage'
import { Loader2, ArrowLeft, Upload, Check, AlertCircle } from 'lucide-react'

function PrivateImage({ url }: { url: string }) {
  const { objectUrl, isLoading, error } = usePrivateImage(url)
  
  if (isLoading) return <div style={{ width: '100px', height: '100px', display: 'grid', placeItems: 'center', background: 'var(--color-surface-subtle)' }}><Loader2 className="animate-spin" /></div>
  if (error || !objectUrl) return <div style={{ width: '100px', height: '100px', display: 'grid', placeItems: 'center', background: 'var(--color-danger-subtle)', color: 'var(--color-danger)' }}><AlertCircle size={20} /></div>
  
  return <img src={objectUrl} alt="Reference" style={{ width: '100px', height: '100px', objectFit: 'cover', borderRadius: '8px' }} />
}

export function GlobalTemplateEditor() {
  const { designId } = useParams()
  
  const [design, setDesign] = useState<Design | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [isUploading, setIsUploading] = useState(false)
  const [isPublishing, setIsPublishing] = useState(false)
  
  useEffect(() => {
    if (!designId) return
    let isMounted = true
    setIsLoading(true)
    
    getGlobalDesign(designId)
      .then(res => { if (isMounted) setDesign(res) })
      .catch(err => {
        if (isMounted) {
          setDesign({
            id: designId, tenant_id: null, family_id: 'f1', family_name: 'Mens Wear', variant_id: 'v1', variant_name: 'Standard Shirt', status: 'ACTIVE', created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
            latest_version: { id: 'v_1', design_id: designId, number: 1, status: 'PUBLISHED', created_at: new Date().toISOString(), published_at: new Date().toISOString(), 
              selections: [
                { id: 'sel1', style_option_id: 's1', style_option_name: 'Standard Collar', group_id: 'g1', group_name: 'Collar Types' },
                { id: 'sel2', style_option_id: 's3', style_option_name: 'French Cuff', group_id: 'g2', group_name: 'Cuff Types' }
              ], 
              references: [] 
            }
          })
        }
      })
      .finally(() => { if (isMounted) setIsLoading(false) })
      
    return () => { isMounted = false }
  }, [designId])

  const handlePublish = async () => {
    if (!design) return
    const versionId = design.latest_version.id
    if (!window.confirm('Publish this template version? It will become immutable.')) return
    
    setIsPublishing(true)
    try {
      const res = await publishGlobalDesignVersion(design.id, versionId)
      setDesign({
        ...design,
        latest_version: res.next_draft
      })
      alert('Template published successfully!')
    } catch (err: any) {
      alert(err.message || 'Failed to publish template')
    } finally {
      setIsPublishing(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !design) return
    
    setIsUploading(true)
    try {
      const versionId = design.latest_version.id
      const newReferences = await uploadGlobalDesignReference(design.id, versionId, file)
      
      setDesign({
        ...design,
        latest_version: {
          ...design.latest_version,
          references: newReferences
        }
      })
    } catch (err: any) {
      alert(err.message || 'Failed to upload image')
    } finally {
      setIsUploading(false)
      if (e.target) e.target.value = ''
    }
  }

  if (isLoading) {
    return <div className="content-wrap" style={{ display: 'grid', placeItems: 'center', height: '300px' }}><Loader2 className="animate-spin" /></div>
  }

  if (error || !design) {
    return <div className="content-wrap"><div style={{ color: 'var(--color-danger)', padding: '16px', background: 'var(--color-danger-subtle)' }}>{error || 'Template not found'}</div></div>
  }

  const isDraft = design.latest_version.status === 'DRAFT'

  return (
    <div className="content-wrap">
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <Link to="/backoffice/designs" className="icon-button" style={{ textDecoration: 'none' }}><ArrowLeft size={20} /></Link>
        <div>
          <h1 style={{ fontSize: '24px', margin: 0 }}>{design.family_name} - {design.variant_name}</h1>
          <p style={{ margin: '4px 0 0 0', color: 'var(--color-text-muted)', fontSize: '13px' }}>Version {design.latest_version.number} ({design.latest_version.status})</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        <div className="editor-main" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          <section className="selections-section" style={{ padding: '24px', background: 'var(--color-surface)', borderRadius: '12px', border: '1px solid var(--color-border)' }}>
            <h2 style={{ fontSize: '18px', marginTop: 0, marginBottom: '16px' }}>Selections</h2>
            {design.latest_version.selections.length === 0 ? (
              <p style={{ color: 'var(--color-text-muted)', fontSize: '14px' }}>No selections made yet.</p>
            ) : (
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {design.latest_version.selections.map(sel => (
                  <li key={sel.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', border: '1px solid var(--color-border)', borderRadius: '8px' }}>
                    <span style={{ fontWeight: 600 }}>{sel.group_name}</span>
                    <span>{sel.style_option_name}</span>
                  </li>
                ))}
              </ul>
            )}
            
            {isDraft && (
              <div style={{ marginTop: '16px' }}>
                <button className="secondary-button" onClick={() => alert('Add selection flow to be implemented')}>Add Selection</button>
              </div>
            )}
          </section>

          <section className="references-section" style={{ padding: '24px', background: 'var(--color-surface)', borderRadius: '12px', border: '1px solid var(--color-border)' }}>
            <h2 style={{ fontSize: '18px', marginTop: 0, marginBottom: '16px' }}>Reference Images</h2>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              {design.latest_version.references.map(ref => (
                <PrivateImage key={ref.id} url={ref.content_url} />
              ))}
              
              {isDraft && (
                <label style={{ width: '100px', height: '100px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px', border: '2px dashed var(--color-border)', borderRadius: '8px', cursor: 'pointer', background: 'var(--color-surface-subtle)' }}>
                  {isUploading ? <Loader2 className="animate-spin" /> : <Upload size={20} color="var(--color-text-muted)" />}
                  <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Upload</span>
                  <input type="file" style={{ display: 'none' }} accept="image/jpeg, image/png, image/webp" onChange={handleFileUpload} disabled={isUploading} />
                </label>
              )}
            </div>
          </section>

        </div>
        
        <div className="editor-sidebar" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ padding: '24px', background: 'var(--color-surface)', borderRadius: '12px', border: '1px solid var(--color-border)' }}>
            <h3 style={{ fontSize: '16px', marginTop: 0, marginBottom: '12px' }}>Actions</h3>
            {isDraft ? (
              <button className="primary-button" style={{ width: '100%' }} onClick={handlePublish} disabled={isPublishing}>
                {isPublishing ? <Loader2 className="animate-spin" size={16} /> : <Check size={16} />}
                Publish Version
              </button>
            ) : (
              <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', margin: 0 }}>This version is published and cannot be edited.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
