import { useEffect, useState } from 'react'
import { Archive, ArrowLeft, Search } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { ordersApi } from './api'
import type { DeletedOrder } from './types'
import './orders.css'

type Filters = { search: string; deletedFrom: string; deletedTo: string }
const emptyFilters: Filters = { search: '', deletedFrom: '', deletedTo: '' }

export function DeletedOrdersPage() {
  const { t, i18n } = useTranslation()
  const { shopId, role, isLoading } = useCurrentShop()
  const [draft, setDraft] = useState<Filters>(emptyFilters)
  const [filters, setFilters] = useState<Filters>(emptyFilters)
  const [orders, setOrders] = useState<DeletedOrder[]>([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    if (!shopId || role !== 'ADMIN') return
    let active = true
    setLoading(true)
    setError('')
    void ordersApi.deletedList(shopId, { page, ...filters }).then(result => {
      if (!active) return
      setOrders(result.results)
      setCount(result.count)
    }).catch(cause => {
      if (active) setError(cause instanceof Error ? cause.message : t('orders.archive.loadFailed', 'Unable to load deleted orders.'))
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [shopId, role, page, filters, retry, t])

  if (isLoading) return <div className="content-wrap orders-page" role="status">{t('orders.loading', 'Loading orders…')}</div>
  if (!shopId) return <div className="content-wrap orders-page" role="alert">{t('orders.archive.noShop', 'No Shop context is available.')}</div>
  if (role !== 'ADMIN') return <div className="content-wrap orders-page" role="alert">{t('orders.archive.adminOnly', 'Only a Shop Admin can view deleted orders.')}</div>

  const applyFilters = (event: React.FormEvent) => {
    event.preventDefault()
    if (draft.deletedFrom && draft.deletedTo && draft.deletedFrom > draft.deletedTo) {
      setError(t('orders.archive.invalidRange', 'The end date must be on or after the start date.'))
      return
    }
    setPage(1)
    setFilters({ ...draft, search: draft.search.trim() })
  }
  const clearFilters = () => {
    setDraft(emptyFilters)
    setFilters(emptyFilters)
    setPage(1)
  }
  const createdDate = (value: string) => new Date(value).toLocaleDateString(i18n.language)

  return <div className="content-wrap orders-page">
    <header className="orders-heading"><div><Link className="orders-back" to="/orders"><ArrowLeft size={17} /> {t('nav.orders')}</Link><h1><Archive size={24} aria-hidden="true" /> {t('orders.archive.title', 'Deleted Orders')}</h1><p>{t('orders.archive.subtitle', 'Read-only history of deleted orders in this Shop.')}</p></div></header>
    <form className="orders-archive-filters" onSubmit={applyFilters}>
      <label className="orders-search"><Search size={17} aria-hidden="true" /><input value={draft.search} onChange={event => setDraft(current => ({ ...current, search: event.target.value }))} placeholder={t('orders.search', 'Search work number or client')} aria-label={t('orders.search', 'Search work number or client')} /></label>
      <label>{t('orders.archive.from', 'Deleted from')}<input type="date" value={draft.deletedFrom} max={draft.deletedTo || undefined} onChange={event => setDraft(current => ({ ...current, deletedFrom: event.target.value }))} /></label>
      <label>{t('orders.archive.to', 'Deleted to')}<input type="date" value={draft.deletedTo} min={draft.deletedFrom || undefined} onChange={event => setDraft(current => ({ ...current, deletedTo: event.target.value }))} /></label>
      <div className="orders-archive-filter-actions"><button className="orders-primary" type="submit">{t('orders.archive.apply', 'Apply filters')}</button><button className="orders-secondary" type="button" onClick={clearFilters}>{t('orders.archive.clear', 'Clear')}</button></div>
    </form>
    {error && <div className="orders-error" role="alert">{error}<button type="button" onClick={() => setRetry(current => current + 1)}>{t('orders.retry', 'Retry')}</button></div>}
    {loading ? <p className="orders-empty" role="status">{t('orders.archive.loading', 'Loading deleted orders…')}</p> : error ? null : !orders.length ? <p className="orders-empty">{t('orders.archive.empty', 'No deleted orders match these filters.')}</p> : <div className="orders-grid">{orders.map(order => <article className="orders-card" key={order.id}><div className="orders-card-top"><strong>{order.work_number}</strong><span className="orders-stage">{t('orders.archive.deleted', 'Deleted')}</span></div><dl className="orders-archive-meta"><div><dt>{t('orders.archive.client', 'Client')}</dt><dd>{order.client_name}</dd></div><div><dt>{t('orders.archive.garment', 'Garment')}</dt><dd>{order.design_name || '—'}</dd></div><div><dt>{t('orders.stage', 'Stage')}</dt><dd>{order.status}</dd></div><div><dt>{t('orders.archive.created', 'Created')}</dt><dd>{createdDate(order.created_at)}</dd></div><div><dt>{t('orders.archive.deletedOn', 'Deleted on')}</dt><dd>{order.deleted_date}</dd></div></dl></article>)}</div>}
    {count > 20 && <div className="orders-pages"><button type="button" disabled={page <= 1} onClick={() => setPage(current => current - 1)}>{t('orders.previous', 'Previous')}</button><span>{page} / {Math.ceil(count / 20)}</span><button type="button" disabled={page * 20 >= count} onClick={() => setPage(current => current + 1)}>{t('orders.next', 'Next')}</button></div>}
  </div>
}
