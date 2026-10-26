import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { FinancialPurgePage } from './FinancialPurgePage'
import { shopsService } from '../services/shops'
import { billingApi } from '../features/billing/api'
import type { Invoice, InvoicePage } from '../features/billing/types'

vi.mock('../services/shops', () => ({ shopsService: { list: vi.fn() } }))
vi.mock('../features/billing/api', () => ({ billingApi: { historyPage: vi.fn(), purgeInvoiceBundle: vi.fn() } }))

const shops = vi.mocked(shopsService)
const billing = vi.mocked(billingApi)
const invoice: Invoice = {
  id: 'invoice-1', work_id: 'work-1', client_id: 'client-1', related_person_id: null, currency: 'INR',
  status: 'ISSUED', invoice_number: 'INV-000001', subtotal: '100', discount_type: 'NONE', discount_value: '0',
  discount_total: '0', tax_rate: null, tax_total: '0', total_amount: '100', amount_paid: '20', amount_refunded: '0',
  credited_total: '0', balance: '80', refund_due: '0', items: [], payments: [], credit_notes: [], issued_at: '2026-10-21T00:00:00Z',
  issued_by_id: 'user-1', voided_at: null, voided_by_id: null, void_reason: '', created_at: '', updated_at: '',
}
const invoicePage = (rows: Invoice[]): InvoicePage => ({ count: rows.length, next: null, previous: null, results: rows })

