import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { X, AlertCircle } from 'lucide-react'

type ConfirmDeleteModalProps = {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
}

export function ConfirmDeleteModal({ isOpen, onClose, onConfirm, title, message }: ConfirmDeleteModalProps) {
  const { t } = useTranslation()

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  if (!isOpen) return null

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="delete-title" tabIndex={-1}>
      <div className="modal-content" style={{ maxWidth: 400 }}>
        <div className="modal-header" style={{ borderBottom: 'none', paddingBottom: 0 }}>
          <h2 id="delete-title" style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-danger)' }}>
            <AlertCircle size={20} /> {title}
          </h2>
          <button data-dialog-close className="modal-close" onClick={onClose} aria-label={t('clients.cancel')}>
            <X size={20} />
          </button>
        </div>
        
        <div className="modal-body" style={{ paddingTop: 16 }}>
          <p style={{ margin: 0, color: 'var(--color-text)', fontSize: 14, lineHeight: 1.5 }}>
            {message}
          </p>
        </div>
        
        <div className="modal-footer" style={{ borderTop: 'none', paddingTop: 0 }}>
          <button data-dialog-close type="button" className="btn-secondary" onClick={onClose}>{t('clients.cancel')}</button>
          <button type="button" className="btn-primary" onClick={onConfirm} style={{ background: 'var(--color-danger)' }}>
            {t('clients.remove')}
          </button>
        </div>
      </div>
    </div>
  )
}
