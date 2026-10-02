import { apiRequest, multipartRequest } from '../../services/apiClient'
import type {
  ShopDesignPage,
  Design,
  DesignCreateRequest,
  PublishResponse,
  SelectionCreateRequest,
  DesignReference
} from './types'

export async function getShopDesigns(shopId: string, page = 1, familyId?: string): Promise<ShopDesignPage> {
  const url = new URL(`/api/v1/shops/${shopId}/designs/`, window.location.origin)
  url.searchParams.set('page', page.toString())
  if (familyId) url.searchParams.set('family', familyId)
  return apiRequest<ShopDesignPage>(url.pathname + url.search)
}

export async function createShopDesign(shopId: string, data: DesignCreateRequest): Promise<Design> {
  return apiRequest<Design>(`/api/v1/shops/${shopId}/designs/`, {
    method: 'POST',
    body: data
  })
}

export async function getShopDesign(shopId: string, designId: string): Promise<Design> {
  return apiRequest<Design>(`/api/v1/shops/${shopId}/designs/${designId}/`)
}

export async function archiveShopDesign(shopId: string, designId: string): Promise<void> {
  return apiRequest(`/api/v1/shops/${shopId}/designs/${designId}/`, { method: 'DELETE' })
}

export async function publishShopDesignVersion(shopId: string, versionId: string): Promise<PublishResponse> {
  return apiRequest<PublishResponse>(`/api/v1/shops/${shopId}/design-versions/${versionId}/publish/`, { method: 'POST', body: {} })
}

export async function addShopDesignSelection(shopId: string, versionId: string, data: SelectionCreateRequest): Promise<any> {
  return apiRequest(`/api/v1/shops/${shopId}/design-versions/${versionId}/selections/`, { method: 'POST', body: data })
}

export async function uploadShopDesignReference(shopId: string, versionId: string, file: File): Promise<DesignReference[]> {
  const formData = new FormData()
  formData.append('file', file)
  return multipartRequest<DesignReference[]>(`/api/v1/shops/${shopId}/design-versions/${versionId}/references/`, formData)
}
