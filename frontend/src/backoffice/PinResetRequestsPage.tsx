import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { pinResetService } from '../services/pinReset'
import type { PendingPinReset } from '../services/pinReset'
import './backoffice.css'

export function PinResetRequestsPage() {
  const { t } = useTranslation()
  const [requests, setRequests] = useState<PendingPinReset[]>([])
  const [busyId, setBusyId] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [result, setResult] = useState<{ login_id: string | null; temporary_password: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const resolveInFlight = useRef(false)

  useEffect(() => {
    let active = true
    pinResetService.pending().then(rows => { if (active) setRequests(rows) })
      .catch(() => { if (active) setError('auth.queueLoadError') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const resolve = async (row: PendingPinReset, approve: boolean) => {
    if (resolveInFlight.current) return
    if (!window.confirm(t(approve ? 'auth.confirmApprove' : 'auth.confirmReject', { name: row.name, shop: row.shop }))) return
    resolveInFlight.current = true
    setBusyId(row.id); setError('')
    try {
      if (approve) {
        const approved = await pinResetService.approve(row.id)
        setResult({ login_id: approved.login_id, temporary_password: approved.temporary_password })
      } else await pinResetService.reject(row.id)
      setRequests(previous => previous.filter(item => item.id !== row.id))
    } catch {
      setError(t('auth.resolveError'))
    } finally { resolveInFlight.current = false; setBusyId(null) }
  }

  return <div className="content-wrap bo-content">
    <Link className="bo-back" to="/backoffice">{t('auth.backOffice')}</Link>
    <div className="bo-page-heading"><div><span className="bo-eyebrow">{t('auth.backOffice')}</span><h1>{t('auth.queueTitle')}</h1><p>{t('auth.queueIntro')}</p></div></div>
    {error && <div className="bo-error" role="alert">{error.startsWith('auth.') ? t(error) : error}</div>}
    {loading ? <p role="status">{t('auth.queueLoading')}</p> : requests.length === 0 ? <p>{t('auth.queueEmpty')}</p> : requests.map(row => <section className="bo-card" key={row.id}>
      <h2>{row.name}</h2><p>{t('auth.shopLabel')}: {row.shop}</p><p>{t('auth.loginIdLabel')}: {row.login_id || t('auth.notAssigned')}</p><p>{t('auth.registeredPhone')}: {row.phone}</p><p>{t('auth.requestedLabel')}: {new Date(row.requested_at).toLocaleString()}</p>
      <div className="bo-actions"><button type="button" className="primary-button" disabled={Boolean(busyId)} onClick={() => void resolve(row, true)}>{busyId === row.id ? t('auth.processing') : t('auth.approve')}</button>
        <button type="button" className="bo-secondary-button" disabled={Boolean(busyId)} onClick={() => void resolve(row, false)}>{busyId === row.id ? t('auth.processing') : t('auth.reject')}</button></div>
    </section>)}
    {result && <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="reset-result-title"><div className="modal-content credentials-modal">
      <h2 id="reset-result-title">{t('auth.pinIssuedTitle')}</h2><p>{t('auth.pinIssuedWarning')}</p>
      <p>{t('auth.loginIdLabel')}: <strong>{result.login_id || t('auth.legacyLoginHint')}</strong></p>
      <p>{t('auth.temporaryPinLabel')}: <code>{result.temporary_password}</code></p>
      <p>{t('auth.pinChangeRequired')}</p>
      <button type="button" className="btn-primary" onClick={() => setResult(null)}>{t('auth.dismissPin')}</button>
    </div></div>}
  </div>
}
