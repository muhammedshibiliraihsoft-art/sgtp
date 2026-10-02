import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, Archive, Loader2, Wand2 } from 'lucide-react'
import { ApiError } from '../../services/apiClient'
import type { Design } from '../../features/designs/types'
import { archiveGlobalDesign, getAllGlobalDesigns } from './api'

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : 'Could not load global templates.'
}

export function GlobalDesignTemplatesPage() {
  const [designs, setDesigns] = useState<Design[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadDesigns = useCallback(async () => {
    try {
      setDesigns(await getAllGlobalDesigns())
      setError(null)
    } catch (loadError) {
      setError(errorMessage(loadError))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    queueMicrotask(() => { if (active) void loadDesigns() })
    return () => { active = false }
  }, [loadDesigns])

  async function handleArchive(designId: string) {
    if (!window.confirm('Archive this global template?')) return
    try {
      await archiveGlobalDesign(designId)
      setDesigns(current => current.filter(design => design.id !== designId))
    } catch (archiveError) {
      setError(errorMessage(archiveError))
    }
  }

  return (
    <div className="content-wrap">
      <div className="design-page-heading"><div><h1>Global Design Templates</h1><p>Published global templates are available to Shops.</p></div></div>
      <div className="design-info-note"><AlertCircle size={17} /> Creating a template needs a global-variant listing API. The backend currently exposes variant listing only inside an explicitly selected Shop, so this action is not offered here.</div>
      {error && <div className="design-error" role="alert">{error}<button onClick={() => { setIsLoading(true); setError(null); void loadDesigns() }} disabled={isLoading}>Retry</button></div>}
      {isLoading ? <div className="design-loading"><Loader2 className="animate-spin" /></div> : <div className="design-grid">
        {designs.map((design: Design) => <article key={design.id} className="design-card">
          <div className="design-card-heading"><Wand2 size={20} /><Link to={`/backoffice/designs/${design.id}`}>{design.name || design.id}</Link><button className="icon-button" onClick={() => void handleArchive(design.id)} title="Archive template" aria-label="Archive template"><Archive size={16} /></button></div>
          <p>Status: {design.status}</p><p>Version: {design.latest_version ? `${design.latest_version.number} (${design.latest_version.status})` : 'No version'}</p>
        </article>)}
        {designs.length === 0 && <p className="design-empty">No active global templates found.</p>}
      </div>}
    </div>
  )
}
