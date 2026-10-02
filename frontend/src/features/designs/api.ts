import { apiRequest, multipartRequest } from '../../services/apiClient'
import type { ApiPage } from '../catalog/types'
import type { Design, DesignCreateRequest, DesignReference, DesignSelection, PublishResponse, SelectionCreateRequest, ShopDesignPage } from './types'

function pageUrl(path: string, page: number, familyId?: string) {
  const url = new URL(path, window.location.origin)
  url.searchParams.set('page', String(page))
  if (familyId) url.searchParams.set('family', familyId)
  return url.pathname + url.search
}

export function getShopDesigns(shopId: string, page = 1, familyId?: string): Promise<ShopDesignPage> {
  return apiRequest<ShopDesignPage>(pageUrl(`/api/v1/shops/${shopId}/designs/`, page, familyId))
}

export function createShopDesign(shopId: string, data: DesignCreateRequest): Promise<Design> {
  return apiRequest<Design>(`/api/v1/shops/${shopId}/designs/`, { method: 'POST', body: data })
}

export function getShopDesign(shopId: string, designId: string): Promise<Design> {
  return apiRequest<Design>(`/api/v1/shops/${shopId}/designs/${designId}/`)
}

export function archiveShopDesign(shopId: string, designId: string): Promise<Design> {
  return apiRequest<Design>(`/api/v1/shops/${shopId}/designs/${designId}/`, { method: 'DELETE' })
}

export function addShopDesignSelection(shopId: string, versionId: string, data: SelectionCreateRequest): Promise<DesignSelection> {
  return apiRequest<DesignSelection>(`/api/v1/shops/${shopId}/design-versions/${versionId}/selections/`, { method: 'POST', body: data })
}

export function publishShopDesignVersion(shopId: string, versionId: string): Promise<PublishResponse> {
  return apiRequest<PublishResponse>(`/api/v1/shops/${shopId}/design-versions/${versionId}/publish/`, { method: 'POST', body: {} })
}

export function getShopDesignReferences(shopId: string, versionId: string): Promise<DesignReference[]> {
  return apiRequest<DesignReference[]>(`/api/v1/shops/${shopId}/design-versions/${versionId}/references/`)
}

export function uploadShopDesignReferences(shopId: string, versionId: string, files: File[]): Promise<DesignReference[]> {
  const formData = new FormData()
  files.forEach(file => formData.append('images', file))
  return multipartRequest<DesignReference[]>(`/api/v1/shops/${shopId}/design-versions/${versionId}/references/`, formData)
}

export async function getAllShopDesigns(shopId: string): Promise<Design[]> {
  let page = 1
  const designs: Design[] = []
  while (true) {
    const response = await apiRequest<ApiPage<Design>>(pageUrl(`/api/v1/shops/${shopId}/designs/`, page))
    designs.push(...response.results)
    if (!response.next) return designs
    page += 1
  }
}
