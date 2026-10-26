import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ApiError } from '../../services/apiClient'
import { useAuth } from '../../services/useAuth'
import './password-reset.css'

export function PasswordResetPage() {
  const { t } = useTranslation()
  const { confirmPasswordReset, requestPasswordReset } = useAuth()
  const [searchParams] = useSearchParams()
  const uid = searchParams.get('uid') ?? ''
  const token = searchParams.get('token') ?? ''
  const isConfirmation = Boolean(uid && token)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const invalidLink = searchParams.has('uid') || searchParams.has('token') ? !isConfirmation : false

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setMessage('')
    setIsLoading(true)
    try {
      if (isConfirmation) {
        await confirmPasswordReset(uid, token, password, passwordConfirm)
        setMessage(t('auth.passwordResetComplete', 'Password reset. Sign in with your new password.'))
        setPassword('')
        setPasswordConfirm('')
      } else {
        await requestPasswordReset(email.trim())
        setMessage(t('auth.passwordResetRequested', 'If the account is eligible, password reset instructions will be sent.'))
      }
    } catch (cause: unknown) {
      setError(cause instanceof ApiError || cause instanceof Error
        ? cause.message
        : t('auth.passwordResetError', 'Unable to complete the request. Please try again.'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-form-area">
        <div className="login-form-container">
          <div className="login-header">
            <h1>{invalidLink
              ? t('auth.passwordResetInvalidTitle', 'Reset link is incomplete')
              : isConfirmation
                ? t('auth.passwordResetTitle', 'Choose a new password')
                : t('auth.forgotPasswordTitle', 'Forgot your password?')}</h1>
            <p className="login-subtitle">{invalidLink
              ? t('auth.passwordResetInvalidHint', 'Open the complete password-reset link from your email.')
              : isConfirmation
                ? t('auth.passwordResetConfirmHint', 'Choose a new password for your account.')
                : t('auth.forgotPasswordHint', 'Enter your account email. If eligible, we will send reset instructions.')}</p>
          </div>

          {error && <div className="login-error-message" role="alert">{error}</div>}
          {message && <div className="password-reset-status" role="status">{message}</div>}

          {!invalidLink && !(isConfirmation && message) && <form className="login-form" onSubmit={submit}>
            {isConfirmation ? <>
              <label className="field-label" htmlFor="reset-password">{t('auth.newPassword', 'New password')}</label>
              <input id="reset-password" type="password" autoComplete="new-password" value={password} onChange={event => setPassword(event.target.value)} required disabled={isLoading} />
              <label className="field-label" htmlFor="reset-password-confirm">{t('auth.confirmPassword', 'Confirm new password')}</label>
              <input id="reset-password-confirm" type="password" autoComplete="new-password" value={passwordConfirm} onChange={event => setPasswordConfirm(event.target.value)} required disabled={isLoading} />
            </> : <>
              <label className="field-label" htmlFor="reset-email">{t('auth.accountEmail', 'Account email')}</label>
              <input id="reset-email" type="email" autoComplete="email" inputMode="email" value={email} onChange={event => setEmail(event.target.value)} required disabled={isLoading} />
            </>}
            <button className="primary-button submit-button" type="submit" disabled={isLoading}>
              {isLoading
                ? t('auth.processing', 'Please wait…')
                : isConfirmation
                  ? t('auth.resetPasswordAction', 'Reset password')
                  : t('auth.sendResetInstructions', 'Send reset instructions')}
            </button>
          </form>}

          <p><Link to="/login">{t('auth.backToLogin', 'Back to sign in')}</Link></p>
        </div>
      </section>
    </main>
  )
}
