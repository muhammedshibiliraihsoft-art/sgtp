import { useEffect } from 'react'

const DIALOG_SELECTOR = '[role="dialog"][aria-modal="true"], dialog[open]'
const FOCUSABLE_SELECTOR = 'a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])'

export function DialogKeyboardManager() {
  useEffect(() => {
    let activeDialog: HTMLElement | null = null
    let returnFocus: HTMLElement | null = null

    const focusables = (dialog: HTMLElement) => [...dialog.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)]
      .filter(element => !element.closest('[hidden], [inert]')
        && getComputedStyle(element).display !== 'none'
        && getComputedStyle(element).visibility !== 'hidden')

    const syncDialog = () => {
      const dialogs = [...document.querySelectorAll<HTMLElement>(DIALOG_SELECTOR)]
      const next = dialogs.at(-1) ?? null
      if (next === activeDialog) return
      if (activeDialog && returnFocus?.isConnected) returnFocus.focus()
      activeDialog = next
      returnFocus = next && document.activeElement instanceof HTMLElement ? document.activeElement : null
      if (next) {
        const target = focusables(next)[0] ?? next
        if (target === next && !next.hasAttribute('tabindex')) next.tabIndex = -1
        requestAnimationFrame(() => target.isConnected && target.focus())
      }
    }

    const onKeyDown = (event: KeyboardEvent) => {
      syncDialog()
      const dialog = activeDialog
      if (!dialog) return
      if (event.key === 'Escape') {
        const close = dialog.querySelector<HTMLElement>('[data-dialog-close], [aria-label*="close" i], [aria-label*="cancel" i]')
          ?? [...dialog.querySelectorAll<HTMLElement>('button')].find(button => /^(cancel|close|back)$/i.test(button.textContent?.trim() ?? ''))
        if (close) {
          event.preventDefault()
          event.stopImmediatePropagation()
          close.click()
        }
        return
      }
      if (event.key !== 'Tab') return
      const controls = focusables(dialog)
      if (!controls.length) {
        event.preventDefault()
        dialog.focus()
        return
      }
      const first = controls[0]
      const last = controls[controls.length - 1]
      if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && (document.activeElement === last || !dialog.contains(document.activeElement))) {
        event.preventDefault()
        first.focus()
      }
    }

    const onFocusIn = (event: FocusEvent) => {
      syncDialog()
      if (activeDialog && event.target instanceof Node && !activeDialog.contains(event.target)) {
        ;(focusables(activeDialog)[0] ?? activeDialog).focus()
      }
    }

    const observer = new MutationObserver(syncDialog)
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['open', 'role', 'aria-modal'],
    })
    document.addEventListener('keydown', onKeyDown, true)
    document.addEventListener('focusin', onFocusIn, true)
    syncDialog()
    return () => {
      observer.disconnect()
      document.removeEventListener('keydown', onKeyDown, true)
      document.removeEventListener('focusin', onFocusIn, true)
      if (returnFocus?.isConnected) returnFocus.focus()
    }
  }, [])
  return null
}
