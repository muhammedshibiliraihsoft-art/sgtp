import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { cleanup, render, waitFor } from '@testing-library/react'
import { fireEvent, screen } from '@testing-library/dom'
import { BrowserRouter } from 'react-router-dom'
import { vi } from 'vitest'
import App from './App'
import i18n from './i18n'
import { authService } from './services/auth'

async function renderApp(path = '/') {
  window.history.replaceState({}, '', path)
  const result = render(<BrowserRouter><App /></BrowserRouter>)
  await waitFor(() => expect(screen.queryByText('Loading your session…')).not.toBeInTheDocument())
  return result
}

describe('foundation shell', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    localStorage.clear()
    vi.spyOn(authService, 'restore').mockResolvedValue({
      user: { id: 'u1', user_code: 'USER-1', email: null, first_name: 'Test', last_name: '', is_active: true, date_joined: '', phone: null, preferred_locale: 'en', appearance_preference: 'system', must_change_password: false, is_main_supplier_admin: false },
      passwordChangeRequired: false,
    })
  })
  afterEach(() => { cleanup(); vi.restoreAllMocks() })

  it('renders a preview shell without claiming live business data', async () => {
    await renderApp()
    expect(screen.getByText('Modern Tailors')).toBeInTheDocument()
    expect(screen.getAllByText(/Dashboard/i)[0]).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /shop selector|switch shop/i })).not.toBeInTheDocument()
  })

  it('provides an identifier-and-password sign-in shell without public signup', async () => {
    vi.spyOn(authService, 'restore').mockResolvedValue(null)
    const loginSpy = vi.spyOn(authService, 'login').mockResolvedValue({
      user: { id: 'u1', user_code: 'USER-1', email: null, first_name: 'Test', last_name: '', is_active: true, date_joined: '', phone: null, preferred_locale: 'en', appearance_preference: 'system', must_change_password: false, is_main_supplier_admin: false },
      passwordChangeRequired: false,
    })
    await renderApp('/login')
    expect(screen.getByLabelText('User ID, Email, or Phone')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()

    expect(screen.queryByText(/sign up|create account/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/apple|google/i)).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/remember/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/continue/i, { selector: 'button' })).not.toBeInTheDocument()

    const submitBtn = screen.getByRole('button', { name: /log in/i })
    expect(submitBtn).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('User ID, Email, or Phone'), { target: { value: 'testuser' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'testpass' } })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(loginSpy).toHaveBeenCalledWith({ identifier: 'testuser', password: 'testpass' })
    })

  })

  it('routes generated-credential accounts to the password change gate', async () => {
    vi.spyOn(authService, 'restore').mockResolvedValue(null)
    vi.spyOn(authService, 'login').mockResolvedValue({ user: null, passwordChangeRequired: true })
    await renderApp('/login')
    fireEvent.change(screen.getByLabelText('User ID, Email, or Phone'), { target: { value: 'TEMP-1' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'initial-pass' } })
    fireEvent.click(screen.getByRole('button', { name: /log in/i }))
    expect(await screen.findByRole('heading', { name: 'Change your password' })).toBeInTheDocument()
    expect(screen.getByLabelText('Current password')).toBeInTheDocument()
  })

  it('changes document direction when an RTL locale is selected', async () => {
    await renderApp()
    fireEvent.click(screen.getByLabelText('Language'))
    fireEvent.click(screen.getByText('العربية'))
    await waitFor(() => expect(screen.getAllByText(/لوحة القيادة/i).length).toBeGreaterThan(0))
    expect(document.documentElement.dir).toBe('rtl')
    await i18n.changeLanguage('bn')
    expect(i18n.dir()).toBe('ltr')
  })

  it('supports explicit light, dark and system theme preferences', async () => {
    await renderApp()
    fireEvent.click(screen.getByLabelText('Color theme'))
    fireEvent.click(screen.getByText('Dark'))
    await waitFor(() => expect(localStorage.getItem('sgtp-theme')).toBe('dark'))
    fireEvent.click(screen.getByLabelText('Color theme'))
    fireEvent.click(screen.getByText('System'))
    await waitFor(() => expect(localStorage.getItem('sgtp-theme')).toBe('system'))
  })

  it('displays exactly 2 visible Work records per stage on the Work page', async () => {
    await renderApp('/work')
    // Since there are 4 stages and each shows 2 records, there should be 8 visible work-cards
    const cards = screen.getAllByText(/#ORD-/i)
    expect(cards.length).toBe(8)
  })

  it('renders accessible N-more buttons with correct remaining count', async () => {
    await renderApp('/work')
    // Cutting total = 8, visible = 2, remaining = 6
    const btn = screen.getByRole('button', { name: 'Show 6 more Cutting records' })
    expect(btn).toBeInTheDocument()
  })

  it('renders a mobile work-stage selector with correct accessible names', async () => {
    await renderApp('/work')
    expect(screen.getByRole('button', { name: /Cutting, 8 items/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Stitching, 7 items/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Finishing, 5 items/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Ready, 4 items/i })).toBeInTheDocument()
  })
})