describe('FinancialPurgePage', () => {
  beforeEach(() => {
    shops.list.mockResolvedValue({ count: 2, next: null, previous: null, results: [
      { id: 'shop-1', name: 'Tailor Shop', is_active: true, max_users: 20, user_count: 1, is_at_user_limit: false, default_locale: 'en', default_timezone: 'UTC', default_currency: 'INR' },
      { id: 'shop-2', name: 'Inactive Shop', is_active: false, max_users: 20, user_count: 0, is_at_user_limit: false, default_locale: 'en', default_timezone: 'UTC', default_currency: 'INR' },
    ] })
    billing.historyPage.mockResolvedValue(invoicePage([invoice]))
    billing.purgeInvoiceBundle.mockResolvedValue({ id: 'purge-1', invoice_id: 'invoice-1', invoice_number: 'INV-000001', status: 'COMPLETED', attempt_count: 1, failure_code: '', completed_at: '' })
  })
  afterEach(() => { cleanup(); vi.clearAllMocks() })

  it('selects a Shop and requires reason plus exact invoice number before purge', async () => {
    render(<FinancialPurgePage />)
    expect(await screen.findByRole('option', { name: 'Inactive Shop · Inactive' })).toBeDisabled()
    fireEvent.change(await screen.findByLabelText('Shop'), { target: { value: 'shop-1' } })
    expect(await screen.findByText('INV-000001')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Permanently delete financial bundle' }))
    const confirm = screen.getByRole('button', { name: 'Delete permanently' })
    expect(confirm).toBeDisabled()
    fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Duplicate created in error' } })
    fireEvent.change(screen.getByLabelText('Type the invoice number to confirm'), { target: { value: 'INV-000001' } })
    expect(confirm).toBeEnabled()
    fireEvent.click(confirm)
    await waitFor(() => expect(billing.purgeInvoiceBundle).toHaveBeenCalledWith('shop-1', 'invoice-1', {
      reason: 'Duplicate created in error', confirm_invoice_number: 'INV-000001',
    }))
    expect(await screen.findByText(/Audit and sequence history was retained/i)).toBeInTheDocument()
  })

  it('keeps Shop selection disabled while Shop data is loading', () => {
    shops.list.mockReturnValue(new Promise(() => undefined))
    render(<FinancialPurgePage />)
    expect(screen.getByLabelText('Shop')).toBeDisabled()
    expect(screen.getByText(/Loading Shops/i)).toBeInTheDocument()
  })

  it('retries the Shop request when Shop loading fails', async () => {
    shops.list.mockRejectedValueOnce(new Error('Shop service unavailable'))
    render(<FinancialPurgePage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Shop service unavailable')
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByRole('option', { name: 'Tailor Shop' })).toBeInTheDocument()
    expect(shops.list).toHaveBeenCalledTimes(2)
  })

  it('retries invoice history and shows its empty state', async () => {
    billing.historyPage.mockRejectedValueOnce(new Error('History service unavailable'))
      .mockResolvedValueOnce(invoicePage([]))
    render(<FinancialPurgePage />)
    fireEvent.change(await screen.findByLabelText('Shop'), { target: { value: 'shop-1' } })
    expect(await screen.findByRole('alert')).toHaveTextContent('History service unavailable')
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByText('No invoices for this Shop.')).toBeInTheDocument()
    expect(billing.historyPage).toHaveBeenCalledTimes(2)
  })

  it('does not offer permanent purge for a draft invoice', async () => {
    billing.historyPage.mockResolvedValue(invoicePage([{ ...invoice, status: 'DRAFT', invoice_number: null }]))
    render(<FinancialPurgePage />)
    fireEvent.change(await screen.findByLabelText('Shop'), { target: { value: 'shop-1' } })
    expect(await screen.findByText('Draft invoice')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Permanently delete financial bundle' })).not.toBeInTheDocument()
  })

  it('shows invoices loading while the selected Shop history request is pending', async () => {
    let finishHistory!: (page: InvoicePage) => void
    billing.historyPage.mockReturnValue(new Promise(resolve => { finishHistory = resolve }))
    render(<FinancialPurgePage />)
    fireEvent.change(await screen.findByLabelText('Shop'), { target: { value: 'shop-1' } })
    expect(screen.getByRole('status')).toHaveTextContent('Loading invoices')
    finishHistory(invoicePage([]))
    expect(await screen.findByText('No invoices for this Shop.')).toBeInTheDocument()
  })

  it('keeps database records protected after storage failure and retries the purge', async () => {
    billing.purgeInvoiceBundle.mockResolvedValueOnce({ id: 'purge-1', invoice_id: 'invoice-1', invoice_number: 'INV-000001', status: 'FAILED', attempt_count: 1, failure_code: 'PRIVATE_FILE_DELETE_FAILED', completed_at: '' })
      .mockResolvedValueOnce({ id: 'purge-1', invoice_id: 'invoice-1', invoice_number: 'INV-000001', status: 'COMPLETED', attempt_count: 2, failure_code: '', completed_at: '' })
    render(<FinancialPurgePage />)
    fireEvent.change(await screen.findByLabelText('Shop'), { target: { value: 'shop-1' } })
    await screen.findByText('INV-000001')
    fireEvent.click(screen.getByRole('button', { name: 'Permanently delete financial bundle' }))
    fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Synthetic storage retry test' } })
    fireEvent.change(screen.getByLabelText('Type the invoice number to confirm'), { target: { value: 'INV-000001' } })
    fireEvent.click(screen.getByRole('button', { name: 'Delete permanently' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Private PDF cleanup is incomplete')
    expect(billing.historyPage).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByText(/Audit and sequence history was retained/i)).toBeInTheDocument()
    expect(billing.purgeInvoiceBundle).toHaveBeenCalledTimes(2)
  })

  it('retries a failed purge instead of only reloading history', async () => {
    billing.purgeInvoiceBundle.mockRejectedValueOnce(new Error('Temporary storage failure'))
    render(<FinancialPurgePage />)
    fireEvent.change(await screen.findByLabelText('Shop'), { target: { value: 'shop-1' } })
    await screen.findByText('INV-000001')
    fireEvent.click(screen.getByRole('button', { name: 'Permanently delete financial bundle' }))
    fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Synthetic retry test' } })
    fireEvent.change(screen.getByLabelText('Type the invoice number to confirm'), { target: { value: 'INV-000001' } })
    fireEvent.click(screen.getByRole('button', { name: 'Delete permanently' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Temporary storage failure')
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByText(/Audit and sequence history was retained/i)).toBeInTheDocument()
    expect(billing.purgeInvoiceBundle).toHaveBeenCalledTimes(2)
  })
})
