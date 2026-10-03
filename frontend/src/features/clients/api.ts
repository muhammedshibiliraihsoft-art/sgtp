import { apiRequest } from '../../services/apiClient'
import type { Client, PaginatedResponse, RelatedPerson } from './types'

export type ContactInput = { name: string; phone?: string; email?: string }
export type ContactWriteResult<T> = T & {
  warnings?: { code: 'possible_duplicate'; field: 'phone' | 'email'; matches: { id: string; name: string }[] }[]
}

const base = (shopId: string) => `/api/v1/shops/${encodeURIComponent(shopId)}/clients/`
const contactBody = (input: ContactInput) => ({ name: input.name.trim(), phone: input.phone?.trim() ?? '', email: input.email?.trim() ?? '' })

export const clientsApi = {
  list(shopId: string, search: string, page: number) {
    const query = new URLSearchParams()
    if (search.trim()) query.set('search', search.trim())
    if (page > 1) query.set('page', String(page))
    return apiRequest<PaginatedResponse<Client>>(`${base(shopId)}${query.size ? `?${query}` : ''}`)
  },
  detail(shopId: string, clientId: string) {
    return apiRequest<Client>(`${base(shopId)}${encodeURIComponent(clientId)}/`)
  },
  create(shopId: string, input: ContactInput) {
    return apiRequest<ContactWriteResult<Client>>(base(shopId), { method: 'POST', body: contactBody(input) })
  },
  update(shopId: string, clientId: string, input: ContactInput) {
    return apiRequest<ContactWriteResult<Client>>(`${base(shopId)}${encodeURIComponent(clientId)}/`, { method: 'PATCH', body: contactBody(input) })
  },
  remove(shopId: string, clientId: string) {
    return apiRequest<void>(`${base(shopId)}${encodeURIComponent(clientId)}/`, { method: 'DELETE' })
  },
  related(shopId: string, clientId: string) {
    return apiRequest<PaginatedResponse<RelatedPerson>>(`${base(shopId)}${encodeURIComponent(clientId)}/related-persons/`)
  },
  createRelated(shopId: string, clientId: string, input: ContactInput) {
    return apiRequest<ContactWriteResult<RelatedPerson>>(`${base(shopId)}${encodeURIComponent(clientId)}/related-persons/`, { method: 'POST', body: contactBody(input) })
  },
  updateRelated(shopId: string, clientId: string, personId: string, input: ContactInput) {
    return apiRequest<ContactWriteResult<RelatedPerson>>(`${base(shopId)}${encodeURIComponent(clientId)}/related-persons/${encodeURIComponent(personId)}/`, { method: 'PATCH', body: contactBody(input) })
  },
  removeRelated(shopId: string, clientId: string, personId: string) {
    return apiRequest<void>(`${base(shopId)}${encodeURIComponent(clientId)}/related-persons/${encodeURIComponent(personId)}/`, { method: 'DELETE' })
  },
}
