import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Plus, Search, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react'
import type { Client } from './types'
import { ClientForm, type FormValues } from './ClientForm'
import { ConfirmDeleteModal } from './ConfirmDeleteModal'
import { clientsApi, type ContactWriteResult } from './api'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import './clients.css'

export function ClientsPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { shopId, role, isLoading: isShopLoading } = useCurrentShop()
  const [clients, setClients] = useState<Client[]>([])
  const [count, setCount] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 20
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState<{id:string;name:string}[]>([])
  const canWrite = role === 'ADMIN' || role === 'STAFF'
  const canDelete = role === 'ADMIN'

  const [isFormOpen, setIsFormOpen] = useState(false)
  
  const [deleteClient, setDeleteClient] = useState<Client | null>(null)

  const loadClients = useCallback(async () => {
    if (!shopId) { setIsLoading(isShopLoading); return }
    setIsLoading(true); setError('')
    try {
      const response = await clientsApi.list(shopId, searchQuery, page)
      setClients(response.results); setCount(response.count)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to load clients.')
    } finally { setIsLoading(false) }
  }, [shopId, isShopLoading, searchQuery, page])

  useEffect(() => { void loadClients() }, [loadClients])
  const totalPages = Math.ceil(count / pageSize)

  const handleAddClient = async (values: FormValues) => {
    if (!shopId) return
    setError(''); setNotice([])
    try {
      const created = await clientsApi.create(shopId, values) as ContactWriteResult<Client>
      setNotice(created.warnings?.flatMap(w => w.matches) ?? [])
      setIsFormOpen(false)
      if (page !== 1) setPage(1)
      else await loadClients()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to create client.') }
  }

  const confirmDelete = async () => {
    if (!deleteClient) return
    if (!shopId) return
    try {
      await clientsApi.remove(shopId, deleteClient.id)
      setDeleteClient(null)
      if (clients.length === 1 && page > 1) setPage(current => current - 1)
      else await loadClients()
    }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to remove client.') }
  }

  return (
    <div className="clients-page">
      <div className="clients-header">
        <div className="clients-title-area">
          <h1>{t('clients.title')}</h1>
          <p>{t('clients.subtitle')}</p>
        </div>
        {canWrite && <button className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }} onClick={() => setIsFormOpen(true)}>
          <Plus size={16} /> {t('clients.addClient')}
        </button>}
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

      {error && <div className="login-error-message" role="alert">{error}</div>}
      {notice.length > 0 && <div className="duplicate-warning" role="status"><strong>{t('clients.possibleDuplicate')}</strong><p>{t('clients.duplicateHint')}</p>{notice.map(item => <div key={item.id}>{item.name}</div>)}</div>}
      {isLoading ? <div className="empty-state" aria-busy="true">Loading clients…</div> : !shopId ? <div className="empty-state"><h3>Shop context unavailable</h3><p>Sign in with a Shop account to manage clients.</p></div> : clients.length === 0 ? (
        <div className="empty-state">
          <h3>{t('clients.noClients')}</h3>
          <p>{t('clients.noClientsHint')}</p>
          {canWrite && <button className="btn-primary" onClick={() => setIsFormOpen(true)}>
            {t('clients.addClient')}
          </button>}
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
                {clients.map(client => (
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
                      {canDelete && <button className="action-btn-icon" onClick={(e) => { e.stopPropagation(); setDeleteClient(client); }} aria-label={t('clients.remove')}>
                        <Trash2 size={16} />
                      </button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards (hidden on wide screens via CSS media queries, but we'll manage via CSS) */}
          <div className="clients-cards-list">
            {clients.map(client => (
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
                  {canDelete && <button
                    className="action-btn-icon" 
                    onClick={(e) => { e.stopPropagation(); setDeleteClient(client); }}
                    aria-label={t('clients.remove')}
                  >
                    <Trash2 size={16} />
                  </button>}
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
