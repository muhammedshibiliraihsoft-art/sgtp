import { apiRequest, binaryRequest } from '../../services/apiClient'
import type { CreditNote, DiscountType, FinancialDocument, Invoice, InvoicePage, ManualInvoiceLineInput } from './types'

const retries = new Map<string, string>()
const shopPath = (shopId: string) => `/api/v1/shops/${encodeURIComponent(shopId)}`
const invoicePath = (shopId: string, invoiceId: string) => `${shopPath(shopId)}/invoices/${encodeURIComponent(invoiceId)}/`

async function write<T>(path: string, method: string, body?: unknown): Promise<T> {
  const fingerprint = JSON.stringify([path, method, body ?? null])
  const key = retries.get(fingerprint) ?? crypto.randomUUID()
  retries.set(fingerprint, key)
  try {
    const response = await apiRequest<T>(path, {
      method,
      headers: { 'Idempotency-Key': key },
      ...(body === undefined ? {} : { body }),
    })
    retries.delete(fingerprint)
    return response
  } catch (error) {
    throw error
  }
}

async function allPages(path: string): Promise<Invoice[]> {
  const rows: Invoice[] = []
  let page = 1
  while (true) {
    const separator = path.includes('?') ? '&' : '?'
    const response = await apiRequest<InvoicePage>(`${path}${separator}page=${page}`)
    rows.push(...response.results)
    if (!response.next) return rows
    page += 1
  }
}

export const billingApi = {
  listForWork(shopId: string, workId: string) {
    return allPages(`${shopPath(shopId)}/works/${encodeURIComponent(workId)}/invoices/`)
  },
  history(shopId: string, options: { status?: string; from?: string; to?: string } = {}) {
    const query = new URLSearchParams()
    if (options.status) query.set('status', options.status)
    if (options.from) query.set('from', options.from)
    if (options.to) query.set('to', options.to)
    return allPages(`${shopPath(shopId)}/billing/invoices/${query.size ? `?${query}` : ''}`)
  },
  historyPage(shopId: string, page: number, options: { status?: string; from?: string; to?: string } = {}) {
    const query = new URLSearchParams({ page: String(page) })
    if (options.status) query.set('status', options.status)
    if (options.from) query.set('from', options.from)
    if (options.to) query.set('to', options.to)
    return apiRequest<InvoicePage>(`${shopPath(shopId)}/billing/invoices/?${query}`)
  },
  outstanding(shopId: string) {
    return allPages(`${shopPath(shopId)}/billing/outstanding/`)
  },
  outstandingPage(shopId: string, page: number) {
    return apiRequest<InvoicePage>(`${shopPath(shopId)}/billing/outstanding/?page=${page}`)
  },
  createInvoiceDocument(shopId: string, invoiceId: string, locale: FinancialDocument['locale']) {
    return apiRequest<FinancialDocument>(`${invoicePath(shopId, invoiceId)}documents/`, { method: 'POST', body: { locale } })
  },
  createReceiptDocument(shopId: string, invoiceId: string, paymentId: string, locale: FinancialDocument['locale']) {
    return apiRequest<FinancialDocument>(`${invoicePath(shopId, invoiceId)}payments/${encodeURIComponent(paymentId)}/receipt/`, { method: 'POST', body: { locale } })
  },
  createCreditNoteDocument(shopId: string, creditNoteId: string, locale: FinancialDocument['locale']) {
    return apiRequest<FinancialDocument>(`${shopPath(shopId)}/credit-notes/${encodeURIComponent(creditNoteId)}/documents/`, { method: 'POST', body: { locale } })
  },
  downloadDocument(shopId: string, documentId: string) {
    return binaryRequest(`${shopPath(shopId)}/financial-documents/${encodeURIComponent(documentId)}/download/`)
  },
  createDraft(shopId: string, workId: string, input: { mode: 'AUTO' | 'MANUAL'; lines: ManualInvoiceLineInput[]; discount_type: DiscountType; discount_value: string; tax_rate: string | null }) {
    return write<Invoice>(`${shopPath(shopId)}/works/${encodeURIComponent(workId)}/invoices/`, 'POST', input)
  },
  addLine(shopId: string, invoiceId: string, input: ManualInvoiceLineInput) {
    return write<unknown>(`${invoicePath(shopId, invoiceId)}items/`, 'POST', input)
  },
  updateLine(shopId: string, invoiceId: string, lineId: string, input: Partial<ManualInvoiceLineInput>) {
    return write<unknown>(`${invoicePath(shopId, invoiceId)}items/${encodeURIComponent(lineId)}/`, 'PATCH', input)
  },
  deleteLine(shopId: string, invoiceId: string, lineId: string) {
    return write<void>(`${invoicePath(shopId, invoiceId)}items/${encodeURIComponent(lineId)}/`, 'DELETE')
  },
  setAdjustments(shopId: string, invoiceId: string, input: { discount_type: DiscountType; discount_value: string; tax_rate: string | null }) {
    return write<Invoice>(`${invoicePath(shopId, invoiceId)}adjustments/`, 'PATCH', input)
  },
  issue(shopId: string, invoiceId: string) {
    return write<Invoice>(`${invoicePath(shopId, invoiceId)}issue/`, 'POST', {})
  },
  recordPayment(shopId: string, invoiceId: string, amount: string) {
    return write<unknown>(`${invoicePath(shopId, invoiceId)}payments/`, 'POST', { amount })
  },
  voidInvoice(shopId: string, invoiceId: string, reason: string) {
    return write<Invoice>(`${invoicePath(shopId, invoiceId)}void/`, 'POST', { reason })
  },
  deleteDraft(shopId: string, invoiceId: string) {
    return write<void>(invoicePath(shopId, invoiceId), 'DELETE')
  },
  purgeInvoiceBundle(shopId: string, invoiceId: string, input: { reason: string; confirm_invoice_number: string }) {
    return write<{ id: string; invoice_id: string; invoice_number: string; status: 'PENDING' | 'FAILED' | 'COMPLETED'; attempt_count: number; failure_code: string; completed_at: string | null }>(`${invoicePath(shopId, invoiceId)}purge/`, 'POST', input)
  },
  createCreditNote(shopId: string, invoiceId: string, input: { amount: string; reason: string }) {
    return write<CreditNote>(`${invoicePath(shopId, invoiceId)}credit-notes/`, 'POST', input)
  },
  issueCreditNote(shopId: string, creditNoteId: string) {
    return write<CreditNote>(`${shopPath(shopId)}/credit-notes/${encodeURIComponent(creditNoteId)}/issue/`, 'POST', {})
  },
  deleteDraftCreditNote(shopId: string, creditNoteId: string) {
    return write<void>(`${shopPath(shopId)}/credit-notes/${encodeURIComponent(creditNoteId)}/`, 'DELETE')
  },
  recordRefund(shopId: string, creditNoteId: string, paymentId: string, amount: string) {
    return write<unknown>(`${shopPath(shopId)}/credit-notes/${encodeURIComponent(creditNoteId)}/refunds/`, 'POST', { payment_id: paymentId, amount })
  },
  getDesignPrice(shopId: string, designId: string) {
    return apiRequest<{ design_id: string; amount: string; currency: string; updated_at: string }>(`${shopPath(shopId)}/design-prices/${encodeURIComponent(designId)}/`)
  },
  setDesignPrice(shopId: string, designId: string, amount: string) {
    return write<{ design_id: string; amount: string; currency: string; updated_at: string }>(`${shopPath(shopId)}/design-prices/${encodeURIComponent(designId)}/`, 'PUT', { amount })
  },
}
