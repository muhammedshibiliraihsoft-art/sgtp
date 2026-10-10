import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { pinResetService } from './services/pinReset'

export function PinResetPage() {
  const { t } = useTranslation()
  const [phone, setPhone] = useState('')
  const [busy, setBusy] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const submitInFlight = useRef(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (submitInFlight.current) return
    setError('')
    const normalizedPhone = phone.trim()
    const compactPhone = normalizedPhone.replace(/[ ()-]/g, '')
    if (!/^\+[1-9][0-9]{7,14}$/.test(compactPhone)) {
      setError(t('auth.phoneFormatError'))
      return
    }
    submitInFlight.current = true
    setBusy(true)
    try {
      await pinResetService.request(normalizedPhone)
      setSent(true)
    } catch {
      setError(t('auth.recoverySubmitError'))
    } finally { submitInFlight.current = false; setBusy(false) }
  }

  return <main className="login-page"><section className="login-form-area"><div className="login-form-container">
    <div className="login-header"><h1>{t('auth.recoveryTitle')}</h1><p className="login-subtitle">{t('auth.recoveryIntro')}</p><p className="auth-field-hint">{t('auth.recoveryApprovalNote')}</p></div>
    {sent ? <p role="status">{t('auth.recoverySuccess')}</p> : <form className="login-form" onSubmit={submit}>
      {error && <div className="login-error-message" role="alert">{error}</div>}
      <label className="field-label" htmlFor="reset-phone">{t('auth.registeredPhone')}</label>
      <input id="reset-phone" type="tel" inputMode="tel" autoComplete="tel" placeholder={t('auth.phoneExample')} aria-describedby="reset-phone-hint" value={phone} onChange={event => setPhone(event.target.value)} required disabled={busy} />
      <span className="auth-field-hint" id="reset-phone-hint">{t('auth.phoneFormatHint')}</span>
      <button className="primary-button submit-button" type="submit" disabled={busy}>{busy ? t('auth.submitting') : t('auth.requestReset')}</button>
    </form>}
    <Link to="/login">{t('auth.backToLogin')}</Link>
  </div></section></main>
}
