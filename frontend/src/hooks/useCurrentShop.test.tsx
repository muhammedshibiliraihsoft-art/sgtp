import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { useState } from 'react'
import { CurrentShopProvider, useCurrentShop } from './useCurrentShop'

const mock = vi.hoisted(() => ({
  user: { id: 'user-1', is_main_supplier_admin: false } as { id: string; is_main_supplier_admin: boolean } | null,
  list: vi.fn(),
  context: vi.fn(),
}))

vi.mock('../services/useAuth', () => ({ useAuth: () => ({ user: mock.user }) }))
vi.mock('../services/shops', () => ({ shopsService: { list: mock.list, context: mock.context } }))

function ShopPage() {
  const { shop, role, isLoading } = useCurrentShop()
  return <p>{isLoading ? 'Loading' : `${shop?.id ?? 'none'}:${role ?? 'none'}:${shop?.default_currency ?? 'no-currency'}`}</p>
}

function Shell() {
  const [show, setShow] = useState(true)
  return <CurrentShopProvider>
    <button onClick={() => setShow(value => !value)}>Toggle route</button>
    {show && <ShopPage />}
  </CurrentShopProvider>
}

describe('shared Shop context', () => {
  afterEach(() => { cleanup(); vi.clearAllMocks(); mock.user = { id: 'user-1', is_main_supplier_admin: false } })

  it('keeps one authoritative context load across Shop page navigation', async () => {
    mock.list.mockResolvedValue({ results: [{ id: 'shop-1', is_active: true }] })
    mock.context.mockResolvedValue({ role: 'ADMIN', work_functions: ['MEASUREMENT'], billing_currency: 'KWD' })
    render(<Shell />)
    expect(await screen.findByText('shop-1:ADMIN:KWD')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Toggle route' }))
    fireEvent.click(screen.getByRole('button', { name: 'Toggle route' }))
    expect(screen.getByText('shop-1:ADMIN:KWD')).toBeInTheDocument()
    expect(mock.list).toHaveBeenCalledTimes(1)
    expect(mock.context).toHaveBeenCalledTimes(1)
  })

  it('uses finance-only currency for CASHIER staff and hides it from other staff', async () => {
    mock.list.mockResolvedValue({ results: [{ id: 'shop-1', is_active: true }] })
    mock.context.mockResolvedValue({ role: 'STAFF', work_functions: ['CASHIER'], billing_currency: 'USD' })
    const cashier = render(<CurrentShopProvider><ShopPage /></CurrentShopProvider>)
    expect(await screen.findByText('shop-1:STAFF:USD')).toBeInTheDocument()
    cashier.unmount()

    vi.clearAllMocks()
    mock.list.mockResolvedValue({ results: [{ id: 'shop-1', is_active: true }] })
    mock.context.mockResolvedValue({ role: 'STAFF', work_functions: ['MEASUREMENT'] })
    render(<CurrentShopProvider><ShopPage /></CurrentShopProvider>)
    expect(await screen.findByText('shop-1:STAFF:no-currency')).toBeInTheDocument()
  })

  it('does not fetch Shop membership for Main Supplier', async () => {
    mock.user = { id: 'supplier-1', is_main_supplier_admin: true }
    render(<CurrentShopProvider><ShopPage /></CurrentShopProvider>)
    await waitFor(() => expect(screen.getByText('none:none:no-currency')).toBeInTheDocument())
    expect(mock.list).not.toHaveBeenCalled()
    expect(mock.context).not.toHaveBeenCalled()
  })
})
