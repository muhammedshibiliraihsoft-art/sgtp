import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ClientsPage } from './ClientsPage'
import { ClientDetailPage } from './ClientDetailPage'
import { clientsApi } from './api'
import * as catalogApi from '../catalog/api'
import { measurementApi } from '../measurements/api'

const i18nMock = vi.hoisted(() => ({ resolvedLanguage: 'en', t: (key: string) => key }))
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: i18nMock.t, i18n: i18nMock }) }))
vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => ({ shopId:'shop-1', role:'ADMIN', isLoading:false }) }))
vi.mock('./api', () => ({ clientsApi: { list:vi.fn(), detail:vi.fn(), create:vi.fn(), update:vi.fn(), remove:vi.fn(), related:vi.fn(), relatedAll:vi.fn(), createRelated:vi.fn(), updateRelated:vi.fn(), removeRelated:vi.fn() } }))

const client = { id:'client-uuid', name:'Ahmed Al-Rashid', phone:'+97412345678', phone_normalized:'+97412345678', email:'ahmed@example.test', created_at:'2026-01-01T00:00:00Z', updated_at:'2026-01-02T00:00:00Z' }
const related = { id:'person-uuid', name:'Zainab Hussein', phone:'', phone_normalized:'', email:'', created_at:'2026-01-01T00:00:00Z', updated_at:'2026-01-02T00:00:00Z', primary_client_id:client.id }

describe('Clients module API integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(clientsApi.list).mockResolvedValue({ count:1,next:null,previous:null,results:[client] })
    vi.mocked(clientsApi.detail).mockResolvedValue(client)
    vi.mocked(clientsApi.related).mockResolvedValue({ count:1,next:null,previous:null,results:[related] })
    vi.mocked(clientsApi.relatedAll).mockResolvedValue([related])
  })
  afterEach(() => { cleanup(); vi.restoreAllMocks() })

  it('loads the Shop-scoped backend client page and supports server search', async () => {
    render(<MemoryRouter><ClientsPage /></MemoryRouter>)
    expect((await screen.findAllByText(client.name)).length).toBeGreaterThan(0)
    expect(clientsApi.list).toHaveBeenCalledWith('shop-1','',1)
    fireEvent.change(screen.getByPlaceholderText('clients.searchPlaceholder'), { target:{ value:'Zainab' } })
    await waitFor(() => expect(clientsApi.list).toHaveBeenLastCalledWith('shop-1','Zainab',1))
  })

  it('debounces rapid search input to one request and keeps the final query', async () => {
    render(<MemoryRouter><ClientsPage /></MemoryRouter>)
    expect((await screen.findAllByText(client.name)).length).toBeGreaterThan(0)
    vi.mocked(clientsApi.list).mockClear()
    const search = screen.getByPlaceholderText('clients.searchPlaceholder')
    fireEvent.change(search, { target: { value: 'Z' } })
    fireEvent.change(search, { target: { value: 'Za' } })
    fireEvent.change(search, { target: { value: 'Zainab' } })
    await waitFor(() => expect(clientsApi.list).toHaveBeenCalledTimes(1))
    expect(clientsApi.list).toHaveBeenCalledWith('shop-1', 'Zainab', 1)
  })

  it('opens the create form only after loading live data', async () => {
    render(<MemoryRouter><ClientsPage /></MemoryRouter>)
    fireEvent.click(await screen.findByText('clients.addClient'))
    expect(screen.getByLabelText('clients.name *')).toBeInTheDocument()
  })

  it('loads client and Related Person measurement history for the detail view', async () => {
    vi.spyOn(catalogApi, 'getAllFamilies').mockResolvedValue([{ id:'family-1', code:'abaya', name:'Abaya' }])
    vi.spyOn(measurementApi, 'profiles').mockImplementation(async (_shopId, _clientId, owner) => owner.kind === 'related_person'
      ? [{ id:'profile-1', client:null, related_person:related.id, family:'family-1', variant:null, created_at:'2026-01-01T00:00:00Z' }]
      : [])
    vi.spyOn(measurementApi, 'sets').mockResolvedValue([{ id:'set-1', profile:'profile-1', version:1, copied_from:null, created_at:'2026-01-03T00:00:00Z', values:[] }])
    render(<MemoryRouter initialEntries={[`/clients/${client.id}`]}><Routes><Route path="/clients/:clientId" element={<ClientDetailPage />} /></Routes></MemoryRouter>)
    expect(await screen.findByRole('heading', { name:client.name })).toBeInTheDocument()
    expect(await screen.findByText('Zainab Hussein')).toBeInTheDocument()
    expect(screen.getByText('Abaya')).toBeInTheDocument()
    expect(clientsApi.detail).toHaveBeenCalledWith('shop-1',client.id)
    expect(clientsApi.relatedAll).toHaveBeenCalledWith('shop-1',client.id)
    expect(measurementApi.profiles).toHaveBeenCalledWith('shop-1', client.id, { kind:'related_person', id:related.id })
  })
})
