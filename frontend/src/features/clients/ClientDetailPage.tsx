import { Suspense, lazy, useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ChevronLeft, Edit2, Trash2, Plus, Users, Ruler, MoreHorizontal } from 'lucide-react'
import type { Client, RelatedPerson } from './types'
import { ClientForm, type FormValues } from './ClientForm'
import { ConfirmDeleteModal } from './ConfirmDeleteModal'
import { clientsApi, type ContactWriteResult } from './api'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { useAuth } from '../../services/useAuth'
import { ClientMeasurementHistory } from './ClientMeasurementHistory'
import './clients.css'
import './client-workspace.css'

const EmbeddedClientMeasurements = lazy(() => import('../measurements/ClientMeasurementsPage').then(module => ({ default: module.ClientMeasurementsPage })))

export function ClientDetailPage() {
  const { clientId } = useParams<{ clientId: string }>()
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()
  const { user } = useAuth()
  const { shopId, role, workFunctions, isLoading: isShopLoading } = useCurrentShop()

  const [client, setClient] = useState<Client | undefined>()
  const [relatedPersons, setRelatedPersons] = useState<RelatedPerson[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [relatedLoading, setRelatedLoading] = useState(true)
  const [relatedError, setRelatedError] = useState('')
  const [duplicateMatches, setDuplicateMatches] = useState<{id:string;name:string}[]>([])
  const canWrite = role === 'ADMIN' || role === 'STAFF'
  const canDelete = role === 'ADMIN'
  const canReadMeasurements = Boolean(shopId && (user?.is_main_supplier_admin === true || role === 'ADMIN' || (role === 'STAFF' && workFunctions.includes('MEASUREMENT'))))
  const clientRequest = useRef(0)
  const relatedRequest = useRef(0)

  const loadData = useCallback(async () => {
    const requestId = ++clientRequest.current
    if (!shopId || !clientId) { setIsLoading(isShopLoading); return }
    setIsLoading(true); setError('')
    try {
      const loadedClient = await clientsApi.detail(shopId, clientId)
      if (requestId === clientRequest.current) setClient(loadedClient)
    }
    catch (cause) { if (requestId === clientRequest.current) setError(cause instanceof Error ? cause.message : 'Unable to load client.') }
    finally { if (requestId === clientRequest.current) setIsLoading(false) }
  }, [shopId, clientId, isShopLoading])

  useEffect(() => { void loadData() }, [loadData])

  const loadRelated = useCallback(async () => {
    const requestId = ++relatedRequest.current
    if (!shopId || !clientId) { setRelatedLoading(isShopLoading); return }
    setRelatedLoading(true); setRelatedError('')
    try {
      const related = await clientsApi.related(shopId, clientId)
      if (requestId === relatedRequest.current) setRelatedPersons(related.results)
    }
    catch (cause) { if (requestId === relatedRequest.current) setRelatedError(cause instanceof Error ? cause.message : 'Unable to load related persons.') }
    finally { if (requestId === relatedRequest.current) setRelatedLoading(false) }
  }, [shopId, clientId, isShopLoading])

  useEffect(() => { void loadRelated() }, [loadRelated])

  const [isEditClientOpen, setIsEditClientOpen] = useState(false)
  const [isDeleteClientOpen, setIsDeleteClientOpen] = useState(false)
  const [showMeasurementWorkspace, setShowMeasurementWorkspace] = useState(false)
  const [hasOpenedMeasurementWorkspace, setHasOpenedMeasurementWorkspace] = useState(false)
  
  const [isAddRelatedOpen, setIsAddRelatedOpen] = useState(false)
  const [editRelatedId, setEditRelatedId] = useState<string | null>(null)
  const [deleteRelatedId, setDeleteRelatedId] = useState<string | null>(null)

  if (isLoading) return <div className="client-detail-page"><div className="empty-state" aria-busy="true">Loading client…</div></div>
  if (!client) {
    return (
      <div className="client-detail-page">
        <div className="empty-state">
          <h3>{error || 'Client not found'}</h3>
          <button className="btn-primary" onClick={() => navigate('/clients')}>Back to Clients</button>
        </div>
      </div>
    )
  }

  const handleEditClient = async (values: FormValues) => {
    if (!shopId) return
    try {
      const updated = await clientsApi.update(shopId, client.id, values) as ContactWriteResult<Client>
      setClient(updated); setDuplicateMatches(updated.warnings?.flatMap(w => w.matches) ?? []); setIsEditClientOpen(false)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to update client.') }
  }

  const handleDeleteClient = async () => {
    if (!shopId) return
    try { await clientsApi.remove(shopId, client.id); navigate('/clients') }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to remove client.') }
  }

  const handleSaveRelated = async (values: FormValues) => {
    if (!shopId) return
    if (editRelatedId) {
      try {
        const updated = await clientsApi.updateRelated(shopId, client.id, editRelatedId, values) as ContactWriteResult<RelatedPerson>
        setRelatedPersons(prev => prev.map(rp => rp.id === updated.id ? updated : rp)); setDuplicateMatches(updated.warnings?.flatMap(w => w.matches) ?? []); setEditRelatedId(null)
      } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to update related person.') }
    } else {
      try {
        const created = await clientsApi.createRelated(shopId, client.id, values) as ContactWriteResult<RelatedPerson>
        setRelatedPersons(prev => [...prev, created]); setDuplicateMatches(created.warnings?.flatMap(w => w.matches) ?? []); setIsAddRelatedOpen(false)
      } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to add related person.') }
    }
  }

  const handleDeleteRelated = async () => {
    if (!shopId || !deleteRelatedId) return
    try { await clientsApi.removeRelated(shopId, client.id, deleteRelatedId); setRelatedPersons(prev => prev.filter(rp => rp.id !== deleteRelatedId)); setDeleteRelatedId(null) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to remove related person.') }
  }

  const editRelatedPerson = relatedPersons.find(rp => rp.id === editRelatedId)

  return (
    <div className="client-detail-page client-workspace-page">
      {error && <div className="login-error-message" role="alert">{error}</div>}
      {duplicateMatches.length > 0 && <div className="duplicate-warning" role="status"><strong>{t('clients.possibleDuplicate')}</strong>{duplicateMatches.map(match => <div key={match.id}>{match.name}</div>)}</div>}
      <Link to="/clients" className="back-link">
        <ChevronLeft size={16} /> {t('clients.title')}
      </Link>

      <div className="detail-header">
        <h1 style={{ fontSize: 28, fontWeight: 600, margin: 0 }}>{client.name}</h1>
      </div>

      <div className="client-workspace-topbar">
        <span className="client-workspace-muted">{t('clients.workspaceSubtitle')}</span>
        <div className="detail-actions">
          {canReadMeasurements && (showMeasurementWorkspace
            ? <button className="btn-secondary" onClick={() => setShowMeasurementWorkspace(false)}><ChevronLeft size={17} /> {t('clients.title')}</button>
            : <button className="btn-primary" onClick={() => { setHasOpenedMeasurementWorkspace(true); setShowMeasurementWorkspace(true) }}><Ruler size={17} /> {t('measurements.title')}</button>)}
          {canWrite && <button className="btn-secondary" onClick={() => setIsEditClientOpen(true)}>
            <Edit2 size={16} /> <span className="hide-mobile">{t('clients.edit')}</span>
          </button>}
          {canDelete && <details className="client-workspace-more-actions">
            <summary aria-label={t('clients.moreActions')}><MoreHorizontal size={19} /><span className="hide-mobile">{t('clients.moreActions')}</span></summary>
            <div className="client-workspace-more-menu"><button type="button" onClick={() => setIsDeleteClientOpen(true)}><Trash2 size={15} /> {t('clients.remove')}</button></div>
          </details>}
        </div>
      </div>

      <div className="client-workspace-summary">
      <div className="info-card">
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">{t('clients.phone')}</span>
            <span className="info-value">{client.phone || '—'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">{t('clients.email')}</span>
            <span className="info-value">{client.email || '—'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">{t('clients.created')}</span>
            <span className="info-value">{new Intl.DateTimeFormat(i18n.resolvedLanguage || 'en', { dateStyle: 'medium' }).format(new Date(client.created_at))}</span>
          </div>
          <div className="info-item">
            <span className="info-label">{t('clients.lastUpdated')}</span>
            <span className="info-value">{new Intl.DateTimeFormat(i18n.resolvedLanguage || 'en', { dateStyle: 'medium' }).format(new Date(client.updated_at))}</span>
          </div>
        </div>
      </div>
      </div>

      <div className={`client-workspace-layout${showMeasurementWorkspace ? ' is-measurement-view' : ''}`}>
      <div className="client-workspace-main">
        {canReadMeasurements ? <>
          {!showMeasurementWorkspace && <ClientMeasurementHistory shopId={shopId!} clientId={client.id} locale={i18n.resolvedLanguage || 'en'} />}
          {hasOpenedMeasurementWorkspace && <div className="client-workspace-embedded-measurements" hidden={!showMeasurementWorkspace}>
            <Suspense fallback={<section className="client-workspace-panel" aria-busy="true">{t('measurements.loading')}</section>}>
              <EmbeddedClientMeasurements embedded initialClient={client} initialRelatedPersons={relatedPersons} initialShopId={shopId!} />
            </Suspense>
          </div>}
        </> : (
          <section className="client-workspace-panel"><p className="client-workspace-eyebrow">{t('clients.measurementEyebrow')}</p><h2>{t('measurements.title')}</h2><p className="client-workspace-muted">{t('measurements.accessDenied')}</p></section>
        )}
      </div>

      {!showMeasurementWorkspace && <aside className="client-workspace-aside">
        <section className="client-workspace-panel client-related-panel" aria-labelledby="client-related-heading">
          <div className="client-workspace-panel-heading">
            <div>
              <p className="client-workspace-eyebrow">{t('clients.measurementEyebrow')}</p>
              <h2 id="client-related-heading"><Users size={19} aria-hidden="true" /> {t('clients.relatedPersons')}</h2>
            </div>
            <div className="client-related-header-actions">
              {!relatedLoading && <span className="client-workspace-count" aria-label={`${relatedPersons.length} ${t('clients.relatedPersons')}`}>{relatedPersons.length}</span>}
              {canWrite && !showMeasurementWorkspace && <button className="btn-primary client-related-add" onClick={() => setIsAddRelatedOpen(true)}>
                <Plus size={16} /> {t('clients.addRelatedPerson')}
              </button>}
            </div>
          </div>

          {relatedError && <div className="client-workspace-inline-error client-workspace-related-error" role="alert"><span>{relatedError}</span><button type="button" className="client-workspace-text-button" onClick={() => void loadRelated()}>{t('measurements.retry')}</button></div>}
          {relatedLoading ? <p className="client-workspace-muted" aria-busy="true">{t('clients.loadingRelated')}</p> : relatedPersons.length === 0 ? (
            <div className="client-related-empty"><Users size={22} aria-hidden="true" /><p>{t('clients.noRelated')}</p></div>
          ) : (
            <div className="clients-cards-list client-related-list">
              {relatedPersons.map(rp => (
                <div key={rp.id} className="client-card">
                  <div className="client-card-info">
                    <span className="client-card-name">{rp.name}</span>
                    {(rp.phone || rp.email) && (
                      <span className="client-card-detail">
                        {rp.phone} {rp.phone && rp.email ? '·' : ''} {rp.email}
                      </span>
                    )}
                  </div>
                  {canWrite && <div className="detail-actions">
                    <button className="action-btn-icon" onClick={() => setEditRelatedId(rp.id)} aria-label={t('clients.edit')}>
                      <Edit2 size={16} />
                    </button>
                    {canDelete && <button className="action-btn-icon" onClick={() => setDeleteRelatedId(rp.id)} aria-label={t('clients.remove')}>
                      <Trash2 size={16} />
                    </button>}
                  </div>}
                </div>
              ))}
            </div>
          )}
        </section>
      </aside>}
      </div>

      <ClientForm 
        isOpen={isEditClientOpen}
        onClose={() => setIsEditClientOpen(false)}
        onSave={handleEditClient}
        initialValues={client}
        duplicateMatches={duplicateMatches}
        title={t('clients.edit')}
      />

      <ClientForm 
        isOpen={isAddRelatedOpen || !!editRelatedId}
        onClose={() => { setIsAddRelatedOpen(false); setEditRelatedId(null); }}
        onSave={handleSaveRelated}
        initialValues={editRelatedPerson}
        duplicateMatches={duplicateMatches}
        title={editRelatedId ? t('clients.edit') : t('clients.addRelatedPerson')}
      />

      <ConfirmDeleteModal
        isOpen={isDeleteClientOpen}
        onClose={() => setIsDeleteClientOpen(false)}
        onConfirm={handleDeleteClient}
        title={t('clients.remove')}
        message={t('clients.confirmRemove')}
      />

      <ConfirmDeleteModal
        isOpen={!!deleteRelatedId}
        onClose={() => setDeleteRelatedId(null)}
        onConfirm={handleDeleteRelated}
        title={t('clients.remove')}
        message={t('clients.confirmRemoveRelated')}
      />

    </div>
  )
}
