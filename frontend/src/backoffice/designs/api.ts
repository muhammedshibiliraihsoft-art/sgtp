import { apiRequest, multipartRequest } from '../../services/apiClient'
import type { ShopDesignPage, Design, DesignReference, DesignCreateRequest, SelectionCreateRequest, PublishResponse } from '../../features/designs/types'

export async function getGlobalDesigns(page = 1, familyId?: string): Promise<ShopDesignPage> {
  const url = new URL(`/api/v1/catalog/design-templates/`, window.location.origin)
  url.searchParams.set('page', page.toString())
  if (familyId) url.searchParams.set('family', familyId)
  return apiRequest<ShopDesignPage>(url.pathname + url.search)
}

export async function createGlobalDesign(data: DesignCreateRequest): Promise<Design> {
  return apiRequest<Design>(`/api/v1/catalog/design-templates/`, {
    method: 'POST', body: data
  })
}

export async function getGlobalDesign(designId: string): Promise<Design> {
  return apiRequest<Design>(`/api/v1/catalog/design-templates/${designId}/`)
}

export async function archiveGlobalDesign(designId: string): Promise<void> {
  return apiRequest(`/api/v1/catalog/design-templates/${designId}/archive/`, { method: 'POST', body: {} })
}

export async function publishGlobalDesignVersion(designId: string, versionId: string): Promise<PublishResponse> {
  return apiRequest<PublishResponse>(`/api/v1/catalog/design-templates/${designId}/versions/${versionId}/publish/`, { method: 'POST', body: {} })
}

export async function addGlobalDesignSelection(designId: string, versionId: string, data: SelectionCreateRequest): Promise<any> {
  return apiRequest(`/api/v1/catalog/design-templates/${designId}/versions/${versionId}/selections/`, { method: 'POST', body: data })
}

export async function uploadGlobalDesignReference(designId: string, versionId: string, file: File): Promise<DesignReference[]> {
  const formData = new FormData()
  formData.append('file', file)
  return multipartRequest<DesignReference[]>(`/api/v1/catalog/design-templates/${designId}/versions/${versionId}/references/`, formData)
}
