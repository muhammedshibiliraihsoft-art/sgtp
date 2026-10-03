import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ChevronLeft, Edit2, Trash2, Plus, Users, Ruler } from 'lucide-react'
import type { Client, RelatedPerson } from './types'
import { ClientForm, type FormValues } from './ClientForm'
import { ConfirmDeleteModal } from './ConfirmDeleteModal'
import { clientsApi, type ContactWriteResult } from './api'
import { useCurrentShop } from '../../hooks/useCurrentShop'

export function ClientDetailPage() {
  const { clientId } = useParams<{ clientId: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { shopId, role, isLoading: isShopLoading } = useCurrentShop()

  const [client, setClient] = useState<Client | undefined>()
  const [relatedPersons, setRelatedPersons] = useState<RelatedPerson[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [duplicateMatches, setDuplicateMatches] = useState<{id:string;name:string}[]>([])
  const canWrite = role === 'ADMIN' || role === 'STAFF'
  const canDelete = role === 'ADMIN'

  const loadData = useCallback(async () => {
    if (!shopId || !clientId) { setIsLoading(isShopLoading); return }
    setIsLoading(true); setError('')
    try {
      const [loadedClient, related] = await Promise.all([clientsApi.detail(shopId, clientId), clientsApi.related(shopId, clientId)])
      setClient(loadedClient); setRelatedPersons(related.results)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to load client.') }
    finally { setIsLoading(false) }
  }, [shopId, clientId, isShopLoading])

  useEffect(() => { void loadData() }, [loadData])

  const [isEditClientOpen, setIsEditClientOpen] = useState(false)
  const [isDeleteClientOpen, setIsDeleteClientOpen] = useState(false)
  
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
    <div className="client-detail-page">
      {error && <div className="login-error-message" role="alert">{error}</div>}
      {duplicateMatches.length > 0 && <div className="duplicate-warning" role="status"><strong>{t('clients.possibleDuplicate')}</strong>{duplicateMatches.map(match => <div key={match.id}>{match.name}</div>)}</div>}
      <Link to="/clients" className="back-link">
        <ChevronLeft size={16} /> {t('clients.title')}
      </Link>

      <div className="detail-header">
        <h1 style={{ fontSize: 28, fontWeight: 600, margin: 0 }}>{client.name}</h1>
        <div className="detail-actions">
          <Link to={`/clients/${client.id}/measurements`} className="btn-secondary"><Ruler size={16} /> Measurements</Link>
          {canWrite && <button className="btn-secondary" onClick={() => setIsEditClientOpen(true)}>
            <Edit2 size={16} /> <span className="hide-mobile">{t('clients.edit')}</span>
          </button>}
          {canDelete && <button className="btn-secondary" style={{ color: 'var(--color-danger)' }} onClick={() => setIsDeleteClientOpen(true)}>
            <Trash2 size={16} /> <span className="hide-mobile">{t('clients.remove')}</span>
          </button>}
        </div>
      </div>

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
            <span className="info-value">{new Date(client.created_at).toLocaleDateString()}</span>
          </div>
          <div className="info-item">
            <span className="info-label">{t('clients.lastUpdated')}</span>
            <span className="info-value">{new Date(client.updated_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      <div className="clients-header" style={{ marginTop: 40, marginBottom: 16 }}>
        <h2 style={{ fontSize: 20, margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Users size={20} /> {t('clients.relatedPersons')}
        </h2>
        {canWrite && <button className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }} onClick={() => setIsAddRelatedOpen(true)}>
          <Plus size={16} /> {t('clients.addRelatedPerson')}
        </button>}
      </div>

      {relatedPersons.length === 0 ? (
        <div className="empty-state" style={{ padding: '32px 16px' }}>
          <p>{t('clients.noRelated')}</p>
        </div>
      ) : (
        <div className="clients-cards-list">
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

      <style>{`
        .hide-mobile { display: none; }
        @media (min-width: 600px) {
          .hide-mobile { display: inline; }
        }
      `}</style>
    </div>
  )
}
