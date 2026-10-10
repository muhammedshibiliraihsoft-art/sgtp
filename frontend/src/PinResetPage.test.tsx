import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { PinResetPage } from './PinResetPage'
import { pinResetService } from './services/pinReset'
import './i18n'

afterEach(() => { cleanup(); vi.restoreAllMocks() })

describe('Shop Admin PIN reset request page', () => {
  it('shows only the generic result after a phone request', async () => {
    const request = vi.spyOn(pinResetService, 'request').mockResolvedValue({ detail: 'generic' })
    render(<BrowserRouter><PinResetPage /></BrowserRouter>)
    fireEvent.change(screen.getByLabelText('Registered phone number'), { target: { value: '+96550000102' } })
    fireEvent.click(screen.getByRole('button', { name: 'Request recovery' }))
    await waitFor(() => expect(request).toHaveBeenCalledWith('+96550000102'))
    expect(await screen.findByRole('status')).toHaveTextContent('If this Shop Admin account is eligible')
    expect(screen.queryByText(/account exists/i)).not.toBeInTheDocument()
  })

  it('retains input and shows a safe failure', async () => {
    vi.spyOn(pinResetService, 'request').mockRejectedValue(new Error('private backend detail'))
    render(<BrowserRouter><PinResetPage /></BrowserRouter>)
    fireEvent.change(screen.getByLabelText('Registered phone number'), { target: { value: '+96550000102' } })
    fireEvent.click(screen.getByRole('button', { name: 'Request recovery' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to submit')
    expect(screen.getByLabelText('Registered phone number')).toHaveValue('+96550000102')
    expect(screen.queryByText('private backend detail')).not.toBeInTheDocument()
  })

  it('rejects malformed numbers locally and does not call the API', async () => {
    const request = vi.spyOn(pinResetService, 'request')
    render(<BrowserRouter><PinResetPage /></BrowserRouter>)
    fireEvent.change(screen.getByLabelText('Registered phone number'), { target: { value: '50000102' } })
    fireEvent.click(screen.getByRole('button', { name: 'Request recovery' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('international phone number')
    expect(request).not.toHaveBeenCalled()
    expect(screen.getByLabelText('Registered phone number')).toHaveValue('50000102')
  })

  it('does not send duplicate requests on rapid repeated submit', async () => {
    let finishRequest!: (value: { detail: string }) => void
    const request = vi.spyOn(pinResetService, 'request').mockReturnValue(new Promise(resolve => { finishRequest = resolve }))
    render(<BrowserRouter><PinResetPage /></BrowserRouter>)
    fireEvent.change(screen.getByLabelText('Registered phone number'), { target: { value: '+96550000102' } })
    const form = screen.getByLabelText('Registered phone number').closest('form')!
    fireEvent.submit(form)
    fireEvent.submit(form)
    expect(request).toHaveBeenCalledTimes(1)
    finishRequest({ detail: 'generic' })
    expect(await screen.findByRole('status')).toHaveTextContent('If this Shop Admin account is eligible')
  })
})
