import { useTranslation } from 'react-i18next'
import { AlertTriangle } from 'lucide-react'

type DuplicateWarningProps = {
  matches: { id: string; name: string }[]
}

export function DuplicateWarning({ matches }: DuplicateWarningProps) {
  const { t } = useTranslation()
  
  if (matches.length === 0) return null

  return (
    <div className="duplicate-warning">
      <h4><AlertTriangle size={16} /> {t('clients.possibleDuplicate')}</h4>
      <p>{t('clients.duplicateHint')}</p>
      <div>
        <strong>{t('clients.matchedClients')}</strong>
        <ul>
          {matches.map(m => (
            <li key={m.id}>{m.name}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}
