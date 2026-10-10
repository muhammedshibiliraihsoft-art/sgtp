import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { PinResetRequestsPage } from './PinResetRequestsPage'
import { pinResetService } from '../services/pinReset'
import '../i18n'

const row = { id: 'r1', shop: 'Demo Shop', shop_id: 's1', name: 'Shop Admin', login_id: 'shop_admin', phone: '+96550000102', requested_at: '2026-10-08T00:00:00Z', status: 'PENDING' }

afterEach(() => { cleanup(); vi.restoreAllMocks() })

describe('Back Office PIN reset requests', () => {
  it('shows pending requests and a one-time approval result', async () => {
    vi.spyOn(pinResetService, 'pending').mockResolvedValue([row])
    const approve = vi.spyOn(pinResetService, 'approve').mockResolvedValue({ id: 'r1', status: 'APPROVED', login_id: 'shop_admin', temporary_password: '048731' })
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<BrowserRouter><PinResetRequestsPage /></BrowserRouter>)
    expect(await screen.findByText('Shop Admin')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Approve' }))
    await waitFor(() => expect(approve).toHaveBeenCalledWith('r1'))
    expect(await screen.findByText('048731')).toBeInTheDocument()
    expect(localStorage.getItem('temporary_password')).toBeNull()
    expect(sessionStorage.getItem('temporary_password')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'I have saved the PIN' }))
    expect(screen.queryByText('048731')).not.toBeInTheDocument()
  })

  it('rejects without generating a PIN', async () => {
    vi.spyOn(pinResetService, 'pending').mockResolvedValue([row])
    const reject = vi.spyOn(pinResetService, 'reject').mockResolvedValue({ id: 'r1', status: 'REJECTED' })
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<BrowserRouter><PinResetRequestsPage /></BrowserRouter>)
    await screen.findByText('Shop Admin')
    fireEvent.click(screen.getByRole('button', { name: 'Reject' }))
    await waitFor(() => expect(reject).toHaveBeenCalledWith('r1'))
    expect(screen.queryByText('Temporary PIN issued')).not.toBeInTheDocument()
  })

  it('shows a clear empty state when there are no pending requests', async () => {
    vi.spyOn(pinResetService, 'pending').mockResolvedValue([])
    render(<BrowserRouter><PinResetRequestsPage /></BrowserRouter>)
    expect(await screen.findByText('No pending recovery requests.')).toBeInTheDocument()
  })
})
