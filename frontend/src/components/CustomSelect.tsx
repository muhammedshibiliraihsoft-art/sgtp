import { useState, useRef, useEffect, useId } from 'react'
import { ChevronDown } from 'lucide-react'
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
}

export function CustomSelect({ value, options, onChange, className = '', disabled = false, ariaLabel, id }: CustomSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([])
  const [activeIndex, setActiveIndex] = useState(0)
  const listboxId = useId()

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (isOpen) optionRefs.current[activeIndex]?.focus()
  }, [isOpen, activeIndex])

  const selectedOption = options.find(o => o.value === value) || options[0]
  const optionGroups = options.reduce<Array<{ group?: string; options: Array<{ option: SelectOption; index: number }> }>>((groups, option, index) => {
    let current = groups[groups.length - 1]
    if (!current || current.group !== option.group) {
      current = { group: option.group, options: [] }
      groups.push(current)
    }
    current.options.push({ option, index })
    return groups
  }, [])

  function openAt(index: number) {
    setActiveIndex(Math.max(0, Math.min(index, options.length - 1)))
    setIsOpen(true)
  }

  function selectOption(option: SelectOption) {
    onChange(option.value)
    setIsOpen(false)
    triggerRef.current?.focus()
  }

  return (
    <div className={`custom-select-container ${className}`} ref={containerRef}>
      <button 
        ref={triggerRef}
        id={id}
        type="button"
        className={`custom-select-trigger ${isOpen ? 'open' : ''}`}
        disabled={disabled || options.length === 0}
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={isOpen ? listboxId : undefined}
        onClick={() => isOpen ? setIsOpen(false) : openAt(Math.max(0, options.findIndex(option => option.value === value)))}
        onKeyDown={event => {
          if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            event.preventDefault()
            openAt(Math.max(0, options.findIndex(option => option.value === value)))
          } else if (event.key === 'Home') {
            event.preventDefault()
            openAt(0)
          } else if (event.key === 'End') {
            event.preventDefault()
            openAt(options.length - 1)
          }
        }}
      >
        <span>{selectedOption?.label ?? ''}</span>
        <ChevronDown size={16} className="custom-select-icon" />
      </button>

      {isOpen && (
        <div className="custom-select-dropdown" id={listboxId} role="listbox" aria-label={ariaLabel}>
          {optionGroups.map((group, groupIndex) => <div key={`${group.group ?? 'options'}-${groupIndex}`} role="group" aria-label={group.group || 'Options'}>
            {group.group && <div className="custom-select-group-label">{group.group}</div>}
            {group.options.map(({ option, index }) => (
              <button
                key={option.value}
                ref={element => { optionRefs.current[index] = element }}
                type="button"
                role="option"
                aria-selected={option.value === value}
                tabIndex={activeIndex === index ? 0 : -1}
                className={`custom-select-option ${option.value === value ? 'selected' : ''}`}
                onClick={() => selectOption(option)}
                onKeyDown={event => {
                  let nextIndex: number | null = null
                  if (event.key === 'ArrowDown') nextIndex = (index + 1) % options.length
                  else if (event.key === 'ArrowUp') nextIndex = (index - 1 + options.length) % options.length
                  else if (event.key === 'Home') nextIndex = 0
                  else if (event.key === 'End') nextIndex = options.length - 1
                  else if (event.key === 'Escape') {
                    event.preventDefault()
                    setIsOpen(false)
                    triggerRef.current?.focus()
                  } else if (event.key === 'Tab') setIsOpen(false)
                  if (nextIndex !== null) {
                    event.preventDefault()
                    setActiveIndex(nextIndex)
                  }
                }}
              >
                {option.label}
              </button>
            ))}
          </div>)}
        </div>
      )}
    </div>
  )
}
