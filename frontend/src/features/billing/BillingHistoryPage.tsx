import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, ArrowUpRight, Loader2, RefreshCw } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { ApiError } from '../../services/apiClient'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { billingApi } from './api'
import type { Invoice, InvoicePage } from './types'
import './billing.css'

const formatAmount = (amount: string, currency: string) => {
  const value = Number(amount)
  if (!Number.isFinite(value)) return `${amount} ${currency}`
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(value) } catch { return `${amount} ${currency}` }
}

function InvoiceSummary({ invoice }: { invoice: Invoice }) {
  const { t } = useTranslation()
  const date = invoice.issued_at ?? invoice.created_at
  return <article className="billing-invoice">
    <div className="billing-invoice-heading"><div><strong>{invoice.invoice_number ?? t('billing.draft', 'Draft invoice')}</strong><span className={`billing-status billing-status-${invoice.status.toLowerCase()}`}>{invoice.status}</span></div><span>{invoice.currency}</span></div>
    <p className="billing-history-meta">{date ? new Date(date).toLocaleString() : '—'} · {t('billing.clientRecord', 'Client')} {invoice.client_id.slice(0, 8)}</p>
    <ul className="billing-lines">{invoice.items.map(item => <li key={item.id}><span>{item.description} × {item.quantity}</span><strong>{formatAmount(item.line_total, invoice.currency)}</strong></li>)}</ul>
    <div className="billing-totals"><span>{t('billing.subtotal', 'Subtotal')} <strong>{formatAmount(invoice.subtotal, invoice.currency)}</strong></span>{Number(invoice.discount_total) > 0 && <span>{t('billing.discount', 'Discount')} <strong>−{formatAmount(invoice.discount_total, invoice.currency)}</strong></span>}{Number(invoice.tax_total) > 0 && <span>{t('billing.tax', 'Tax')} <strong>{formatAmount(invoice.tax_total, invoice.currency)}</strong></span>}<span>{t('billing.total', 'Total')} <strong>{formatAmount(invoice.total_amount, invoice.currency)}</strong></span><span>{t('billing.paid', 'Paid')} <strong>{formatAmount(String(Number(invoice.amount_paid) - Number(invoice.amount_refunded)), invoice.currency)}</strong></span><span>{t('billing.balance', 'Balance')} <strong>{formatAmount(invoice.balance, invoice.currency)}</strong></span>{Number(invoice.refund_due) > 0 && <span>{t('billing.refundDue', 'Refund due')} <strong>{formatAmount(invoice.refund_due, invoice.currency)}</strong></span>}</div>
    <div className="billing-history-footer"><span>{invoice.payments.length} {t('billing.payments', 'payments')} · {invoice.credit_notes.length} {t('billing.credits', 'credit notes')}</span><Link to={`/orders/${invoice.work_id}`}>{t('billing.openWork', 'Open Work')} <ArrowUpRight size={15} /></Link></div>
  </article>
}

