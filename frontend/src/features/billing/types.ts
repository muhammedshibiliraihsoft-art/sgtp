export type InvoiceStatus = 'DRAFT' | 'ISSUED' | 'VOID'
export type DiscountType = 'NONE' | 'FIXED' | 'PERCENT'

export interface InvoiceLine {
  id: string
  source: 'DESIGN_SNAPSHOT' | 'MANUAL'
  description: string
  quantity: string
  unit_price: string
  line_total: string
  discount_amount: string
  tax_amount: string
}

export interface InvoiceRefund {
  id: string
  payment_id: string
  credit_note_id: string
  amount: string
  refunded_at: string
  recorded_by_id: string
}

export interface InvoicePayment {
  id: string
  amount: string
  received_at: string
  recorded_by_id: string
  refunds: InvoiceRefund[]
}

export interface CreditNote {
  id: string
  invoice_id: string
  credit_number: string | null
  status: 'DRAFT' | 'ISSUED'
  reason: string
  amount: string
  issued_at: string | null
  issued_by_id: string | null
  created_at: string
}

export interface Invoice {
  id: string
  work_id: string
  client_id: string
  related_person_id: string | null
  currency: string
  status: InvoiceStatus
  invoice_number: string | null
  subtotal: string
  discount_type: DiscountType
  discount_value: string
  discount_total: string
  tax_rate: string | null
  tax_total: string
  total_amount: string
  amount_paid: string
  amount_refunded: string
  credited_total: string
  balance: string
  refund_due: string
  items: InvoiceLine[]
  payments: InvoicePayment[]
  credit_notes: CreditNote[]
  issued_at: string | null
  issued_by_id: string | null
  voided_at: string | null
  voided_by_id: string | null
  void_reason: string
  created_at: string
  updated_at: string
}

export interface InvoicePage {
  count: number
  next: string | null
  previous: string | null
  results: Invoice[]
}

export interface FinancialDocument {
  id: string
  kind: 'INVOICE' | 'RECEIPT' | 'CREDIT_NOTE'
  locale: 'en' | 'ar-KW' | 'bn' | 'ur'
  sha256: string
  generated_at: string
}

export interface ManualInvoiceLineInput {
  description: string
  quantity: string
  unit_price: string
}
