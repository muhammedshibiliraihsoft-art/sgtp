import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowRight, ChevronLeft, Clock, Edit2, Ruler, Trash2, Users } from 'lucide-react'
import type { Client, RelatedPerson } from './types'
import { ClientForm, type FormValues } from './ClientForm'
import { ConfirmDeleteModal } from './ConfirmDeleteModal'
import { clientsApi, type ContactWriteResult } from './api'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { getAllFamilies } from '../catalog/api'
import { measurementApi } from '../measurements/api'
import type { MeasurementOwner, MeasurementProfile, MeasurementSet } from '../measurements/types'
import './clients.css'

type MeasurementHistoryRecord = {
  profile: MeasurementProfile
  owner: MeasurementOwner
  wearerName: string
  familyName: string
  latestSet: MeasurementSet
}

export function ClientDetailPage() {
  const { clientId } = useParams<{ clientId: string }>()
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()
  const { shopId, role, workFunctions, isLoading: isShopLoading } = useCurrentShop()

  const [client, setClient] = useState<Client | undefined>()
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [duplicateMatches, setDuplicateMatches] = useState<{id:string;name:string}[]>([])
  const [measurementHistory, setMeasurementHistory] = useState<MeasurementHistoryRecord[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState('')
  const canWrite = role === 'ADMIN' || role === 'STAFF'
  const canDelete = role === 'ADMIN'
  const canReadMeasurements = role === 'ADMIN' || (role === 'STAFF' && workFunctions.includes('MEASUREMENT'))

  const loadData = useCallback(async () => {
    if (!shopId || !clientId) { setIsLoading(isShopLoading); return }
    setIsLoading(true); setError('')
    try {
      setClient(await clientsApi.detail(shopId, clientId))
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to load client.') }
    finally { setIsLoading(false) }
  }, [shopId, clientId, isShopLoading])

  useEffect(() => { void loadData() }, [loadData])

  useEffect(() => {
    if (!shopId || !clientId || !client || !canReadMeasurements) {
      setMeasurementHistory([])
      setHistoryLoading(false)
      return
    }
    let active = true
    const locale = ['en', 'ar-KW', 'bn', 'ur'].includes(i18n.resolvedLanguage || '') ? i18n.resolvedLanguage! : 'en'
    setHistoryLoading(true)
    setHistoryError('')

    void Promise.all([
      clientsApi.relatedAll(shopId, clientId),
      getAllFamilies(locale),
    ]).then(async ([people, families]) => {
      const owners: Array<{ owner: MeasurementOwner; name: string }> = [
        { owner: { kind: 'client' }, name: client.name },
        ...people.map((person: RelatedPerson) => ({ owner: { kind: 'related_person' as const, id: person.id }, name: person.name })),
      ]
      const profilesByOwner = await Promise.all(owners.map(async ownerInfo => ({
        ...ownerInfo,
        profiles: await measurementApi.profiles(shopId, clientId, ownerInfo.owner),
      })))
      const profiles = profilesByOwner.flatMap(ownerInfo => ownerInfo.profiles.map(profile => ({
        profile,
        owner: ownerInfo.owner,
        wearerName: ownerInfo.name,
      })))
      const records = await Promise.all(profiles.map(async item => {
        const sets = await measurementApi.sets(shopId, clientId, item.owner, item.profile.id)
        const orderedSets = [...sets].sort((left, right) => Date.parse(right.created_at) - Date.parse(left.created_at))
        const latestSet = orderedSets[0]
        if (!latestSet) return null
        return {
          ...item,
          familyName: families.find(family => family.id === item.profile.family)?.name ?? t('measurements.garment'),
          latestSet,
        }
      }))
      if (active) {
        setMeasurementHistory(records.filter((record): record is MeasurementHistoryRecord => record !== null)
          .sort((left, right) => Date.parse(right.latestSet.created_at) - Date.parse(left.latestSet.created_at)))
      }
    }).catch(cause => {
      if (active) setHistoryError(cause instanceof Error ? cause.message : t('measurements.loadError'))
    }).finally(() => {
      if (active) setHistoryLoading(false)
    })

    return () => { active = false }
  }, [shopId, clientId, client, canReadMeasurements, i18n.resolvedLanguage, t])

  const [isEditClientOpen, setIsEditClientOpen] = useState(false)
  const [isDeleteClientOpen, setIsDeleteClientOpen] = useState(false)
  
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

  return (
    <div className="client-detail-page">
      {error && <div className="login-error-message" role="alert">{error}</div>}
      {duplicateMatches.length > 0 && <div className="duplicate-warning" role="status"><strong>{t('clients.possibleDuplicate')}</strong>{duplicateMatches.map(match => <div key={match.id}>{match.name}</div>)}</div>}
      <Link to="/clients" className="back-link">
        <ChevronLeft size={16} /> {t('clients.title')}
      </Link>

      <div className="detail-header">
        <h1 style={{ fontSize: 28, fontWeight: 600, margin: 0 }}>{client.name}</h1>
        <div className={`detail-actions${canWrite ? ' has-edit' : ''}${canDelete ? ' has-delete' : ''}`}>
          <Link to={`/clients/${client.id}/measurements`} className="btn-secondary"><Ruler size={16} /> <span className="hide-mobile">Measurements</span></Link>
          {canWrite && <button className="btn-secondary" onClick={() => setIsEditClientOpen(true)}>
            <Edit2 size={16} /> <span className="hide-mobile">{t('clients.edit')}</span>
          </button>}
          {canDelete && <button className="btn-secondary" style={{ color: 'var(--color-danger)' }} onClick={() => setIsDeleteClientOpen(true)}>
            <Trash2 size={16} /> <span className="hide-mobile">{t('clients.remove')}</span>
          </button>}
          <Link to={`/clients/${client.id}/related-persons`} className="btn-secondary"><Users size={16} /> <span>{t('clients.relatedPersons')}</span></Link>
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

      {canReadMeasurements && <section className="client-detail-history" aria-labelledby="client-measurement-history-heading">
        <div className="client-detail-related-header"><h2 id="client-measurement-history-heading"><Clock size={19} /> {t('measurements.history')}</h2></div>
        {historyLoading ? <div className="client-history-empty" aria-busy="true">{t('measurements.loading')}</div>
          : historyError ? <div className="client-history-empty" role="status">{historyError}</div>
            : measurementHistory.length === 0 ? <div className="client-history-empty">{t('measurements.noHistory')}</div>
              : <div className="client-history-list">{measurementHistory.map(record => {
                const query = new URLSearchParams({ view: 'history', wearer: record.owner.kind === 'client' ? 'client' : record.owner.id, family: record.profile.family, profile: record.profile.id, set: record.latestSet.id })
                return <article className="client-history-card" key={record.profile.id}>
                  <div className="client-history-card-copy">
                    <strong>{record.familyName}</strong>
                    <span>{record.wearerName}</span>
                    <small>{new Date(record.latestSet.created_at).toLocaleDateString(i18n.resolvedLanguage || undefined)} · {t('measurements.version', { version: record.latestSet.version })}</small>
                  </div>
                  <Link to={`/clients/${client.id}/measurements?${query.toString()}`} className="btn-secondary" aria-label={`${t('measurements.history')}: ${record.familyName}, ${record.wearerName}`}>
                    {t('measurements.history')} <ArrowRight size={16} />
                  </Link>
                </article>
              })}</div>}
      </section>}

      <ClientForm 
        isOpen={isEditClientOpen}
        onClose={() => setIsEditClientOpen(false)}
        onSave={handleEditClient}
        initialValues={client}
        duplicateMatches={duplicateMatches}
        title={t('clients.edit')}
      />

      <ConfirmDeleteModal
        isOpen={isDeleteClientOpen}
        onClose={() => setIsDeleteClientOpen(false)}
        onConfirm={handleDeleteClient}
        title={t('clients.remove')}
        message={t('clients.confirmRemove')}
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
