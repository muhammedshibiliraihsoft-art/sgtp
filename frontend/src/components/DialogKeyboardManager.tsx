import { useEffect } from 'react'

const DIALOG_SELECTOR = '[role="dialog"][aria-modal="true"], dialog[open]'
const FOCUSABLE_SELECTOR = 'a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])'

export function DialogKeyboardManager() {
  useEffect(() => {
    let activeDialog: HTMLElement | null = null
    let returnFocus: HTMLElement | null = null
    let pendingCloseFrame = 0

    const focusables = (dialog: HTMLElement) => [...dialog.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)]
      .filter(element => !element.closest('[hidden], [inert]')
        && getComputedStyle(element).display !== 'none'
        && getComputedStyle(element).visibility !== 'hidden')

    const syncDialog = () => {
      const dialogs = [...document.querySelectorAll<HTMLElement>(DIALOG_SELECTOR)]
      const next = dialogs.at(-1) ?? null
      if (next && pendingCloseFrame) {
        cancelAnimationFrame(pendingCloseFrame)
        pendingCloseFrame = 0
      }
      if (next === activeDialog) return
      // Catalog temporarily removes aria-modal from its drawer while a
      // body-portaled choice dialog is active. Keep the drawer as the current
      // modal through that brief gap so its original opener is not restored.
      if (!next && activeDialog?.isConnected && activeDialog.getAttribute('aria-modal') === 'false') return
      // A nested dialog can be portaled to document.body, so DOM containment
      // cannot tell whether this is a dialog transition or the modal closing.
      // Keep the current focus during transitions; the dialog itself restores
      // focus to its trigger. Restore the original opener only when all modals
      // have closed.
      if (activeDialog && !next) {
        // Focus can return from a body portal before React restores the
        // underlying drawer's aria-modal attribute. Wait one frame so that
        // transition is not mistaken for the final dialog closing.
        if (!pendingCloseFrame) pendingCloseFrame = requestAnimationFrame(() => {
          pendingCloseFrame = 0
          const current = [...document.querySelectorAll<HTMLElement>(DIALOG_SELECTOR)].at(-1) ?? null
          if (current) {
            syncDialog()
            return
          }
          if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true })
          activeDialog = null
          returnFocus = null
        })
        return
      }
      const openingFirstDialog = !activeDialog && Boolean(next)
      activeDialog = next
      if (openingFirstDialog) returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
      if (next && openingFirstDialog) {
        const target = focusables(next)[0] ?? next
        if (target === next && !next.hasAttribute('tabindex')) next.tabIndex = -1
        requestAnimationFrame(() => target.isConnected && target.focus({ preventScroll: true }))
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
      // A browser may briefly move focus to body as a portaled dialog closes.
      // Let the picker restore focus after its React update instead of
      // redirecting that transient focus to the drawer header.
      if (event.target === document.body || event.target === document.documentElement) return
      if (activeDialog && event.target instanceof Node && !activeDialog.contains(event.target)) {
        ;(focusables(activeDialog)[0] ?? activeDialog).focus({ preventScroll: true })
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
      if (pendingCloseFrame) cancelAnimationFrame(pendingCloseFrame)
      document.removeEventListener('keydown', onKeyDown, true)
      document.removeEventListener('focusin', onFocusIn, true)
      if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true })
    }
  }, [])
  return null
}
