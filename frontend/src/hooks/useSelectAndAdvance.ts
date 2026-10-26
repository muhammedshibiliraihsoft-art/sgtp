import { useCallback, useEffect, useLayoutEffect, useRef } from 'react'
import type { ChangeEvent, KeyboardEvent, PointerEvent } from 'react'

export type SelectionMode = 'SINGLE' | 'MULTI'

type SelectAndAdvanceOptions<Item> = {
  selectionMode: SelectionMode
  selectedItems: readonly Item[]
  onChange: (selectedItems: Item[]) => void
  onCommit?: (selectedItems: Item[]) => void
  onAdvance: () => void
  scopeKey: string
  doubleActivationDelay?: number
}

/** Adds an item selection on the first activation and commits/advances on a
 * second activation of that same item within the configured time window.
 */
export function useSelectAndAdvance<Item>({
  selectionMode,
  selectedItems,
  onChange,
  onCommit,
  onAdvance,
  scopeKey,
  doubleActivationDelay = 350,
}: SelectAndAdvanceOptions<Item>) {
  const selectionRef = useRef([...selectedItems])
  const lastActivationRef = useRef<{ item: Item; at: number; kind: 'pointer' | 'keyboard' } | null>(null)
  const advancedRef = useRef(false)

  // Sync after React commits so activation handlers always read controlled UI state.
  useLayoutEffect(() => {
    selectionRef.current = [...selectedItems]
  }, [selectedItems])

  useEffect(() => {
    lastActivationRef.current = null
    advancedRef.current = false
  }, [scopeKey])

  const setSelectedItems = useCallback((next: Item[]) => {
    selectionRef.current = next
    onChange(next)
  }, [onChange])

  const ensureSelected = useCallback((item: Item) => {
    const current = selectionRef.current
    if (current.includes(item)) return [...current]
    return selectionMode === 'SINGLE' ? [item] : [...current, item]
  }, [selectionMode])

  const activateAgain = useCallback((item: Item, at: number, kind: 'pointer' | 'keyboard') => {
    const previous = lastActivationRef.current
    const isSecondActivation = previous?.item === item && previous.kind === kind && at - previous.at <= doubleActivationDelay
    if (!isSecondActivation || advancedRef.current) {
      lastActivationRef.current = { item, at, kind }
      return false
    }

    const finalSelection = ensureSelected(item)
    setSelectedItems(finalSelection)
    lastActivationRef.current = null
    advancedRef.current = true
    onCommit?.(finalSelection)
    onAdvance()
    return true
  }, [doubleActivationDelay, ensureSelected, onAdvance, onCommit, setSelectedItems])

  const getItemProps = useCallback((item: Item, disabled = false) => ({
    onPointerDown(event: PointerEvent<HTMLElement>) {
      if (disabled || (typeof event.button === 'number' && event.button !== 0) || event.isPrimary === false) return
      if (activateAgain(item, event.timeStamp, 'pointer')) event.preventDefault()
    },
    onChange(_event: ChangeEvent<HTMLInputElement>) {
      if (disabled || advancedRef.current) return
      const current = selectionRef.current
      const next = selectionMode === 'SINGLE'
        ? [item]
        : current.includes(item) ? current.filter(selected => selected !== item) : [...current, item]
      setSelectedItems(next)
    },
    onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
      if (disabled || event.key !== 'Enter') return
      event.preventDefault()
      event.stopPropagation()
      if (activateAgain(item, event.timeStamp, 'keyboard')) return
      setSelectedItems(ensureSelected(item))
    },
  }), [activateAgain, ensureSelected, selectionMode, setSelectedItems])

  return { getItemProps }
}
