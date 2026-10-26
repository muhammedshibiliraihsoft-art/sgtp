import { ChevronDown, ChevronRight, Check } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { OptionGroup, StyleOption } from '../catalog/types'
import { PrivateReferenceGallery } from './PrivateReferenceImage'

interface Props {
  groups: OptionGroup[]
  selected: Record<string, StyleOption[]>
  activeGroupId: string | null
  optionsByGroup: Record<string, StyleOption[]>
  loadingGroupId: string | null
  groupErrorId: string | null
  onOpenGroup: (groupId: string) => void
  onSelectOption: (groupId: string, option: StyleOption) => void
  onRetryGroup: (groupId: string) => void
  canWrite: boolean
}

export function StyleConfiguration({
  groups, selected, activeGroupId, optionsByGroup, loadingGroupId, groupErrorId,
  onOpenGroup, onSelectOption, onRetryGroup, canWrite,
}: Props) {
  const { t } = useTranslation()
  if (groups.length === 0) {
    return <div className="measurement-empty" role="status">{t('measurements.noGroups')}</div>
  }

  return <div className="measurement-style-groups">
    {groups.map(group => {
      const isOpen = activeGroupId === group.id
      const current = selected[group.id] ?? []
      return <section className={`measurement-style-group${isOpen ? ' is-open' : ''}`} key={group.id}>
        <button type="button" className="measurement-style-group-toggle" aria-expanded={isOpen} onClick={() => onOpenGroup(group.id)}>
          <span className="measurement-style-group-copy">
            <strong>{group.name}</strong>
            <small>{current.length ? `${current[0].name}${current.length > 1 ? ` +${current.length - 1}` : ''}` : t('measurements.noOptionSelected')}</small>
          </span>
          {current.length > 0 && <Check size={18} aria-label="Selected" />}
          {isOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
        </button>
        {isOpen && <div className="measurement-style-group-body">
          {loadingGroupId === group.id ? <div className="measurement-empty" aria-busy="true">{t('measurements.loadingOptions')}</div>
            : groupErrorId === group.id ? <div className="measurement-error-inline" role="alert"><span>{t('measurements.optionLoadError', { name: group.name })}</span><button type="button" className="btn-secondary" onClick={() => onRetryGroup(group.id)}>{t('measurements.retry')}</button></div>
              : (optionsByGroup[group.id] ?? []).length === 0 ? <div className="measurement-empty">{t('measurements.noOptions')}</div>
                : <div className="measurement-option-grid">{(optionsByGroup[group.id] ?? []).map(option => <article
                  className={`measurement-option-card${current.some(item => item.id === option.id) ? ' is-selected' : ''}`}
                  key={option.id}
                >
                  <PrivateReferenceGallery images={option.reference_images} alt={t('measurements.referenceAlt', { name: option.name })} />
                  <button type="button" className="measurement-option-select" aria-pressed={current.some(item => item.id === option.id)} onClick={() => onSelectOption(group.id, option)} disabled={!canWrite}>
                    <span className="measurement-option-copy"><strong>{option.name}</strong><small>{option.code}</small></span>
                    <span className="measurement-option-source">{option.is_global ? t('measurements.global') : t('measurements.shop')}</span>
                  </button>
                </article>)}</div>}
        </div>}
      </section>
    })}
  </div>
}
