import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { cleanup, render, waitFor } from '@testing-library/react'
import { fireEvent, screen } from '@testing-library/dom'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import i18n from './i18n'

function renderApp(path = '/') {
  window.history.replaceState({}, '', path)
  return render(<BrowserRouter><App /></BrowserRouter>)
}

describe('foundation shell', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    localStorage.clear()
  })
  afterEach(() => cleanup())

  it('renders a preview shell without claiming live business data', () => {
    renderApp()
    expect(screen.getByText('Modern Tailors')).toBeInTheDocument()
    expect(screen.getAllByText(/Dashboard/i)[0]).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /shop selector|switch shop/i })).not.toBeInTheDocument()
  })

  it('provides an identifier-and-password sign-in shell without public signup', () => {
    renderApp('/login')
    expect(screen.getByLabelText('Email or phone')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.queryByText(/sign up|create account/i)).not.toBeInTheDocument()
  })

  it('changes document direction when an RTL locale is selected', async () => {
    renderApp()
    fireEvent.click(screen.getByLabelText('Language'))
    fireEvent.click(screen.getByText('العربية'))
    await waitFor(() => expect(screen.getAllByText(/لوحة القيادة/i).length).toBeGreaterThan(0))
    expect(document.documentElement.dir).toBe('rtl')
    await i18n.changeLanguage('bn')
    expect(i18n.dir()).toBe('ltr')
  })

  it('supports explicit light, dark and system theme preferences', async () => {
    renderApp()
    fireEvent.click(screen.getByLabelText('Color theme'))
    fireEvent.click(screen.getByText('Dark'))
    await waitFor(() => expect(localStorage.getItem('sgtp-theme')).toBe('dark'))
    fireEvent.click(screen.getByLabelText('Color theme'))
    fireEvent.click(screen.getByText('System'))
    await waitFor(() => expect(localStorage.getItem('sgtp-theme')).toBe('system'))
  })

  it('displays exactly 2 visible Work records per stage on the Work page', () => {
    renderApp('/work')
    // Since there are 4 stages and each shows 2 records, there should be 8 visible work-cards
    const cards = screen.getAllByText(/#ORD-/i)
    expect(cards.length).toBe(8)
  })

  it('renders accessible N-more buttons with correct remaining count', () => {
    renderApp('/work')
    // Cutting total = 8, visible = 2, remaining = 6
    const btn = screen.getByRole('button', { name: 'Show 6 more Cutting records' })
    expect(btn).toBeInTheDocument()
  })

  it('renders a mobile work-stage selector with correct accessible names', () => {
    renderApp('/work')
    expect(screen.getByRole('button', { name: /Cutting, 8 items/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Stitching, 7 items/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Finishing, 5 items/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Ready, 4 items/i })).toBeInTheDocument()
  })
})
