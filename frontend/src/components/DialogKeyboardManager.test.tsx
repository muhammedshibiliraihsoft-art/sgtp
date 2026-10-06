import { useState } from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { DialogKeyboardManager } from './DialogKeyboardManager'

function Harness() {
  const [open, setOpen] = useState(false)
  return <>
    <DialogKeyboardManager />
    <button onClick={() => setOpen(true)}>Open dialog</button>
    {open && <section role="dialog" aria-modal="true" aria-label="Test dialog" tabIndex={-1}>
      <button data-dialog-close onClick={() => setOpen(false)}>Close dialog</button>
      <button>Continue</button>
    </section>}
    <button>After dialog</button>
  </>
}

describe('DialogKeyboardManager', () => {
  it('focuses the dialog, traps Tab, closes on Escape, and restores focus', async () => {
    render(<Harness />)
    const opener = screen.getByRole('button', { name: 'Open dialog' })
    opener.focus()
    fireEvent.click(opener)
    const close = await screen.findByRole('button', { name: 'Close dialog' })
    await waitFor(() => expect(close).toHaveFocus())
    const continueButton = screen.getByRole('button', { name: 'Continue' })

    fireEvent.keyDown(continueButton, { key: 'Tab' })
    expect(close).toHaveFocus()
    fireEvent.keyDown(close, { key: 'Escape' })
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    await waitFor(() => expect(opener).toHaveFocus())
  })
})
