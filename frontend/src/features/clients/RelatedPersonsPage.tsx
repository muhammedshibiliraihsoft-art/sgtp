import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ChevronLeft, Edit2, Plus, Trash2, Users } from 'lucide-react'
import { ClientForm, type FormValues } from './ClientForm'
import { ConfirmDeleteModal } from './ConfirmDeleteModal'
import { clientsApi, type ContactWriteResult } from './api'
import type { Client, RelatedPerson } from './types'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import './clients.css'

export function RelatedPersonsPage() {
  const { clientId = '' } = useParams<{ clientId: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { shopId, role, isLoading: isShopLoading } = useCurrentShop()
  const [client, setClient] = useState<Client | null>(null)
  const [relatedPersons, setRelatedPersons] = useState<RelatedPerson[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [duplicateMatches, setDuplicateMatches] = useState<{ id: string; name: string }[]>([])
  const [isAddOpen, setIsAddOpen] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const canWrite = role === 'ADMIN' || role === 'STAFF'
  const canDelete = role === 'ADMIN'

  const loadData = useCallback(async () => {
    if (!shopId || !clientId) { setLoading(isShopLoading); return }
    setLoading(true)
    setError('')
    try {
      const [loadedClient, related] = await Promise.all([
        clientsApi.detail(shopId, clientId),
        clientsApi.related(shopId, clientId),
      ])
      setClient(loadedClient)
      setRelatedPersons(related.results)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to load related persons.')
    } finally {
      setLoading(false)
    }
  }, [shopId, clientId, isShopLoading])

  useEffect(() => { void loadData() }, [loadData])

  const handleSave = async (values: FormValues) => {
    if (!shopId || !client) return
    try {
      if (editId) {
        const updated = await clientsApi.updateRelated(shopId, client.id, editId, values) as ContactWriteResult<RelatedPerson>
        setRelatedPersons(previous => previous.map(person => person.id === updated.id ? updated : person))
        setDuplicateMatches(updated.warnings?.flatMap(warning => warning.matches) ?? [])
        setEditId(null)
      } else {
        const created = await clientsApi.createRelated(shopId, client.id, values) as ContactWriteResult<RelatedPerson>
        setRelatedPersons(previous => [...previous, created])
        setDuplicateMatches(created.warnings?.flatMap(warning => warning.matches) ?? [])
        setIsAddOpen(false)
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to save related person.')
    }
  }

  const handleDelete = async () => {
    if (!shopId || !client || !deleteId) return
    try {
      await clientsApi.removeRelated(shopId, client.id, deleteId)
      setRelatedPersons(previous => previous.filter(person => person.id !== deleteId))
      setDeleteId(null)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to remove related person.')
    }
  }

  if (loading) return <div className="client-detail-page"><div className="empty-state" aria-busy="true">Loading…</div></div>
  if (!client) return <div className="client-detail-page"><div className="empty-state"><h3>{error || 'Client not found'}</h3><button className="btn-primary" onClick={() => navigate('/clients')}>{t('clients.title')}</button></div></div>

  const editPerson = relatedPersons.find(person => person.id === editId)

  return <div className="client-detail-page related-persons-page">
    <Link to={`/clients/${client.id}`} className="back-link"><ChevronLeft size={16} /> {client.name}</Link>
    {error && <div className="login-error-message" role="alert">{error}</div>}
    {duplicateMatches.length > 0 && <div className="duplicate-warning" role="status"><strong>{t('clients.possibleDuplicate')}</strong>{duplicateMatches.map(match => <div key={match.id}>{match.name}</div>)}</div>}
    <div className="related-persons-heading">
      <h1><Users size={22} /> {t('clients.relatedPersons')}</h1>
      {canWrite && <button type="button" className="btn-primary" onClick={() => setIsAddOpen(true)}><Plus size={17} /> {t('clients.addRelatedPerson')}</button>}
    </div>
    {relatedPersons.length === 0 ? <div className="empty-state"><p>{t('clients.noRelated')}</p></div> : <div className="clients-cards-list">
      {relatedPersons.map(person => <article className="client-card" key={person.id}>
        <div className="client-card-info"><strong className="client-card-name">{person.name}</strong>{(person.phone || person.email) && <span className="client-card-detail">{person.phone}{person.phone && person.email ? ' · ' : ''}{person.email}</span>}</div>
        {canWrite && <div className="detail-actions">
          <button type="button" className="action-btn-icon" onClick={() => setEditId(person.id)} aria-label={t('clients.edit')}><Edit2 size={16} /></button>
          {canDelete && <button type="button" className="action-btn-icon" onClick={() => setDeleteId(person.id)} aria-label={t('clients.remove')}><Trash2 size={16} /></button>}
        </div>}
      </article>)}
    </div>}
    <ClientForm isOpen={isAddOpen || Boolean(editId)} onClose={() => { setIsAddOpen(false); setEditId(null) }} onSave={handleSave} initialValues={editPerson} duplicateMatches={duplicateMatches} title={editId ? t('clients.edit') : t('clients.addRelatedPerson')} />
    <ConfirmDeleteModal isOpen={Boolean(deleteId)} onClose={() => setDeleteId(null)} onConfirm={handleDelete} title={t('clients.remove')} message={t('clients.confirmRemoveRelated')} />
  </div>
}
