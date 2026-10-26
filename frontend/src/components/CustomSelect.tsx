import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react'
import type { CSSProperties, KeyboardEvent as ReactKeyboardEvent, ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { Check, Plus, Search, X } from 'lucide-react'
import './CustomSelect.css'

export interface SelectOption {
  value: string
  label: string
  group?: string
}

interface CustomSelectProps {
  value: string
  options: SelectOption[]
  onChange: (value: string) => void
  className?: string
  disabled?: boolean
  ariaLabel?: string
  id?: string
  icon?: ReactNode
  compact?: boolean
}

const EMPTY_VALUE = ''

export function CustomSelect({ value, options, onChange, className = '', disabled = false, ariaLabel, id, icon, compact = false }: CustomSelectProps) {
  const emptyOption = options.find(option => option.value === EMPTY_VALUE)
  const choices = options.filter(option => option.value !== EMPTY_VALUE)
  return <ResponsiveChoice
    value={value}
    options={choices}
    onChange={onChange}
    className={className}
    disabled={disabled}
    ariaLabel={ariaLabel}
    id={id}
    icon={icon}
    compact={compact}
    placeholder={emptyOption?.label}
  />
}

export interface ResponsiveChoiceProps {
  value: string
  options: SelectOption[]
  onChange: (value: string) => void
  className?: string
  disabled?: boolean
  ariaLabel?: string
  id?: string
  placeholder?: string
  required?: boolean
  searchable?: boolean
  icon?: ReactNode
  compact?: boolean
  /** Fixed preview count followed by a matching tile to browse all choices. */
  previewLimit?: number
  /** Show this many choices on narrow screens and put the remaining count in the next grid slot. */
  mobilePreviewLimit?: number
  /** Keep the page and its scrollable panels in place after choosing from the popup. */
  preserveScrollOnDialogChoice?: boolean
}

interface ScrollSnapshot {
  elements: Array<{ element: HTMLElement; top: number; left: number }>
  x: number
  y: number
}

/** Responsive, touch-friendly replacement for native dropdown selection controls. */
export function ResponsiveChoice({
  value, options, onChange, className = '', disabled = false, ariaLabel, id, placeholder, required = false,
  searchable, icon, compact = false, previewLimit, mobilePreviewLimit, preserveScrollOnDialogChoice = false,
}: ResponsiveChoiceProps) {
  const hostRef = useRef<HTMLDivElement>(null)
  const triggerRefs = useRef<Array<HTMLButtonElement | null>>([])
  const popupTriggerRef = useRef<HTMLButtonElement>(null)
  const popupRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLInputElement>(null)
  const popupScrollSnapshotRef = useRef<ScrollSnapshot | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [visibleCount, setVisibleCount] = useState(4)
  const [isNarrowViewport, setIsNarrowViewport] = useState(() => window.innerWidth <= 480)
  const [invalid, setInvalid] = useState(false)
  const dialogId = useId()
  const selected = options.find(option => option.value === value)

  useEffect(() => {
    const host = hostRef.current
    if (!host) return
    const updateCount = (width: number) => {
      const viewport = window.innerWidth
      setIsNarrowViewport(viewport <= 480)
      const screenCap = viewport < 480 ? 4 : viewport < 900 ? 6 : viewport < 1440 ? 8 : 10
      const fit = Math.max(2, Math.floor(width / (viewport < 480 ? 82 : 104)))
      setVisibleCount(Math.min(screenCap, fit))
    }
    const handleResize = () => updateCount(host.getBoundingClientRect().width)
    handleResize()
    window.addEventListener('resize', handleResize)
    const observer = typeof ResizeObserver === 'undefined'
      ? null
      : new ResizeObserver(entries => updateCount(entries[0]?.contentRect.width ?? host.getBoundingClientRect().width))
    observer?.observe(host)
    return () => {
      window.removeEventListener('resize', handleResize)
      observer?.disconnect()
    }
  }, [])

  const visibleOptions = useMemo(() => {
    const limit = isNarrowViewport && mobilePreviewLimit !== undefined ? mobilePreviewLimit : previewLimit ?? visibleCount
    if (options.length <= limit) return options
    const visible = options.slice(0, limit)
    if (selected && !visible.some(option => option.value === selected.value)) {
      visible[visible.length - 1] = selected
    }
    return visible
  }, [isNarrowViewport, mobilePreviewLimit, options, previewLimit, selected, visibleCount])
  const hiddenCount = options.length - visibleOptions.length
  const showMobileOverflow = !compact && isNarrowViewport && mobilePreviewLimit !== undefined && hiddenCount > 0
  const filteredOptions = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase()
    if (!normalized) return options
    return options.filter(option => `${option.label} ${option.group ?? ''}`.toLocaleLowerCase().includes(normalized))
  }, [options, query])
  const groupedOptions = useMemo(() => filteredOptions.reduce<Array<{ group?: string; items: SelectOption[] }>>((groups, option) => {
    let group = groups[groups.length - 1]
    if (!group || group.group !== option.group) {
      group = { group: option.group, items: [] }
      groups.push(group)
    }
    group.items.push(option)
    return groups
  }, []), [filteredOptions])
  const showSearch = searchable ?? options.length > 8
  const restoreChoiceFocus = useCallback(() => {
    if (compact) popupTriggerRef.current?.focus({ preventScroll: true })
    else {
      const selectedTile = Array.from(hostRef.current?.querySelectorAll<HTMLButtonElement>('[data-choice-value]') ?? []).find(button => button.dataset.choiceValue === value)
      if (selectedTile) selectedTile.focus({ preventScroll: true })
      else popupTriggerRef.current?.focus({ preventScroll: true })
    }
  }, [compact, value])

  function updateOpen(open: boolean) {
    setIsOpen(open)
  }

  function captureScrollPosition(): ScrollSnapshot {
    const elements: HTMLElement[] = []
    let element = hostRef.current?.parentElement ?? null
    while (element) {
      elements.push(element)
      element = element.parentElement
    }
    return {
      elements: elements.map(item => ({ element: item, top: item.scrollTop, left: item.scrollLeft })),
      x: window.scrollX,
      y: window.scrollY,
    }
  }

  function restorePopupScroll() {
    const snapshot = popupScrollSnapshotRef.current
    popupScrollSnapshotRef.current = null
    if (!snapshot) return
    // Restore after the portal unmount and focus restoration have both had a
    // frame to run; mobile browsers may otherwise scroll the drawer to the top.
    requestAnimationFrame(() => requestAnimationFrame(() => {
      snapshot.elements.forEach(({ element, top, left }) => {
        if (element.isConnected) { element.scrollTop = top; element.scrollLeft = left }
      })
      window.scrollTo(snapshot.x, snapshot.y)
    }))
  }

  function closeChoices() {
    updateOpen(false)
    setQuery('')
    restoreChoiceFocus()
    if (preserveScrollOnDialogChoice) restorePopupScroll()
  }

  useEffect(() => {
    if (!isOpen) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        closeChoices()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    const focusTarget = showSearch ? searchRef.current : popupRef.current?.querySelector<HTMLButtonElement>('.responsive-choice-popup-option')
    focusTarget?.focus()
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [isOpen, showSearch, restoreChoiceFocus])

  function choose(option: SelectOption, fromDialog = false) {
    const scrollPositions = preserveScrollOnDialogChoice && fromDialog ? popupScrollSnapshotRef.current : null
    onChange(option.value)
    setInvalid(false)
    updateOpen(false)
    setQuery('')
    requestAnimationFrame(() => {
      if (compact) popupTriggerRef.current?.focus({ preventScroll: Boolean(scrollPositions) })
      else if (scrollPositions) popupTriggerRef.current?.focus({ preventScroll: true })
      else Array.from(hostRef.current?.querySelectorAll<HTMLButtonElement>('[data-choice-value]') ?? []).find(button => button.dataset.choiceValue === option.value)?.focus()
      if (scrollPositions) restorePopupScroll()
    })
  }

  function openChoices(trigger: HTMLButtonElement) {
    if (preserveScrollOnDialogChoice) popupScrollSnapshotRef.current = captureScrollPosition()
    // The dialog manager uses the active element as its return target. Mobile
    // browsers do not consistently focus a button after a tap, so set it here.
    trigger.focus({ preventScroll: true })
    updateOpen(true)
  }

  function onTileKeyDown(event: ReactKeyboardEvent<HTMLButtonElement>, index: number) {
    let next: number | undefined
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % visibleOptions.length
    else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + visibleOptions.length) % visibleOptions.length
    else if (event.key === 'Home') next = 0
    else if (event.key === 'End') next = visibleOptions.length - 1
    if (next !== undefined) {
      event.preventDefault()
      triggerRefs.current[next]?.focus()
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      choose(visibleOptions[index])
    }
  }

  return <div ref={hostRef} className={`responsive-choice ${className}`} id={id} role={compact ? undefined : 'group'} aria-label={compact ? undefined : ariaLabel} aria-disabled={disabled || undefined} aria-required={required || undefined} aria-invalid={invalid || undefined}>
    {required && <select className="responsive-choice-validation" tabIndex={-1} aria-hidden="true" value={value} required onInvalid={event => { event.preventDefault(); setInvalid(true); updateOpen(true) }} onChange={() => undefined}>
      <option value="" />{options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
    </select>}
    {placeholder && !selected && <div className="responsive-choice-placeholder" aria-live="polite">{placeholder}{required ? ' *' : ''}</div>}
    {compact ? <button ref={popupTriggerRef} type="button" className="responsive-choice-compact-trigger" aria-haspopup="dialog" aria-expanded={isOpen} aria-controls={isOpen ? dialogId : undefined} aria-label={ariaLabel} disabled={disabled} onClick={event => openChoices(event.currentTarget)}>
      {icon && <span className="responsive-choice-leading-icon" aria-hidden="true">{icon}</span>}<span className="responsive-choice-compact-label">{selected?.label ?? placeholder ?? 'Choose an option'}</span><span className="responsive-choice-compact-caret" aria-hidden="true">⌄</span>
    </button> : <div className={`responsive-choice-grid${previewLimit !== undefined ? ' has-preview-limit' : ''}${mobilePreviewLimit !== undefined ? ' has-mobile-preview' : ''}`} style={{ '--choice-columns': previewLimit !== undefined ? 3 : Math.max(1, Math.min(visibleCount, visibleOptions.length)) } as CSSProperties}>
      {visibleOptions.map((option, index) => <button
        key={option.value}
        ref={element => { triggerRefs.current[index] = element }}
        type="button"
        disabled={disabled}
        className={`responsive-choice-tile${value === option.value ? ' is-selected' : ''}`}
        data-choice-value={option.value}
        aria-pressed={value === option.value}
        aria-label={option.label}
        onClick={() => choose(option)}
        onKeyDown={event => onTileKeyDown(event, index)}
      >
        {value === option.value && <Check className="responsive-choice-check" size={15} aria-hidden="true" />}
        <span>{option.label}</span>
      </button>)}
      {showMobileOverflow && <button ref={popupTriggerRef} type="button" className="responsive-choice-tile responsive-choice-mobile-more" aria-label={`+${hiddenCount} more`} aria-haspopup="dialog" aria-expanded={isOpen} aria-controls={isOpen ? dialogId : undefined} disabled={disabled} onClick={event => openChoices(event.currentTarget)}>
        +{hiddenCount} more
      </button>}
    </div>}
    {!compact && previewLimit !== undefined && <button ref={popupTriggerRef} type="button" className="responsive-choice-more-tile" aria-label={`Browse all ${options.length} choices`} aria-haspopup="dialog" aria-expanded={isOpen} aria-controls={isOpen ? dialogId : undefined} disabled={disabled} onClick={event => openChoices(event.currentTarget)}>
        <Plus size={20} aria-hidden="true" /><span>More</span>
      </button>}
    {!compact && !showMobileOverflow && previewLimit === undefined && hiddenCount > 0 && <button ref={popupTriggerRef} type="button" className="responsive-choice-more" aria-label={`+${hiddenCount} more`} aria-haspopup="dialog" aria-expanded={isOpen} aria-controls={isOpen ? dialogId : undefined} disabled={disabled} onClick={event => openChoices(event.currentTarget)}>
        <span>+{hiddenCount}</span><small>more</small>
      </button>}
    {invalid && <small className="responsive-choice-error" role="alert">Choose an option to continue.</small>}
    {isOpen && createPortal(<div className="responsive-choice-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) closeChoices() }}>
      <section ref={popupRef} className="responsive-choice-dialog" role="dialog" aria-modal="true" aria-labelledby={`${dialogId}-title`} id={dialogId} onKeyDown={event => {
        if (event.key !== 'Tab') return
        const focusable = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled)'))
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
      }}>
        <div className="responsive-choice-dialog-heading"><h2 id={`${dialogId}-title`}>{ariaLabel || placeholder || 'Choose an option'}</h2><button type="button" className="responsive-choice-close" aria-label="Close choices" onClick={closeChoices}><X size={20} /></button></div>
        {showSearch && <label className="responsive-choice-search"><Search size={17} aria-hidden="true"/><span className="sr-only">Search options</span><input ref={searchRef} type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search options" /></label>}
        <div className="responsive-choice-popup-list" role="list">
          {groupedOptions.map((group, index) => <div className="responsive-choice-group" key={`${group.group ?? 'options'}-${index}`}>
            {group.group && <h3>{group.group}</h3>}
            {group.items.map(option => <button key={option.value} type="button" className={`responsive-choice-popup-option${value === option.value ? ' is-selected' : ''}`} aria-pressed={value === option.value} onClick={() => choose(option, true)}>
              <span>{option.label}</span>{value === option.value && <Check size={17} aria-hidden="true"/>}
            </button>)}
          </div>)}
          {!filteredOptions.length && <p className="responsive-choice-empty">No matching options.</p>}
        </div>
      </section>
    </div>, document.body)}
  </div>
}
