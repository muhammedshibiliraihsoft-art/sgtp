import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertCircle, FileText, Loader2, Plus, RefreshCw, Trash2 } from 'lucide-react'
import { ApiError } from '../../services/apiClient'
import { billingApi } from './api'
import type { CreditNote, DiscountType, FinancialDocument, Invoice, ManualInvoiceLineInput } from './types'
import './billing.css'

const EMPTY_LINE: ManualInvoiceLineInput = { description: '', quantity: '1', unit_price: '' }
const errorMessage = (error: unknown) => error instanceof ApiError ? error.message : error instanceof Error ? error.message : 'The billing request failed.'
const formatAmount = (amount: string, currency: string) => {
  const value = Number(amount)
  if (!Number.isFinite(value)) return `${amount} ${currency}`
  try { return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(value) } catch { return `${amount} ${currency}` }
}

export function BillingPanel({ shopId, workId, currency, canManage }: { shopId: string; workId: string; currency: string | null; canManage: boolean }) {
  const { t, i18n } = useTranslation()
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [retry, setRetry] = useState(0)
  const [mode, setMode] = useState<'AUTO' | 'MANUAL'>('AUTO')
  const [lines, setLines] = useState<ManualInvoiceLineInput[]>([{ ...EMPTY_LINE }])
  const [discountType, setDiscountType] = useState<DiscountType>('NONE')
  const [discountValue, setDiscountValue] = useState('')
  const [taxRate, setTaxRate] = useState('')
  const [paymentAmounts, setPaymentAmounts] = useState<Record<string, string>>({})
  const [voidReasons, setVoidReasons] = useState<Record<string, string>>({})
  const [creditDrafts, setCreditDrafts] = useState<Record<string, { amount: string; reason: string }>>({})
  const [refundDrafts, setRefundDrafts] = useState<Record<string, { paymentId: string; amount: string }>>({})
  const [lineDrafts, setLineDrafts] = useState<Record<string, ManualInvoiceLineInput>>({})
  const [documentLocale, setDocumentLocale] = useState<FinancialDocument['locale']>(() => {
    const locale = i18n.resolvedLanguage ?? 'en'
    return locale === 'ar' || locale === 'ar-KW' ? 'ar-KW' : locale === 'bn' || locale === 'ur' ? locale : 'en'
  })

  const load = useCallback(async () => {
    if (!canManage) return
    setLoading(true)
    setError('')
    try { setInvoices(await billingApi.listForWork(shopId, workId)) }
    catch (cause) { setError(errorMessage(cause)) }
    finally { setLoading(false) }
  }, [shopId, workId, canManage])

  useEffect(() => { void load() }, [load, retry])

  const perform = async (action: () => Promise<unknown>, success: string, reload = true) => {
    if (busy) return false
    setBusy(true); setError(''); setNotice('')
    try {
      await action()
      setNotice(success)
      if (reload) await load()
      return true
    } catch (cause) { setError(errorMessage(cause)) }
    finally { setBusy(false) }
    return false
  }

  const create = () => {
    if (!currency || busy) return
    const manual = lines.filter(line => line.description.trim() && line.unit_price.trim())
    if (mode === 'MANUAL' && manual.length === 0) { setError(t('billing.lineRequired', 'Add at least one manual line.')); return }
    void perform(() => billingApi.createDraft(shopId, workId, {
      mode, lines: manual.map(line => ({ ...line, description: line.description.trim() })),
      discount_type: discountType, discount_value: discountType === 'NONE' ? '0' : discountValue || '0', tax_rate: taxRate.trim() || null,
    }), t('billing.draftCreated', 'Draft invoice created.')).then(succeeded => {
      if (succeeded) { setLines([{ ...EMPTY_LINE }]); setDiscountType('NONE'); setDiscountValue(''); setTaxRate('') }
    })
  }

  const removeDraft = (invoice: Invoice) => {
    if (!window.confirm(t('billing.confirmDeleteDraft', 'Delete this draft invoice?'))) return
    void perform(() => billingApi.deleteDraft(shopId, invoice.id), t('billing.draftDeleted', 'Draft deleted.'))
  }

  const issue = (invoiceId: string) => void perform(() => billingApi.issue(shopId, invoiceId), t('billing.issued', 'Invoice issued.'))
  const pay = (invoiceId: string) => {
    const amount = paymentAmounts[invoiceId]?.trim()
    if (!amount) return
    void perform(() => billingApi.recordPayment(shopId, invoiceId, amount), t('billing.paymentRecorded', 'Payment recorded.'))
  }

  const makeCredit = async (invoice: Invoice) => {
    const value = creditDrafts[invoice.id] ?? { amount: '', reason: '' }
    if (!value.amount.trim() || !value.reason.trim()) return
    if (busy) return
    setBusy(true); setError(''); setNotice('')
    try {
      const note = await billingApi.createCreditNote(shopId, invoice.id, value)
      await billingApi.issueCreditNote(shopId, note.id)
      setCreditDrafts(current => ({ ...current, [invoice.id]: { amount: '', reason: '' } }))
      setNotice(t('billing.creditIssued', 'Credit note issued.'))
      await load()
    } catch (cause) { await load(); setError(errorMessage(cause)) }
    finally { setBusy(false) }
  }

  const recordRefund = (note: CreditNote) => {
    const value = refundDrafts[note.id]
    if (!value?.paymentId || !value.amount.trim()) return
    void perform(() => billingApi.recordRefund(shopId, note.id, value.paymentId, value.amount), t('billing.refundRecorded', 'Refund recorded.'))
  }

  const updateLine = (invoiceId: string, itemId: string) => {
    const value = lineDrafts[itemId]
    if (!value) return
    void perform(() => billingApi.updateLine(shopId, invoiceId, itemId, value), t('billing.lineUpdated', 'Line updated.'))
  }

  const addLine = (invoiceId: string) => {
    const value = lineDrafts[invoiceId]
    if (!value?.description.trim() || !value.unit_price.trim()) return
    void perform(() => billingApi.addLine(shopId, invoiceId, { ...value, description: value.description.trim() }), t('billing.lineAdded', 'Line added.')).then(succeeded => {
      if (succeeded) setLineDrafts(current => ({ ...current, [invoiceId]: { ...EMPTY_LINE } }))
    })
  }

  const saveAdjustments = (invoice: Invoice) => void perform(() => billingApi.setAdjustments(shopId, invoice.id, {
    discount_type: invoice.discount_type,
    discount_value: invoice.discount_type === 'NONE' ? '0' : invoice.discount_value,
    tax_rate: invoice.tax_rate,
  }), t('billing.adjustmentsSaved', 'Invoice adjustments saved.'))

  const downloadDocument = (createDocument: () => Promise<FinancialDocument>, kind: string) => void perform(async () => {
    const document = await createDocument()
    const pdf = await billingApi.downloadDocument(shopId, document.id)
    const objectUrl = URL.createObjectURL(pdf)
    const anchor = window.document.createElement('a')
    anchor.href = objectUrl
    anchor.download = `${kind.toLowerCase()}-${document.id}.pdf`
    anchor.click()
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
  }, t('billing.documentReady', 'PDF downloaded.'), false)

  if (!canManage) return null

  return <section className="orders-panel billing-panel" aria-labelledby="billing-heading">
    <div className="billing-heading"><div><h2 id="billing-heading"><FileText size={18} /> {t('billing.title', 'Billing')}</h2><p>{t('billing.subtitle', 'Invoices and payments for this Work. Billing does not change production status.')}</p></div><div className="billing-heading-actions"><label className="billing-language">{t('billing.documentLanguage', 'PDF language')}<select aria-label={t('billing.documentLanguage', 'PDF language')} value={documentLocale} onChange={event => setDocumentLocale(event.target.value as FinancialDocument['locale'])} disabled={busy}><option value="en">English</option><option value="ar-KW">العربية</option><option value="bn">বাংলা</option><option value="ur">اردو</option></select></label><button type="button" className="btn-secondary billing-refresh" aria-label={t('common.retry', 'Refresh')} onClick={() => setRetry(value => value + 1)} disabled={loading || busy}><RefreshCw size={15} />{t('common.refresh', 'Refresh')}</button></div></div>
    {!currency && <div className="billing-message" role="status"><AlertCircle size={17} />{t('billing.currencyMissing', 'Set the Shop default currency before creating prices or invoices.')}</div>}
    {error && <div className="billing-error" role="alert">{error}<button type="button" className="btn-secondary" onClick={() => setRetry(value => value + 1)}>{t('common.retry', 'Retry')}</button></div>}
    {notice && <p className="billing-notice" role="status">{notice}</p>}
    {canManage && <details className="billing-create"><summary><Plus size={16} />{t('billing.newInvoice', 'New invoice')}</summary><div className="billing-create-fields">
      <label>{t('billing.source', 'Starting lines')}<select value={mode} onChange={event => setMode(event.target.value as 'AUTO' | 'MANUAL')} disabled={busy}><option value="AUTO">{t('billing.autoLine', 'Add Design price snapshot')}</option><option value="MANUAL">{t('billing.manualOnly', 'Manual lines')}</option></select></label>
      {lines.map((line, index) => <div className="billing-line-form" key={index}><label>{t('billing.description', 'Description')}<input value={line.description} onChange={event => setLines(current => current.map((row, rowIndex) => rowIndex === index ? { ...row, description: event.target.value } : row))} maxLength={240} /></label><label>{t('billing.quantity', 'Qty')}<input type="number" min="0.001" step="0.001" value={line.quantity} onChange={event => setLines(current => current.map((row, rowIndex) => rowIndex === index ? { ...row, quantity: event.target.value } : row))} /></label><label>{t('billing.unitPrice', 'Unit price')}<input inputMode="decimal" value={line.unit_price} onChange={event => setLines(current => current.map((row, rowIndex) => rowIndex === index ? { ...row, unit_price: event.target.value } : row))} placeholder={currency ?? ''} /></label><button type="button" className="btn-secondary billing-remove-line" aria-label={t('billing.removeLine', 'Remove line')} onClick={() => setLines(current => current.length > 1 ? current.filter((_, rowIndex) => rowIndex !== index) : [{ ...EMPTY_LINE }])} disabled={busy}><Trash2 size={15} /></button></div>)}
      <button type="button" className="btn-secondary billing-add-line" onClick={() => setLines(current => [...current, { ...EMPTY_LINE }])} disabled={busy}><Plus size={15} />{t('billing.addLine', 'Add manual line')}</button>
      <div className="billing-adjustments"><label>{t('billing.discount', 'Discount')}<select value={discountType} onChange={event => setDiscountType(event.target.value as DiscountType)} disabled={busy}><option value="NONE">{t('billing.noDiscount', 'None')}</option><option value="FIXED">{t('billing.fixed', 'Fixed amount')}</option><option value="PERCENT">{t('billing.percent', 'Percent')}</option></select></label>{discountType !== 'NONE' && <label>{t('billing.discountValue', 'Discount value')}<input inputMode="decimal" value={discountValue} onChange={event => setDiscountValue(event.target.value)} /></label>}<label>{t('billing.taxRateOptional', 'Tax rate (optional)')}<input inputMode="decimal" value={taxRate} onChange={event => setTaxRate(event.target.value)} placeholder="0" /></label></div>
      <button type="button" className="btn-primary" onClick={create} disabled={busy || !currency || (mode === 'MANUAL' && !lines.some(line => line.description.trim() && line.unit_price.trim()))}>{busy ? <Loader2 size={16} className="animate-spin" /> : null}{t('billing.createDraft', 'Create draft')}</button>
    </div></details>}
    {loading ? <p className="billing-state" role="status"><Loader2 size={16} className="animate-spin" />{t('billing.loading', 'Loading invoices…')}</p> : !error && invoices.length === 0 ? <p className="billing-state">{t('billing.noInvoices', 'No invoices for this Work yet.')}</p> : <div className="billing-list">{invoices.map(invoice => <article className="billing-invoice" key={invoice.id}>
      <div className="billing-invoice-heading"><div><strong>{invoice.invoice_number ?? t('billing.draft', 'Draft invoice')}</strong><span className={`billing-status billing-status-${invoice.status.toLowerCase()}`}>{invoice.status}</span></div><span>{invoice.currency}</span></div>
      <div className="billing-totals"><span>{t('billing.subtotal', 'Subtotal')} <strong>{formatAmount(invoice.subtotal, invoice.currency)}</strong></span>{Number(invoice.discount_total) > 0 && <span>{t('billing.discount', 'Discount')} <strong>−{formatAmount(invoice.discount_total, invoice.currency)}</strong></span>}{Number(invoice.tax_total) > 0 && <span>{t('billing.tax', 'Tax')} <strong>{formatAmount(invoice.tax_total, invoice.currency)}</strong></span>}<span>{t('billing.total', 'Total')} <strong>{formatAmount(invoice.total_amount, invoice.currency)}</strong></span><span>{t('billing.paid', 'Paid')} <strong>{formatAmount(String(Number(invoice.amount_paid) - Number(invoice.amount_refunded)), invoice.currency)}</strong></span><span>{t('billing.balance', 'Balance')} <strong>{formatAmount(invoice.balance, invoice.currency)}</strong></span>{Number(invoice.refund_due) > 0 && <span>{t('billing.refundDue', 'Refund due')} <strong>{formatAmount(invoice.refund_due, invoice.currency)}</strong></span>}</div>
      <ul className="billing-lines">{invoice.items.map(item => <li key={item.id}><span>{item.description}{item.quantity !== '1.000' ? ` × ${item.quantity}` : ''}</span><strong>{formatAmount(item.line_total, invoice.currency)}</strong></li>)}</ul>
      {canManage && invoice.status === 'DRAFT' && <details className="billing-edit"><summary>{t('billing.editDraft', 'Edit draft')}</summary><div className="billing-edit-fields">
        {invoice.items.filter(item => item.source === 'MANUAL').map(item => <div className="billing-line-form" key={item.id}><label>{t('billing.description', 'Description')}<input value={lineDrafts[item.id]?.description ?? item.description} onChange={event => setLineDrafts(current => ({ ...current, [item.id]: { description: event.target.value, quantity: lineDrafts[item.id]?.quantity ?? item.quantity, unit_price: lineDrafts[item.id]?.unit_price ?? item.unit_price } }))} /></label><label>{t('billing.quantity', 'Qty')}<input type="number" min="0.001" step="0.001" value={lineDrafts[item.id]?.quantity ?? item.quantity} onChange={event => setLineDrafts(current => ({ ...current, [item.id]: { description: lineDrafts[item.id]?.description ?? item.description, quantity: event.target.value, unit_price: lineDrafts[item.id]?.unit_price ?? item.unit_price } }))} /></label><label>{t('billing.unitPrice', 'Unit price')}<input inputMode="decimal" value={lineDrafts[item.id]?.unit_price ?? item.unit_price} onChange={event => setLineDrafts(current => ({ ...current, [item.id]: { description: lineDrafts[item.id]?.description ?? item.description, quantity: lineDrafts[item.id]?.quantity ?? item.quantity, unit_price: event.target.value } }))} /></label><button type="button" className="btn-secondary" onClick={() => updateLine(invoice.id, item.id)} disabled={busy}>{t('common.save', 'Save')}</button><button type="button" className="btn-secondary" onClick={() => void perform(() => billingApi.deleteLine(shopId, invoice.id, item.id), t('billing.lineDeleted', 'Line removed.'))} disabled={busy} aria-label={t('billing.removeLine', 'Remove line')}><Trash2 size={15} /></button></div>)}
        <div className="billing-line-form"><label>{t('billing.addLine', 'Add manual line')}<input value={lineDrafts[invoice.id]?.description ?? ''} onChange={event => setLineDrafts(current => ({ ...current, [invoice.id]: { description: event.target.value, quantity: current[invoice.id]?.quantity ?? '1', unit_price: current[invoice.id]?.unit_price ?? '' } }))} /></label><label>{t('billing.quantity', 'Qty')}<input type="number" min="0.001" step="0.001" value={lineDrafts[invoice.id]?.quantity ?? '1'} onChange={event => setLineDrafts(current => ({ ...current, [invoice.id]: { description: current[invoice.id]?.description ?? '', quantity: event.target.value, unit_price: current[invoice.id]?.unit_price ?? '' } }))} /></label><label>{t('billing.unitPrice', 'Unit price')}<input inputMode="decimal" value={lineDrafts[invoice.id]?.unit_price ?? ''} onChange={event => setLineDrafts(current => ({ ...current, [invoice.id]: { description: current[invoice.id]?.description ?? '', quantity: current[invoice.id]?.quantity ?? '1', unit_price: event.target.value } }))} /></label><button type="button" className="btn-secondary" onClick={() => addLine(invoice.id)} disabled={busy || !lineDrafts[invoice.id]?.description.trim() || !lineDrafts[invoice.id]?.unit_price.trim()}><Plus size={15} />{t('billing.addLine', 'Add')}</button></div>
        <label>{t('billing.discount', 'Discount')}<select value={invoice.discount_type} onChange={event => setInvoices(current => current.map(row => row.id === invoice.id ? { ...row, discount_type: event.target.value as DiscountType } : row))}><option value="NONE">{t('billing.noDiscount', 'None')}</option><option value="FIXED">{t('billing.fixed', 'Fixed amount')}</option><option value="PERCENT">{t('billing.percent', 'Percent')}</option></select></label>{invoice.discount_type !== 'NONE' && <label>{t('billing.discountValue', 'Discount value')}<input inputMode="decimal" value={invoice.discount_value} onChange={event => setInvoices(current => current.map(row => row.id === invoice.id ? { ...row, discount_value: event.target.value } : row))} /></label>}<label>{t('billing.taxRateOptional', 'Tax rate (optional)')}<input inputMode="decimal" value={invoice.tax_rate ?? ''} onChange={event => setInvoices(current => current.map(row => row.id === invoice.id ? { ...row, tax_rate: event.target.value || null } : row))} /></label><button type="button" className="btn-secondary" onClick={() => saveAdjustments(invoice)} disabled={busy}>{t('billing.saveAdjustments', 'Save discount/tax')}</button>
      </div></details>}
      {canManage && invoice.status !== 'DRAFT' && <div className="billing-actions"><button type="button" className="btn-secondary" onClick={() => downloadDocument(() => billingApi.createInvoiceDocument(shopId, invoice.id, documentLocale), 'invoice')} disabled={busy}><FileText size={15} />{t('billing.downloadInvoice', 'Invoice PDF')}</button></div>}
      {canManage && invoice.status === 'ISSUED' && <div className="billing-actions">
        <div className="billing-action-row"><label>{t('billing.recordPayment', 'Record payment')}<input inputMode="decimal" value={paymentAmounts[invoice.id] ?? ''} onChange={event => setPaymentAmounts(current => ({ ...current, [invoice.id]: event.target.value }))} placeholder={invoice.currency} disabled={busy || Number(invoice.balance) <= 0} /></label><button type="button" className="btn-primary" onClick={() => pay(invoice.id)} disabled={busy || !paymentAmounts[invoice.id]?.trim() || Number(invoice.balance) <= 0}>{t('billing.record', 'Record')}</button></div>
        {invoice.payments.length > 0 && <div className="billing-payment-list"><h4>{t('billing.payments', 'Payments')}</h4>{invoice.payments.map(payment => <div className="billing-payment-row" key={payment.id}><span>{formatAmount(payment.amount, invoice.currency)} · {new Date(payment.received_at).toLocaleString()}</span><button type="button" className="btn-secondary" onClick={() => downloadDocument(() => billingApi.createReceiptDocument(shopId, invoice.id, payment.id, documentLocale), 'receipt')} disabled={busy}><FileText size={14} />{t('billing.receiptPdf', 'Receipt PDF')}</button></div>)}</div>}
        {Number(invoice.amount_paid) > 0 && <div className="billing-action-row"><label>{t('billing.creditAmount', 'Credit amount')}<input inputMode="decimal" value={creditDrafts[invoice.id]?.amount ?? ''} onChange={event => setCreditDrafts(current => ({ ...current, [invoice.id]: { amount: event.target.value, reason: current[invoice.id]?.reason ?? '' } }))} placeholder={invoice.currency} disabled={busy} /></label><label>{t('billing.creditReason', 'Credit reason')}<input maxLength={500} value={creditDrafts[invoice.id]?.reason ?? ''} onChange={event => setCreditDrafts(current => ({ ...current, [invoice.id]: { amount: current[invoice.id]?.amount ?? '', reason: event.target.value } }))} disabled={busy} /></label><button type="button" className="btn-secondary" onClick={() => void makeCredit(invoice)} disabled={busy || !creditDrafts[invoice.id]?.amount.trim() || !creditDrafts[invoice.id]?.reason.trim()}>{t('billing.issueCredit', 'Issue credit')}</button></div>}
        <div className="billing-action-row"><label>{t('billing.voidReason', 'Void reason')}<input maxLength={500} value={voidReasons[invoice.id] ?? ''} onChange={event => setVoidReasons(current => ({ ...current, [invoice.id]: event.target.value }))} disabled={busy || Number(invoice.amount_paid) > 0} /></label><button type="button" className="btn-secondary" onClick={() => void perform(() => billingApi.voidInvoice(shopId, invoice.id, voidReasons[invoice.id] ?? ''), t('billing.voided', 'Invoice voided.'))} disabled={busy || Number(invoice.amount_paid) > 0 || !voidReasons[invoice.id]?.trim()}>{t('billing.voidInvoice', 'Void invoice')}</button></div>
      </div>}
      {invoice.credit_notes.length > 0 && <div className="billing-credit-list"><h4>{t('billing.creditNotes', 'Credit notes')}</h4>{invoice.credit_notes.map(note => <div className="billing-credit-row" key={note.id}><span><strong>{note.credit_number ?? t('billing.draftCredit', 'Draft credit')}</strong> · {formatAmount(note.amount, invoice.currency)} · {note.reason}</span>{canManage && note.status === 'DRAFT' && <div className="billing-action-row"><button type="button" className="btn-primary" onClick={() => void perform(() => billingApi.issueCreditNote(shopId, note.id), t('billing.creditIssued', 'Credit note issued.'))} disabled={busy}>{t('billing.issueCredit', 'Issue credit')}</button><button type="button" className="btn-secondary" onClick={() => { if (window.confirm(t('billing.confirmDeleteDraftCredit', 'Delete this draft credit note?'))) void perform(() => billingApi.deleteDraftCreditNote(shopId, note.id), t('billing.draftCreditDeleted', 'Draft credit note deleted.')) }} disabled={busy}>{t('billing.deleteDraft', 'Delete draft')}</button></div>}{canManage && note.status === 'ISSUED' && <div className="billing-action-row"><button type="button" className="btn-secondary" onClick={() => downloadDocument(() => billingApi.createCreditNoteDocument(shopId, note.id, documentLocale), 'credit-note')} disabled={busy}><FileText size={14} />{t('billing.creditNotePdf', 'Credit note PDF')}</button><label>{t('billing.refundPayment', 'Refund against payment')}<select value={refundDrafts[note.id]?.paymentId ?? ''} onChange={event => setRefundDrafts(current => ({ ...current, [note.id]: { paymentId: event.target.value, amount: current[note.id]?.amount ?? '' } }))}><option value="">{t('billing.choosePayment', 'Choose payment')}</option>{invoice.payments.map(payment => <option key={payment.id} value={payment.id}>{formatAmount(payment.amount, invoice.currency)} · {new Date(payment.received_at).toLocaleDateString()}</option>)}</select></label><label>{t('billing.refundAmount', 'Refund amount')}<input inputMode="decimal" value={refundDrafts[note.id]?.amount ?? ''} onChange={event => setRefundDrafts(current => ({ ...current, [note.id]: { paymentId: current[note.id]?.paymentId ?? '', amount: event.target.value } }))} /></label><button type="button" className="btn-secondary" onClick={() => recordRefund(note)} disabled={busy || !refundDrafts[note.id]?.paymentId || !refundDrafts[note.id]?.amount.trim()}>{t('billing.recordRefund', 'Record refund')}</button></div>}</div>)}</div>}
      {canManage && invoice.status === 'DRAFT' && <div className="billing-actions"><button type="button" className="btn-primary" onClick={() => issue(invoice.id)} disabled={busy || invoice.items.length === 0}>{busy ? <Loader2 size={15} className="animate-spin" /> : null}{t('billing.issueInvoice', 'Issue invoice')}</button><button type="button" className="btn-secondary" onClick={() => removeDraft(invoice)} disabled={busy}><Trash2 size={15} />{t('billing.deleteDraft', 'Delete draft')}</button></div>}
    </article>)}</div>}
  </section>
}