export function BillingHistoryPage() {
  const { t } = useTranslation()
  const { shopId, role, workFunctions, isLoading: shopLoading } = useCurrentShop()
  const canView = role === 'ADMIN' || (role === 'STAFF' && workFunctions.includes('CASHIER'))
  const [mode, setMode] = useState<'ALL' | 'OUTSTANDING'>('ALL')
  const [status, setStatus] = useState('')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [applied, setApplied] = useState({ status: '', from: '', to: '' })
  const [page, setPage] = useState(1)
  const [data, setData] = useState<InvoicePage | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [refresh, setRefresh] = useState(0)

  useEffect(() => {
    if (!shopId || !canView) return
    let active = true
    setLoading(true); setError('')
    const request = mode === 'OUTSTANDING'
      ? billingApi.outstandingPage(shopId, page)
      : billingApi.historyPage(shopId, page, applied)
    request.then(result => { if (active) setData(result) })
      .catch(cause => { if (active) setError(cause instanceof ApiError ? cause.message : cause instanceof Error ? cause.message : t('billing.loadFailed', 'Unable to load billing records.')) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [shopId, canView, mode, page, applied, refresh, t])

  const applyFilters = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (from && to && from > to) { setError(t('billing.invalidDateRange', 'End date must be on or after start date.')); return }
    setPage(1); setApplied({ status, from, to })
  }

  if (shopLoading) return <main className="content-wrap billing-page" role="status">{t('billing.loading', 'Loading billing…')}</main>
  if (!shopId) return <main className="content-wrap billing-page" role="alert">{t('common.noShop', 'No Shop context is available.')}</main>
  if (!canView) return <main className="content-wrap billing-page" role="alert">{t('billing.permissionRequired', 'Shop ADMIN or CASHIER staff access is required.')}</main>

  return <main className="content-wrap billing-page">
    <header className="billing-page-heading"><div><p>{t('billing.eyebrow', 'Finance')}</p><h1>{t('billing.title', 'Billing')}</h1><span>{t('billing.historySubtitle', 'Shop invoices, payments, and outstanding balances.')}</span></div><button type="button" className="btn-secondary" onClick={() => setRefresh(value => value + 1)} disabled={loading}><RefreshCw size={16} />{t('common.refresh', 'Refresh')}</button></header>
    <div className="billing-tabs" role="tablist" aria-label={t('billing.views', 'Billing views')}><button type="button" role="tab" aria-selected={mode === 'ALL'} className={mode === 'ALL' ? 'active' : ''} onClick={() => { setMode('ALL'); setPage(1) }}>{t('billing.allInvoices', 'All invoices')}</button><button type="button" role="tab" aria-selected={mode === 'OUTSTANDING'} className={mode === 'OUTSTANDING' ? 'active' : ''} onClick={() => { setMode('OUTSTANDING'); setPage(1) }}>{t('billing.outstanding', 'Outstanding')}</button></div>
    {mode === 'ALL' && <form className="billing-history-filters" onSubmit={applyFilters}><label>{t('billing.status', 'Status')}<select value={status} onChange={event => setStatus(event.target.value)}><option value="">{t('billing.allStatuses', 'All statuses')}</option><option value="DRAFT">{t('billing.draft', 'Draft')}</option><option value="ISSUED">{t('billing.issued', 'Issued')}</option><option value="VOID">{t('billing.void', 'Void')}</option></select></label><label>{t('billing.from', 'Issued from')}<input type="date" value={from} onChange={event => setFrom(event.target.value)} /></label><label>{t('billing.to', 'Issued to')}<input type="date" value={to} onChange={event => setTo(event.target.value)} /></label><button type="submit" className="btn-primary">{t('billing.applyFilters', 'Apply filters')}</button></form>}
    {error && <div className="billing-error" role="alert"><AlertCircle size={17} />{error}<button type="button" className="btn-secondary" onClick={() => setRefresh(value => value + 1)}>{t('common.retry', 'Retry')}</button></div>}
    {loading ? <p className="billing-state" role="status"><Loader2 size={16} className="animate-spin" />{t('billing.loadingRecords', 'Loading billing records…')}</p> : !error && data?.results.length === 0 ? <p className="billing-state">{t('billing.emptyHistory', 'No matching invoices.')}</p> : !error && data && <><p className="billing-history-count">{data.count} {mode === 'OUTSTANDING' ? t('billing.outstandingInvoices', 'outstanding invoices') : t('billing.invoiceRecords', 'invoice records')}</p><div className="billing-list">{data.results.map(invoice => <InvoiceSummary key={invoice.id} invoice={invoice} />)}</div><nav className="billing-pagination" aria-label={t('common.pagination', 'Pagination')}><button type="button" className="btn-secondary" disabled={!data.previous || loading} onClick={() => setPage(value => Math.max(1, value - 1))}>{t('common.previous', 'Previous')}</button><span>{t('common.pageOf', 'Page {{page}}', { page })}</span><button type="button" className="btn-secondary" disabled={!data.next || loading} onClick={() => setPage(value => value + 1)}>{t('common.next', 'Next')}</button></nav></>}
  </main>
}
