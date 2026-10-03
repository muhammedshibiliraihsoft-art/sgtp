import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ClientsPage } from './ClientsPage'
import { ClientDetailPage } from './ClientDetailPage'
import { clientsApi } from './api'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key: string) => key }) }))
vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => ({ shopId:'shop-1', role:'ADMIN', isLoading:false }) }))
vi.mock('./api', () => ({ clientsApi: { list:vi.fn(), detail:vi.fn(), create:vi.fn(), update:vi.fn(), remove:vi.fn(), related:vi.fn(), createRelated:vi.fn(), updateRelated:vi.fn(), removeRelated:vi.fn() } }))

const client = { id:'client-uuid', name:'Ahmed Al-Rashid', phone:'+97412345678', phone_normalized:'+97412345678', email:'ahmed@example.test', created_at:'2026-01-01T00:00:00Z', updated_at:'2026-01-02T00:00:00Z' }
const related = { id:'person-uuid', name:'Zainab Hussein', phone:'', phone_normalized:'', email:'', created_at:'2026-01-01T00:00:00Z', updated_at:'2026-01-02T00:00:00Z', primary_client_id:client.id }

describe('Clients module API integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(clientsApi.list).mockResolvedValue({ count:1,next:null,previous:null,results:[client] })
    vi.mocked(clientsApi.detail).mockResolvedValue(client)
    vi.mocked(clientsApi.related).mockResolvedValue({ count:1,next:null,previous:null,results:[related] })
  })
  afterEach(cleanup)

  it('loads the Shop-scoped backend client page and supports server search', async () => {
    render(<MemoryRouter><ClientsPage /></MemoryRouter>)
    expect((await screen.findAllByText(client.name)).length).toBeGreaterThan(0)
    expect(clientsApi.list).toHaveBeenCalledWith('shop-1','',1)
    fireEvent.change(screen.getByPlaceholderText('clients.searchPlaceholder'), { target:{ value:'Zainab' } })
    await waitFor(() => expect(clientsApi.list).toHaveBeenLastCalledWith('shop-1','Zainab',1))
  })

  it('opens the create form only after loading live data', async () => {
    render(<MemoryRouter><ClientsPage /></MemoryRouter>)
    fireEvent.click(await screen.findByText('clients.addClient'))
    expect(screen.getByLabelText('clients.name *')).toBeInTheDocument()
  })

  it('loads real client and Related Person records for the detail view', async () => {
    render(<MemoryRouter initialEntries={[`/clients/${client.id}`]}><Routes><Route path="/clients/:clientId" element={<ClientDetailPage />} /></Routes></MemoryRouter>)
    expect(await screen.findByRole('heading', { name:client.name })).toBeInTheDocument()
    expect(screen.getByText('Zainab Hussein')).toBeInTheDocument()
    expect(clientsApi.detail).toHaveBeenCalledWith('shop-1',client.id)
    expect(clientsApi.related).toHaveBeenCalledWith('shop-1',client.id)
  })
})
