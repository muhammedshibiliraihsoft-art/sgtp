import { apiRequest, multipartRequest } from '../../services/apiClient'
import type { ApiPage } from '../../features/catalog/types'
import type { Design, DesignCreateRequest, DesignReference, DesignSelection, PublishResponse, SelectionCreateRequest, ShopDesignPage } from '../../features/designs/types'

const basePath = '/api/v1/catalog/design-templates/'

export function getGlobalDesigns(page = 1, familyId?: string, locale = 'en'): Promise<ShopDesignPage> {
  const url = new URL(basePath, window.location.origin)
  url.searchParams.set('page', String(page))
  url.searchParams.set('locale', locale)
  if (familyId) url.searchParams.set('family', familyId)
  return apiRequest<ShopDesignPage>(url.pathname + url.search)
}

export async function getAllGlobalDesigns(familyId?: string, locale = 'en'): Promise<Design[]> {
  const designs: Design[] = []
  let page = 1
  while (true) {
    const response = await getGlobalDesigns(page, familyId, locale)
    designs.push(...response.results)
    if (!response.next) return designs
    page += 1
  }
}

export function createGlobalDesign(data: DesignCreateRequest): Promise<Design> {
  return apiRequest<Design>(basePath, { method: 'POST', body: data })
}

export async function getGlobalDesign(designId: string): Promise<Design> {
  const design = (await getAllGlobalDesigns()).find(item => item.id === designId)
  if (!design) throw new Error('Design template not found.')
  return design
}

export function archiveGlobalDesign(designId: string): Promise<Design> {
  return apiRequest<Design>(`${basePath}${designId}/archive/`, { method: 'POST', body: {} })
}

export function addGlobalDesignSelection(designId: string, versionId: string, data: SelectionCreateRequest): Promise<DesignSelection> {
  return apiRequest<DesignSelection>(`${basePath}${designId}/versions/${versionId}/selections/`, { method: 'POST', body: data })
}

export function publishGlobalDesignVersion(designId: string, versionId: string): Promise<PublishResponse> {
  return apiRequest<PublishResponse>(`${basePath}${designId}/versions/${versionId}/publish/`, { method: 'POST', body: {} })
}

export function getGlobalDesignReferences(designId: string, versionId: string): Promise<DesignReference[]> {
  return apiRequest<DesignReference[]>(`${basePath}${designId}/versions/${versionId}/references/`)
}

export function uploadGlobalDesignReferences(designId: string, versionId: string, files: File[]): Promise<DesignReference[]> {
  const formData = new FormData()
  files.forEach(file => formData.append('images', file))
  return multipartRequest<DesignReference[]>(`${basePath}${designId}/versions/${versionId}/references/`, formData)
}

export async function getGlobalDesignPage(page = 1): Promise<ApiPage<Design>> {
  return getGlobalDesigns(page)
}
