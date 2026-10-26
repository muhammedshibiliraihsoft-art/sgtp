import { useCallback, useEffect, useState } from 'react'
import { AlertCircle, Loader2, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { ApiError } from '../services/apiClient'
import { shopsService } from '../services/shops'
import type { ShopSummary } from '../services/shops'
import { billingApi } from '../features/billing/api'
import type { Invoice, InvoicePage } from '../features/billing/types'
import './backoffice.css'
import '../features/billing/billing.css'

const errorMessage = (cause: unknown) => cause instanceof ApiError ? cause.message : cause instanceof Error ? cause.message : 'Unable to load financial records.'
const amount = (value: string, currency: string) => {
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(Number(value)) }
  catch { return `${value} ${currency}` }
}

export function FinancialPurgePage() {
  const { t } = useTranslation()
  const [shops, setShops] = useState<ShopSummary[]>([])
  const [shopId, setShopId] = useState('')
  const [page, setPage] = useState<InvoicePage | null>(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [loadingShops, setLoadingShops] = useState(true)
  const [loadingInvoices, setLoadingInvoices] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [retryTarget, setRetryTarget] = useState<'shops' | 'invoices' | 'purge'>('shops')
  const [notice, setNotice] = useState('')
  const [target, setTarget] = useState<Invoice | null>(null)
  const [reason, setReason] = useState('')
  const [confirmation, setConfirmation] = useState('')

  const loadShops = useCallback(async (isActive: () => boolean = () => true) => {
    if (isActive()) { setLoadingShops(true); setError(''); setRetryTarget('shops') }
    try {
      const rows: ShopSummary[] = []
      let currentPage = 1
      while (true) {
        const result = await shopsService.list('', currentPage, { active: 'all', ordering: 'name' })
        rows.push(...result.results)
        if (!result.next) break
        currentPage += 1
      }
      if (isActive()) setShops(rows)
    } catch (cause) {
      if (isActive()) setError(errorMessage(cause))
    } finally {
      if (isActive()) setLoadingShops(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    void loadShops(() => active)
    return () => { active = false }
  }, [loadShops])

  const loadInvoices = useCallback(async () => {
    if (!shopId) { setPage(null); return }
    setLoadingInvoices(true); setError(''); setRetryTarget('invoices')
    try { setPage(await billingApi.historyPage(shopId, pageNumber)) }
    catch (cause) { setError(errorMessage(cause)) }
    finally { setLoadingInvoices(false) }
  }, [shopId, pageNumber])

  useEffect(() => { void loadInvoices() }, [loadInvoices])

  const purge = async () => {
    const invoice = target
    if (!invoice?.invoice_number || !reason.trim() || confirmation.trim() !== invoice.invoice_number || busy) return
    setBusy(true); setError(''); setNotice(''); setRetryTarget('purge')
    try {
      const result = await billingApi.purgeInvoiceBundle(shopId, invoice.id, {
        reason: reason.trim(), confirm_invoice_number: confirmation.trim(),
      })
      if (result.status === 'COMPLETED') {
        setTarget(null); setReason(''); setConfirmation('')
        setNotice(t('billing.purgeCompleted', 'Invoice and linked financial records were permanently deleted. Audit and sequence history was retained.'))
        await loadInvoices()
      } else {
        setError(t('billing.purgeRetry', 'Private PDF cleanup is incomplete. Financial database records remain protected; correct the storage issue and retry.'))
      }
    } catch (cause) { setError(errorMessage(cause)) }
    finally { setBusy(false) }
  }

  const retry = () => {
    if (retryTarget === 'shops') void loadShops()
    else if (retryTarget === 'purge') void purge()
    else void loadInvoices()
  }

  return <div className="content-wrap bo-content billing-page">
    <div className="bo-page-heading"><div><span className="bo-eyebrow">{t('backoffice.eyebrow', 'Main Supplier')}</span><h1>{t('billing.purgePageTitle', 'Financial purge')}</h1><p>{t('billing.purgePageIntro', 'Select a Shop to review issued financial records. This is a manual, permanent action.')}</p></div></div>
    <div className="billing-purge-toolbar"><label>{t('backoffice.shop', 'Shop')}<select value={shopId} onChange={event => { setShopId(event.target.value); setPageNumber(1); setNotice('') }} disabled={loadingShops || busy}><option value="">{t('billing.chooseShop', 'Choose a Shop')}</option>{shops.map(shop => <option key={shop.id} value={shop.id} disabled={!shop.is_active}>{shop.name}{shop.is_active ? '' : ` · ${t('backoffice.inactive', 'Inactive')}`}</option>)}</select></label><p><AlertCircle size={16} />{t('billing.purgePolicy', 'Draft invoices use the normal draft-delete action. Purging an issued invoice also removes linked payments, credit notes, refunds, and private PDFs. Existing audit/idempotency rows and Shop invoice-number sequences are retained.')}</p></div>
    {error && <div className="billing-error" role="alert">{error}<button type="button" className="btn-secondary" onClick={retry} disabled={loadingShops || loadingInvoices || busy}>{t('common.retry', 'Retry')}</button></div>}
    {notice && <p className="billing-notice" role="status">{notice}</p>}
    {!shopId ? <p className="billing-state">{loadingShops ? t('backoffice.loading', 'Loading Shops…') : t('billing.chooseShopPrompt', 'Choose a Shop to review its invoices.')}</p> : loadingInvoices ? <p className="billing-state" role="status"><Loader2 size={16} className="animate-spin" />{t('billing.loading', 'Loading invoices…')}</p> : page && page.results.length === 0 ? <p className="billing-state">{t('billing.noInvoices', 'No invoices for this Shop.')}</p> : page && <div className="billing-list">{page.results.map(invoice => <article className="billing-invoice" key={invoice.id}>
      <div className="billing-invoice-heading"><div><strong>{invoice.invoice_number ?? t('billing.draft', 'Draft invoice')}</strong><span className={`billing-status billing-status-${invoice.status.toLowerCase()}`}>{invoice.status}</span></div><span>{invoice.currency}</span></div>
      <div className="billing-purge-record-meta"><span>{t('billing.workId', 'Work')}: {invoice.work_id}</span><span>{t('billing.clientId', 'Client')}: {invoice.client_id}</span><span>{invoice.issued_at ? new Date(invoice.issued_at).toLocaleString() : '—'}</span></div>
      <div className="billing-totals"><span>{t('billing.total', 'Total')} <strong>{amount(invoice.total_amount, invoice.currency)}</strong></span><span>{t('billing.paid', 'Paid')} <strong>{amount(String(Number(invoice.amount_paid) - Number(invoice.amount_refunded)), invoice.currency)}</strong></span><span>{t('billing.balance', 'Balance')} <strong>{amount(invoice.balance, invoice.currency)}</strong></span></div>
      {invoice.status !== 'DRAFT' && <div className="billing-actions"><button type="button" className="btn-danger billing-purge-action" onClick={() => { setTarget(invoice); setReason(''); setConfirmation(''); setError('') }} disabled={busy}><Trash2 size={15} />{t('billing.purgeIssued', 'Permanently delete financial bundle')}</button></div>}
    </article>)}</div>}
    {page && page.count > 20 && <div className="billing-pagination"><button type="button" onClick={() => setPageNumber(current => Math.max(1, current - 1))} disabled={pageNumber <= 1 || loadingInvoices}>{t('common.previous', 'Previous')}</button><span>{pageNumber} / {Math.ceil(page.count / 20)}</span><button type="button" onClick={() => setPageNumber(current => current + 1)} disabled={!page.next || loadingInvoices}>{t('common.next', 'Next')}</button></div>}
    {target && <div className="billing-purge-backdrop"><section className="billing-purge-dialog" role="dialog" aria-modal="true" aria-labelledby="billing-purge-title">
      <h2 id="billing-purge-title">{t('billing.purgeTitle', 'Permanently delete financial bundle?')}</h2><p>{t('billing.purgeWarning', 'This removes the invoice, linked payments, credit notes, refunds and private PDFs. Existing audit and idempotency history and Shop sequence numbers are retained. This cannot be undone.')}</p>
      <label>{t('billing.purgeReason', 'Reason')}<textarea value={reason} onChange={event => setReason(event.target.value)} maxLength={500} rows={3} disabled={busy} /></label>
      <label>{t('billing.purgeConfirmNumber', 'Type the invoice number to confirm')}<input value={confirmation} onChange={event => setConfirmation(event.target.value)} autoComplete="off" disabled={busy} /></label>
      <div className="billing-action-row"><button type="button" className="btn-secondary" onClick={() => setTarget(null)} disabled={busy}>{t('common.cancel', 'Cancel')}</button><button type="button" className="btn-danger billing-purge-action" onClick={() => void purge()} disabled={busy || !reason.trim() || confirmation.trim() !== target.invoice_number}>{busy ? <Loader2 size={15} className="animate-spin" /> : <Trash2 size={15} />}{t('billing.confirmPurge', 'Delete permanently')}</button></div>
    </section></div>}
  </div>
}
