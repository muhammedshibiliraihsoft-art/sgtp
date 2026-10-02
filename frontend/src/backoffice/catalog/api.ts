import { apiRequest, multipartRequest } from '../../services/apiClient'
import type { CatalogFamilyPage, CatalogFamily, OptionGroup, CatalogOptionGroupPage, ShopStyleOptionPage, StyleOption, ShopStyleOptionInputRequest, StyleImage } from '../../features/catalog/types'

export async function getGlobalFamilies(page = 1): Promise<CatalogFamilyPage> {
  return apiRequest<CatalogFamilyPage>(`/api/v1/catalog/families/?page=${page}`)
}

export async function createGlobalFamily(data: { name: string, code?: string, description?: string }): Promise<CatalogFamily> {
  return apiRequest<CatalogFamily>(`/api/v1/catalog/families/`, {
    method: 'POST', body: data
  })
}

export async function getGlobalOptionGroups(familyId?: string): Promise<OptionGroup[]> {
  if (familyId) {
    return apiRequest<OptionGroup[]>(`/api/v1/catalog/families/${familyId}/option-groups/`)
  }
  const page = await apiRequest<CatalogOptionGroupPage>(`/api/v1/catalog/option-groups/`)
  return page.results // Note: schema says it's paginated, but frontend may need all. Let's return results.
}

export async function createGlobalOptionGroup(familyId: string, data: { name: string, code?: string, description?: string }): Promise<OptionGroup> {
  return apiRequest<OptionGroup>(`/api/v1/catalog/families/${familyId}/option-groups/`, {
    method: 'POST', body: data
  })
}

export async function getGlobalStyleOptions(page = 1): Promise<ShopStyleOptionPage> {
  return apiRequest<ShopStyleOptionPage>(`/api/v1/catalog/style-options/?page=${page}`)
}

export async function createGlobalStyleOption(data: ShopStyleOptionInputRequest): Promise<StyleOption> {
  return apiRequest<StyleOption>(`/api/v1/catalog/style-options/`, {
    method: 'POST', body: data
  })
}

export async function toggleGlobalStyleOptionActive(optionId: string, is_active: boolean): Promise<StyleOption> {
  return apiRequest<StyleOption>(`/api/v1/catalog/style-options/${optionId}/`, {
    method: 'PATCH', body: { is_active }
  })
}

export async function uploadGlobalStyleOptionImage(optionId: string, file: File): Promise<StyleImage[]> {
  const formData = new FormData()
  formData.append('file', file)
  return multipartRequest<StyleImage[]>(`/api/v1/catalog/style-options/${optionId}/reference-images/`, formData)
}
