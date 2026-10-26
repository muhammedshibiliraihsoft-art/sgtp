import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { PasswordResetPage } from './PasswordResetPage'

const authContextMock = vi.hoisted(() => ({ requestPasswordReset: vi.fn(), confirmPasswordReset: vi.fn() }))
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (_key: string, fallback: string) => fallback }) }))
vi.mock('../../services/useAuth', () => ({ useAuth: () => authContextMock }))

afterEach(() => { cleanup(); vi.clearAllMocks() })

describe('PasswordResetPage', () => {
  it('sends an email-reset request and shows only the generic server response', async () => {
    authContextMock.requestPasswordReset.mockResolvedValue(undefined)
    render(<MemoryRouter><PasswordResetPage /></MemoryRouter>)
    fireEvent.change(screen.getByLabelText('Account email'), { target: { value: ' member@example.test ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send reset instructions' }))
    await waitFor(() => expect(authContextMock.requestPasswordReset).toHaveBeenCalledWith('member@example.test'))
    expect(await screen.findByRole('status')).toHaveTextContent('If the account is eligible')
  })

  it('keeps the request form input and reports an API failure', async () => {
    authContextMock.requestPasswordReset.mockRejectedValue(new Error('Service unavailable.'))
    render(<MemoryRouter><PasswordResetPage /></MemoryRouter>)
    const emailInput = screen.getByLabelText('Account email') as HTMLInputElement
    fireEvent.change(emailInput, { target: { value: 'member@example.test' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send reset instructions' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Service unavailable.')
    expect(emailInput.value).toBe('member@example.test')
  })

  it('confirms a reset using query credentials, then clears password inputs', async () => {
    authContextMock.confirmPasswordReset.mockResolvedValue(undefined)
    render(<MemoryRouter initialEntries={['/reset-password?uid=user-token&token=single-use']}><PasswordResetPage /></MemoryRouter>)
    fireEvent.change(screen.getByLabelText('New password'), { target: { value: 'NewSecure-939!Pass' } })
    fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'NewSecure-939!Pass' } })
    fireEvent.click(screen.getByRole('button', { name: 'Reset password' }))
    await waitFor(() => expect(authContextMock.confirmPasswordReset).toHaveBeenCalledWith('user-token', 'single-use', 'NewSecure-939!Pass', 'NewSecure-939!Pass'))
    expect(await screen.findByRole('status')).toHaveTextContent('Password reset.')
    expect(screen.queryByLabelText('New password')).not.toBeInTheDocument()
  })

  it('does not render reset controls for an incomplete emailed link', () => {
    render(<MemoryRouter initialEntries={['/reset-password?uid=only-one-part']}><PasswordResetPage /></MemoryRouter>)
    expect(screen.getByRole('heading', { name: 'Reset link is incomplete' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Reset password' })).not.toBeInTheDocument()
  })
})
