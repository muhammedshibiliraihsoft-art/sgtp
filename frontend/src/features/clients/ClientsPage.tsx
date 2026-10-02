import { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Plus, Search, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react'
import { mockClients } from './mockClients'
import type { Client } from './types'
import { ClientForm, type FormValues } from './ClientForm'
import { ConfirmDeleteModal } from './ConfirmDeleteModal'
import './clients.css'

export function ClientsPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  
  const [clients, setClients] = useState<Client[]>(mockClients)
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 20

  const [isFormOpen, setIsFormOpen] = useState(false)
  
  const [deleteClient, setDeleteClient] = useState<Client | null>(null)

  const filteredClients = useMemo(() => {
    if (!searchQuery.trim()) return clients
    const q = searchQuery.toLowerCase()
    return clients.filter(c => 
      c.name.toLowerCase().includes(q) || 
      c.phone_normalized.includes(q) || 
      c.phone.includes(q) ||
      c.id.toLowerCase().includes(q)
    )
  }, [clients, searchQuery])

  const paginatedClients = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredClients.slice(start, start + pageSize)
  }, [filteredClients, page])

  const totalPages = Math.ceil(filteredClients.length / pageSize)

  const handleAddClient = (values: FormValues) => {
    const newClient: Client = {
      id: `c${Date.now()}`,
      name: values.name,
      phone: values.phone,
      phone_normalized: values.phone.replace(/[^0-9+]/g, ''),
      email: values.email,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    setClients([newClient, ...clients])
    setIsFormOpen(false)
  }

  const confirmDelete = () => {
    if (!deleteClient) return
    setClients(clients.filter(c => c.id !== deleteClient.id))
    setDeleteClient(null)
  }

  return (
    <div className="clients-page">
      <div className="clients-header">
        <div className="clients-title-area">
          <h1>{t('clients.title')}</h1>
          <p>{t('clients.subtitle')}</p>
        </div>
        <button className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }} onClick={() => setIsFormOpen(true)}>
          <Plus size={16} /> {t('clients.addClient')}
        </button>
      </div>

      <div className="clients-controls">
        <div className="clients-search">
          <Search size={16} />
          <input 
            placeholder={t('clients.searchPlaceholder')}
            value={searchQuery}
            onChange={e => { setSearchQuery(e.target.value); setPage(1); }}
          />
        </div>
      </div>

      {clients.length === 0 ? (
        <div className="empty-state">
          <h3>{t('clients.noClients')}</h3>
          <p>{t('clients.noClientsHint')}</p>
          <button className="btn-primary" onClick={() => setIsFormOpen(true)}>
            {t('clients.addClient')}
          </button>
        </div>
      ) : (
        <>
          {/* Desktop Table (hidden on narrow screens via CSS) */}
          <div className="clients-table-container">
            <table className="clients-table">
              <thead>
                <tr>
                  <th className="col-name">{t('clients.name')}</th>
                  <th className="col-phone">{t('clients.phone')}</th>
                  <th className="col-email">{t('clients.email')}</th>
                  <th className="col-contact" aria-hidden="true">{t('clients.phone')}</th>
                  <th className="col-updated">{t('clients.updatedAt', 'Updated')}</th>
                  <th className="client-actions-cell">{t('clients.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {paginatedClients.map(client => (
                  <tr key={client.id} onClick={() => navigate(`/clients/${client.id}`)}>
                    <td className="client-name-cell col-name">
                      <div className="text-truncate" title={client.name}>{client.name}</div>
                    </td>
                    <td className="client-secondary-cell col-phone">
                      <div className="text-truncate">{client.phone || '—'}</div>
                    </td>
                    <td className="client-secondary-cell col-email">
                      <div className="text-truncate" title={client.email}>{client.email || '—'}</div>
                    </td>
                    <td className="client-secondary-cell col-contact">
                      <div className="text-truncate">{client.phone || '—'}</div>
                      <div className="text-truncate" style={{ fontSize: '12px', opacity: 0.8 }} title={client.email}>{client.email || ''}</div>
                    </td>
                    <td className="client-secondary-cell col-updated">
                      {new Date(client.updated_at).toLocaleDateString()}
                    </td>
                    <td className="client-actions-cell" onClick={e => e.stopPropagation()}>
                      <button className="action-btn-icon" onClick={(e) => { e.stopPropagation(); setDeleteClient(client); }} aria-label={t('clients.remove')}>
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards (hidden on wide screens via CSS media queries, but we'll manage via CSS) */}
          <div className="clients-cards-list">
            {paginatedClients.map(client => (
              <div key={client.id} className="client-card" onClick={() => navigate(`/clients/${client.id}`)}>
                <div className="client-card-info">
                  <span className="client-card-name">{client.name}</span>
                  {(client.phone || client.email) && (
                    <span className="client-card-detail">
                      {client.phone}{client.phone && client.email ? ' · ' : ''}<span className="email-wrap">{client.email}</span>
                    </span>
                  )}
                  <span className="client-card-date">
                    {t('clients.updatedAt', 'Updated')}: {new Date(client.updated_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="client-card-actions">
                  <button 
                    className="action-btn-icon" 
                    onClick={(e) => { e.stopPropagation(); setDeleteClient(client); }}
                    aria-label={t('clients.remove')}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>


          {totalPages > 1 && (
            <div className="pagination-controls">
              <button 
                className="pagination-btn" 
                disabled={page <= 1} 
                onClick={() => setPage(p => p - 1)}
              >
                <ChevronLeft size={16} /> {t('backoffice.previous')}
              </button>
              <span className="pagination-info">
                {t('backoffice.page', { page: page })} / {totalPages}
              </span>
              <button 
                className="pagination-btn" 
                disabled={page >= totalPages} 
                onClick={() => setPage(p => p + 1)}
              >
                {t('backoffice.next')} <ChevronRight size={16} />
              </button>
            </div>
          )}
        </>
      )}

      <ClientForm 
        isOpen={isFormOpen} 
        onClose={() => setIsFormOpen(false)}
        onSave={handleAddClient}
        title={t('clients.addClient')}
      />

      <ConfirmDeleteModal
        isOpen={!!deleteClient}
        onClose={() => setDeleteClient(null)}
        onConfirm={confirmDelete}
        title={t('clients.remove')}
        message={t('clients.confirmRemove')}
      />
    </div>
  )
}
