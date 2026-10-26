import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { BillingPanel } from './BillingPanel'
import { BillingHistoryPage } from './BillingHistoryPage'
import { billingApi } from './api'
import i18n from '../../i18n'

const context = vi.hoisted(() => ({ shopId: 'shop-1', role: 'ADMIN' as 'ADMIN' | 'STAFF' | 'VIEWER', workFunctions: ['CASHIER'], isLoading: false }))
vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => context }))
vi.mock('./api', () => ({ billingApi: { listForWork: vi.fn(), createDraft: vi.fn(), issue: vi.fn(), recordPayment: vi.fn(), historyPage: vi.fn(), outstandingPage: vi.fn(), createInvoiceDocument: vi.fn(), createReceiptDocument: vi.fn(), createCreditNoteDocument: vi.fn(), downloadDocument: vi.fn() } }))

const api = vi.mocked(billingApi)

const draftInvoice = {
  id: 'invoice-1', work_id: 'work-1', client_id: 'client-1', related_person_id: null,
  currency: 'INR', status: 'DRAFT' as const, invoice_number: null,
  subtotal: '100.00', discount_type: 'NONE' as const, discount_value: '0', discount_total: '0', tax_rate: null,
  tax_total: '0', total_amount: '100.00', amount_paid: '0', amount_refunded: '0', credited_total: '0', balance: '100.00', refund_due: '0',
  items: [{ id: 'line-1', source: 'MANUAL' as const, description: 'Stitching', quantity: '1.000', unit_price: '100.00', line_total: '100.00', discount_amount: '0', tax_amount: '0' }],
  payments: [], credit_notes: [], issued_at: null, issued_by_id: null, voided_at: null, voided_by_id: null, void_reason: '', created_at: '', updated_at: '',
}

describe('BillingPanel', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    api.listForWork.mockResolvedValue([])
    api.createDraft.mockResolvedValue(draftInvoice)
    api.issue.mockResolvedValue(draftInvoice)
    api.recordPayment.mockResolvedValue({})
    api.historyPage.mockResolvedValue({ count: 1, next: null, previous: null, results: [draftInvoice] })
    api.outstandingPage.mockResolvedValue({ count: 0, next: null, previous: null, results: [] })
    api.createInvoiceDocument.mockResolvedValue({ id: 'doc-1', kind: 'INVOICE', locale: 'en', sha256: 'hash', generated_at: '' })
    api.createReceiptDocument.mockResolvedValue({ id: 'doc-2', kind: 'RECEIPT', locale: 'en', sha256: 'hash', generated_at: '' })
    api.createCreditNoteDocument.mockResolvedValue({ id: 'doc-3', kind: 'CREDIT_NOTE', locale: 'en', sha256: 'hash', generated_at: '' })
    api.downloadDocument.mockResolvedValue(new Blob(['%PDF-1.4'], { type: 'application/pdf' }))
    context.role = 'ADMIN'; context.workFunctions = ['CASHIER']
  })
  afterEach(() => { cleanup(); vi.clearAllMocks() })

  it('creates a manual draft and renders invoices for the Work', async () => {
    api.listForWork.mockResolvedValueOnce([]).mockResolvedValueOnce([draftInvoice])
    api.createDraft.mockResolvedValueOnce(draftInvoice)
    render(<BillingPanel shopId="shop-1" workId="work-1" currency="INR" canManage />)

    fireEvent.click(await screen.findByText('New invoice'))
    fireEvent.change(screen.getByLabelText('Starting lines'), { target: { value: 'MANUAL' } })
    fireEvent.change(screen.getAllByLabelText('Description')[0], { target: { value: 'Stitching' } })
    fireEvent.change(screen.getAllByLabelText('Unit price')[0], { target: { value: '100.00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create draft' }))

    await waitFor(() => expect(api.createDraft).toHaveBeenCalledWith('shop-1', 'work-1', expect.objectContaining({ mode: 'MANUAL', lines: [expect.objectContaining({ description: 'Stitching', unit_price: '100.00' })] })))
    expect(await screen.findByText('Draft invoice')).toBeInTheDocument()
    expect(screen.getByText('Stitching')).toBeInTheDocument()
  })

  it('does not fetch or render finance data for non-finance users', () => {
    const { container } = render(<BillingPanel shopId="shop-1" workId="work-1" currency="INR" canManage={false} />)
    expect(container).toBeEmptyDOMElement()
    expect(api.listForWork).not.toHaveBeenCalled()
  })

  it('creates and downloads a Shop-scoped invoice PDF using the selected document language', async () => {
    const issued = { ...draftInvoice, status: 'ISSUED' as const, invoice_number: 'INV-000001', issued_at: '2026-10-21T00:00:00Z' }
    api.listForWork.mockResolvedValueOnce([issued])
    const createUrl = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:financial-document')
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined)
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined)
    render(<BillingPanel shopId="shop-1" workId="work-1" currency="INR" canManage />)

    fireEvent.change(await screen.findByLabelText('PDF language'), { target: { value: 'bn' } })
    fireEvent.click(screen.getByRole('button', { name: 'Invoice PDF' }))

    await waitFor(() => expect(api.createInvoiceDocument).toHaveBeenCalledWith('shop-1', 'invoice-1', 'bn'))
    expect(api.downloadDocument).toHaveBeenCalledWith('shop-1', 'doc-1')
    expect(createUrl).toHaveBeenCalled()
    expect(click).toHaveBeenCalled()
  })

  it('shows Shop invoice history and applies the selected date filter', async () => {
    render(<MemoryRouter><BillingHistoryPage /></MemoryRouter>)
    expect(await screen.findByText(/Stitching/)).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Issued from'), { target: { value: '2026-10-01' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }))
    await waitFor(() => expect(api.historyPage).toHaveBeenLastCalledWith('shop-1', 1, { status: '', from: '2026-10-01', to: '' }))
    expect(screen.getByRole('link', { name: 'Open Work' })).toHaveAttribute('href', '/orders/work-1')
  })

  it('does not load Shop financial history for a Viewer', async () => {
    context.role = 'VIEWER'; context.workFunctions = []
    render(<MemoryRouter><BillingHistoryPage /></MemoryRouter>)
    expect(await screen.findByText('Shop ADMIN or CASHIER staff access is required.')).toBeInTheDocument()
    expect(api.historyPage).not.toHaveBeenCalled()
  })

})
