import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import App from '../App'
import i18n from '../i18n'
import { authService } from '../services/auth'
import { ApiError } from '../services/apiClient'
import { shopsService } from '../services/shops'
import type { ShopDetail } from '../services/shops'

const mainUser = {
  id: 'main-1', user_code: 'U-MAIN', email: 'main@example.test', first_name: 'Main', last_name: 'Supplier',
  is_active: true, date_joined: '', phone: '+96550000001', preferred_locale: 'en' as const,
  appearance_preference: 'system' as const, must_change_password: false, is_main_supplier_admin: true,
}

const shop: ShopDetail = {
  id: 'shop-1', name: 'Demo Shop', slug: 'demo-shop', is_active: true, max_users: 5, user_count: 1,
  is_at_user_limit: false, default_locale: 'en', default_timezone: 'Asia/Kolkata', default_currency: 'INR',
  domain: null, contact_email: '', contact_phone: '', address_line1: '', address_line2: '', city: '', state: '',
  postal_code: '', country: '', created_at: '2026-10-01T00:00:00Z', updated_at: '2026-10-01T00:00:00Z',
}

async function open(path: string) {
  window.history.replaceState({}, '', path)
  render(<BrowserRouter><App /></BrowserRouter>)
  await waitFor(() => expect(screen.queryByText('Loading your session…')).not.toBeInTheDocument())
}

describe('Main Supplier Back Office', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    localStorage.clear()
    vi.spyOn(authService, 'restore').mockResolvedValue({ user: mainUser, passwordChangeRequired: false })
  })
  afterEach(() => { cleanup(); vi.restoreAllMocks() })

  it('blocks ordinary Shop accounts from Back Office routes', async () => {
    vi.spyOn(authService, 'restore').mockResolvedValue({ user: { ...mainUser, is_main_supplier_admin: false }, passwordChangeRequired: false })
    const list = vi.spyOn(shopsService, 'list')
    await open('/backoffice/shops')
    await waitFor(() => expect(window.location.pathname).toBe('/'))
    expect(list).not.toHaveBeenCalled()
    expect(screen.queryByRole('heading', { name: 'Shops' })).not.toBeInTheDocument()
  })

  it('shows the Back Office shell and loads real Shop list results', async () => {
    vi.spyOn(shopsService, 'list').mockResolvedValue({ count: 1, next: null, previous: null, results: [shop] })
    await open('/backoffice/shops')
    expect(await screen.findByRole('heading', { name: 'Shops' })).toBeInTheDocument()
    expect(screen.getAllByText('Demo Shop').length).toBeGreaterThan(0)
    expect(screen.queryByText('Modern Tailors')).not.toBeInTheDocument()
  })

  it('creates a Shop with required backend fields and keeps one-time credentials in component memory', async () => {
    const create = vi.spyOn(shopsService, 'create').mockResolvedValue({
      ...shop, first_admin_user_code: 'U-FIRSTADMIN', initial_password: 'temporary-secret',
    })
    vi.spyOn(shopsService, 'detail').mockResolvedValue(shop)
    await open('/backoffice/shops/new')
    fireEvent.change(screen.getByLabelText(/Shop name/), { target: { value: 'Demo Shop' } })
    fireEvent.change(screen.getByLabelText(/Slug/), { target: { value: 'demo-shop' } })
    fireEvent.change(screen.getByLabelText(/Maximum users/), { target: { value: '5' } })
    fireEvent.change(screen.getByLabelText(/First name/), { target: { value: 'First' } })
    fireEvent.change(screen.getByLabelText(/^Email/), { target: { value: 'first@example.test' } })
    fireEvent.change(screen.getAllByLabelText(/^Phone/)[1], { target: { value: '+919000000000' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create Shop' }))
    await waitFor(() => expect(create).toHaveBeenCalledWith(expect.objectContaining({
      name: 'Demo Shop', slug: 'demo-shop', max_users: 5,
      first_admin: expect.objectContaining({ first_name: 'First', email: 'first@example.test', phone: '+919000000000' }),
    })))
    expect(await screen.findByText('U-FIRSTADMIN')).toBeInTheDocument()
    expect(screen.queryByText('temporary-secret')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Show' }))
    expect(screen.getByText('temporary-secret')).toBeInTheDocument()
    const storedValues = (storage: Storage) => Array.from({ length: storage.length }, (_, index) => storage.getItem(storage.key(index) || ''))
    expect(storedValues(localStorage).join(' ')).not.toContain('temporary-secret')
    expect(storedValues(sessionStorage).join(' ')).not.toContain('temporary-secret')
    fireEvent.click(screen.getByRole('button', { name: /Done · Open Shop/ }))
    await waitFor(() => expect(window.location.pathname).toBe('/backoffice/shops/shop-1'))
    expect(screen.queryByText('temporary-secret')).not.toBeInTheDocument()
  })

  it('shows nested backend validation errors by field', async () => {
    vi.spyOn(shopsService, 'create').mockRejectedValue(new ApiError('Invalid input', 400, undefined, {
      errors: { first_admin: { email: ['This email is already assigned.'] } },
    }))
    await open('/backoffice/shops/new')
    fireEvent.change(screen.getByLabelText(/Shop name/), { target: { value: 'Demo Shop' } })
    fireEvent.change(screen.getByLabelText(/Slug/), { target: { value: 'demo-shop' } })
    fireEvent.change(screen.getByLabelText(/First name/), { target: { value: 'First' } })
    fireEvent.change(screen.getByLabelText(/^Email/), { target: { value: 'first@example.test' } })
    fireEvent.change(screen.getAllByLabelText(/^Phone/)[1], { target: { value: '+919000000000' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create Shop' }))
    expect(await screen.findByText('This email is already assigned.')).toBeInTheDocument()
  })

  it('confirms lifecycle changes and still supports logout', async () => {
    const detail = vi.spyOn(shopsService, 'detail').mockResolvedValueOnce(shop).mockResolvedValueOnce({ ...shop, is_active: false })
    const setActive = vi.spyOn(shopsService, 'setActive').mockResolvedValue({ status: 'Shop deactivated', is_active: false })
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const logout = vi.spyOn(authService, 'logout').mockResolvedValue()
    await open('/backoffice/shops/shop-1')
    fireEvent.click(await screen.findByRole('button', { name: 'Deactivate Shop' }))
    await waitFor(() => expect(setActive).toHaveBeenCalledWith('shop-1', false))
    expect(detail).toHaveBeenCalledTimes(2)
    expect(await screen.findByText('Inactive')).toBeInTheDocument()
    fireEvent.click(screen.getAllByRole('button', { name: 'Sign out' })[0])
    await waitFor(() => expect(logout).toHaveBeenCalled())
  })
})
