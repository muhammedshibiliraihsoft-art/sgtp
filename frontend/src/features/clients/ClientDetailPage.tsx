import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ChevronLeft, Edit2, Trash2, Plus, Users } from 'lucide-react'
import { mockClients, mockRelatedPersons } from './mockClients'
import type { Client, RelatedPerson } from './types'
import { ClientForm, type FormValues } from './ClientForm'
import { ConfirmDeleteModal } from './ConfirmDeleteModal'

export function ClientDetailPage() {
  const { clientId } = useParams<{ clientId: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const [client, setClient] = useState<Client | undefined>(mockClients.find(c => c.id === clientId))
  const [relatedPersons, setRelatedPersons] = useState<RelatedPerson[]>(
    mockRelatedPersons.filter(rp => rp.primary_client_id === clientId)
  )

  const [isEditClientOpen, setIsEditClientOpen] = useState(false)
  const [isDeleteClientOpen, setIsDeleteClientOpen] = useState(false)
  
  const [isAddRelatedOpen, setIsAddRelatedOpen] = useState(false)
  const [editRelatedId, setEditRelatedId] = useState<string | null>(null)
  const [deleteRelatedId, setDeleteRelatedId] = useState<string | null>(null)

  if (!client) {
    return (
      <div className="client-detail-page">
        <div className="empty-state">
          <h3>Client not found</h3>
          <button className="btn-primary" onClick={() => navigate('/clients')}>Back to Clients</button>
        </div>
      </div>
    )
  }

  const handleEditClient = (values: FormValues) => {
    setClient({
      ...client,
      name: values.name,
      phone: values.phone,
      phone_normalized: values.phone.replace(/[^0-9+]/g, ''),
      email: values.email,
      updated_at: new Date().toISOString()
    })
    setIsEditClientOpen(false)
  }

  const handleDeleteClient = () => {
    // In a real app we'd call API and navigate away
    navigate('/clients')
  }

  const handleSaveRelated = (values: FormValues) => {
    if (editRelatedId) {
      setRelatedPersons(prev => prev.map(rp => rp.id === editRelatedId ? {
        ...rp,
        name: values.name,
        phone: values.phone,
        phone_normalized: values.phone.replace(/[^0-9+]/g, ''),
        email: values.email,
        updated_at: new Date().toISOString()
      } : rp))
      setEditRelatedId(null)
    } else {
      const newRp: RelatedPerson = {
        id: `rp${Date.now()}`,
        name: values.name,
        phone: values.phone,
        phone_normalized: values.phone.replace(/[^0-9+]/g, ''),
        email: values.email,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        primary_client_id: client.id
      }
      setRelatedPersons([...relatedPersons, newRp])
      setIsAddRelatedOpen(false)
    }
  }

  const handleDeleteRelated = () => {
    setRelatedPersons(prev => prev.filter(rp => rp.id !== deleteRelatedId))
    setDeleteRelatedId(null)
  }

  const editRelatedPerson = relatedPersons.find(rp => rp.id === editRelatedId)

  return (
    <div className="client-detail-page">
      <Link to="/clients" className="back-link">
        <ChevronLeft size={16} /> {t('clients.title')}
      </Link>

      <div className="detail-header">
        <h1 style={{ fontSize: 28, fontWeight: 600, margin: 0 }}>{client.name}</h1>
        <div className="detail-actions">
          <button className="btn-secondary" onClick={() => setIsEditClientOpen(true)}>
            <Edit2 size={16} /> <span className="hide-mobile">{t('clients.edit')}</span>
          </button>
          <button className="btn-secondary" style={{ color: 'var(--color-danger)' }} onClick={() => setIsDeleteClientOpen(true)}>
            <Trash2 size={16} /> <span className="hide-mobile">{t('clients.remove')}</span>
          </button>
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
        <button className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }} onClick={() => setIsAddRelatedOpen(true)}>
          <Plus size={16} /> {t('clients.addRelatedPerson')}
        </button>
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
              <div className="detail-actions">
                <button className="action-btn-icon" onClick={() => setEditRelatedId(rp.id)} aria-label={t('clients.edit')}>
                  <Edit2 size={16} />
                </button>
                <button className="action-btn-icon" onClick={() => setDeleteRelatedId(rp.id)} aria-label={t('clients.remove')}>
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <ClientForm 
        isOpen={isEditClientOpen}
        onClose={() => setIsEditClientOpen(false)}
        onSave={handleEditClient}
        initialValues={client}
        title={t('clients.edit')}
      />

      <ClientForm 
        isOpen={isAddRelatedOpen || !!editRelatedId}
        onClose={() => { setIsAddRelatedOpen(false); setEditRelatedId(null); }}
        onSave={handleSaveRelated}
        initialValues={editRelatedPerson}
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
