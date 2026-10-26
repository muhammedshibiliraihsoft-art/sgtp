import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { X } from 'lucide-react'
import { DuplicateWarning } from './DuplicateWarning'

export type FormValues = {
  name: string
  phone: string
  email: string
}

type ClientFormProps = {
  isOpen: boolean
  onClose: () => void
  onSave: (values: FormValues) => void
  initialValues?: FormValues
  title: string
  duplicateMatches?: { id: string; name: string }[]
}

export function ClientForm({ isOpen, onClose, onSave, initialValues, title, duplicateMatches = [] }: ClientFormProps) {
  const { t } = useTranslation()
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')

  useEffect(() => {
    if (isOpen) {
      setName(initialValues?.name || '')
      setPhone(initialValues?.phone || '')
      setEmail(initialValues?.email || '')
    }
  }, [isOpen, initialValues])

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    onSave({ name, phone, email })
  }


  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-title" tabIndex={-1}>
      <div className="modal-content">
        <div className="modal-header">
          <h2 id="modal-title">{title}</h2>
          <button data-dialog-close className="modal-close" onClick={onClose} aria-label={t('clients.cancel')}>
            <X size={20} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-body" style={{ paddingBottom: 0 }}>
          <DuplicateWarning matches={duplicateMatches} />
          
          <div className="form-group">
            <label htmlFor="client-name" className="form-label">{t('clients.name')} *</label>
            <input 
              id="client-name" 
              className="form-input" 
              value={name} 
              onChange={e => setName(e.target.value)} 
              required 
              autoFocus
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="client-phone" className="form-label">{t('clients.phone')}</label>
            <input 
              id="client-phone" 
              className="form-input" 
              type="tel"
              value={phone} 
              onChange={e => setPhone(e.target.value)} 
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="client-email" className="form-label">{t('clients.email')}</label>
            <input 
              id="client-email" 
              className="form-input" 
              type="email"
              value={email} 
              onChange={e => setEmail(e.target.value)} 
            />
          </div>
        </form>
        
        <div className="modal-footer">
          <button data-dialog-close type="button" className="btn-secondary" onClick={onClose}>{t('clients.cancel')}</button>
          <button type="button" className="btn-primary" onClick={handleSubmit} disabled={!name.trim()}>
            {t('clients.save')}
          </button>
        </div>
      </div>
    </div>
  )
}
