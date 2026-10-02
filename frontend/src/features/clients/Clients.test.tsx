import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ClientsPage } from './ClientsPage'
import { ClientDetailPage } from './ClientDetailPage'

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key })
}))

describe('Clients Module', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    cleanup()
  })
  afterEach(() => {
    cleanup()
  })

  describe('ClientsPage', () => {
    beforeEach(() => {
      render(
        <MemoryRouter>
          <ClientsPage />
        </MemoryRouter>
      )
    })

    it('renders the clients page title and add client CTA', () => {
      expect(screen.getByText('clients.title')).toBeInTheDocument()
      expect(screen.getAllByText('clients.addClient').length).toBeGreaterThan(0)
    })

    it('renders the mock clients list (first page)', () => {
      expect(screen.getAllByText('Ahmed Al-Rashid').length).toBeGreaterThan(0)
    })

    it('filters clients via search', () => {
      const searchInput = screen.getByPlaceholderText('clients.searchPlaceholder')
      fireEvent.change(searchInput, { target: { value: 'Zainab' } })
      
      expect(screen.getAllByText('Zainab Hussein').length).toBeGreaterThan(0)
      expect(screen.queryByText('Ahmed Al-Rashid')).not.toBeInTheDocument()
    })

    it('opens add client form', () => {
      const addBtns = screen.getAllByText('clients.addClient')
      fireEvent.click(addBtns[0])
      expect(screen.getByLabelText('clients.name *')).toBeInTheDocument()
    })
  })

  describe('ClientDetailPage', () => {
    beforeEach(() => {
      render(
        <MemoryRouter initialEntries={['/clients/c1']}>
          <Routes>
            <Route path="/clients/:clientId" element={<ClientDetailPage />} />
          </Routes>
        </MemoryRouter>
      )
    })

    it('renders the client metadata', () => {
      expect(screen.getAllByText('clients.phone').length).toBeGreaterThan(0)
      expect(screen.getAllByText('clients.email').length).toBeGreaterThan(0)
      expect(screen.getByText('clients.relatedPersons')).toBeInTheDocument()
    })

    it('opens add related person form', () => {
      const addRpBtn = screen.getAllByText('clients.addRelatedPerson')[0]
      fireEvent.click(addRpBtn)
      expect(screen.getAllByText('clients.name *').length).toBeGreaterThan(0)
    })
  })
})
