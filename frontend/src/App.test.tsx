import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { cleanup, render } from '@testing-library/react'
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
    expect(screen.getByText('Foundation preview')).toBeInTheDocument()
    expect(screen.getByText(/No live business data or backend actions are connected/)).toBeInTheDocument()
    expect(screen.getByText('Work')).toHaveAttribute('aria-disabled', 'true')
    expect(screen.getByLabelText('Sample workspace').tagName).toBe('DIV')
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
    fireEvent.change(screen.getByLabelText('Language'), { target: { value: 'ar-KW' } })
    await screen.findByText('صباح الخير، أليكس')
    expect(document.documentElement.dir).toBe('rtl')
    await i18n.changeLanguage('bn')
    expect(i18n.dir()).toBe('ltr')
  })

  it('supports explicit light, dark and system theme preferences', () => {
    renderApp()
    const theme = screen.getByLabelText('Color theme')
    fireEvent.change(theme, { target: { value: 'dark' } })
    expect(localStorage.getItem('sgtp-theme')).toBe('dark')
    fireEvent.change(theme, { target: { value: 'system' } })
    expect(localStorage.getItem('sgtp-theme')).toBe('system')
  })
})
