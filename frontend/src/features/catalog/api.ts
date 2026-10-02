import { apiRequest, multipartRequest } from '../../services/apiClient'
import type {
  ApiPage,
  CatalogFamily,
  CatalogFamilyPage,
  CatalogOptionGroupPage,
  OptionGroup,
  ShopStyleOptionInputRequest,
  ShopStyleOptionPage,
  ShopVariantInputRequest,
  ShopVariantPage,
  StyleImage,
  StyleOption,
  Variant,
} from './types'

async function getAllPages<T>(path: string): Promise<T[]> {
  let current = new URL(path, window.location.origin)
  const results: T[] = []
  while (true) {
    const page = await apiRequest<ApiPage<T>>(current.pathname + current.search)
    results.push(...page.results)
    if (!page.next) return results
    const next = new URL(page.next, window.location.origin)
    current = new URL(next.pathname + next.search, window.location.origin)
  }
}

export async function getFamilies(page = 1): Promise<CatalogFamilyPage> {
  return apiRequest<CatalogFamilyPage>(`/api/v1/catalog/families/?page=${page}`)
}

export function getAllFamilies(): Promise<CatalogFamily[]> {
  return getAllPages<CatalogFamily>('/api/v1/catalog/families/')
}

export async function getOptionGroups(familyId?: string): Promise<OptionGroup[]> {
  if (familyId) {
    return apiRequest<OptionGroup[]>(`/api/v1/catalog/families/${familyId}/option-groups/`)
  }
  return getAllPages<OptionGroup>('/api/v1/catalog/option-groups/')
}

export async function getShopVariants(shopId: string, page = 1, familyId?: string): Promise<ShopVariantPage> {
  const url = new URL(`/api/v1/shops/${shopId}/catalog/variants/`, window.location.origin)
  url.searchParams.set('page', page.toString())
  if (familyId) url.searchParams.set('family', familyId)
  return apiRequest<ShopVariantPage>(url.pathname + url.search)
}

export function getAllShopVariants(shopId: string, familyId?: string): Promise<Variant[]> {
  const url = new URL(`/api/v1/shops/${shopId}/catalog/variants/`, window.location.origin)
  if (familyId) url.searchParams.set('family', familyId)
  return getAllPages<Variant>(url.pathname + url.search)
}

export async function createShopVariant(shopId: string, data: ShopVariantInputRequest): Promise<Variant> {
  return apiRequest<Variant>(`/api/v1/shops/${shopId}/catalog/variants/`, {
    method: 'POST',
    body: data,
  })
}

export async function getShopStyleOptions(shopId: string, page = 1, groupId?: string): Promise<ShopStyleOptionPage> {
  const url = new URL(`/api/v1/shops/${shopId}/catalog/style-options/`, window.location.origin)
  url.searchParams.set('page', page.toString())
  if (groupId) url.searchParams.set('option_group', groupId)
  return apiRequest<ShopStyleOptionPage>(url.pathname + url.search)
}

export function getAllShopStyleOptions(shopId: string): Promise<StyleOption[]> {
  return getAllPages<StyleOption>(`/api/v1/shops/${shopId}/catalog/style-options/`)
}

export async function createShopStyleOption(shopId: string, data: ShopStyleOptionInputRequest): Promise<StyleOption> {
  return apiRequest<StyleOption>(`/api/v1/shops/${shopId}/catalog/style-options/`, {
    method: 'POST',
    body: data,
  })
}

export async function toggleShopStyleOptionActive(shopId: string, optionId: string, is_active: boolean): Promise<StyleOption> {
  return apiRequest<StyleOption>(`/api/v1/shops/${shopId}/catalog/style-options/${optionId}/`, {
    method: 'PATCH',
    body: { is_active },
  })
}

export async function uploadShopStyleOptionImages(shopId: string, optionId: string, files: File[]): Promise<StyleImage[]> {
  const formData = new FormData()
  files.forEach(file => formData.append('images', file))
  return multipartRequest<StyleImage[]>(`/api/v1/shops/${shopId}/catalog/style-options/${optionId}/reference-images/`, formData)
}

export async function getGlobalStyleOptions(page = 1): Promise<ShopStyleOptionPage> {
  return apiRequest<ShopStyleOptionPage>(`/api/v1/catalog/style-options/?page=${page}`)
}

export function getAllGlobalStyleOptions(): Promise<StyleOption[]> {
  return getAllPages<StyleOption>('/api/v1/catalog/style-options/')
}

export async function createGlobalStyleOption(data: ShopStyleOptionInputRequest): Promise<StyleOption> {
  return apiRequest<StyleOption>('/api/v1/catalog/style-options/', { method: 'POST', body: data })
}

export async function toggleGlobalStyleOptionActive(optionId: string, is_active: boolean): Promise<StyleOption> {
  return apiRequest<StyleOption>(`/api/v1/catalog/style-options/${optionId}/`, {
    method: 'PATCH',
    body: { is_active },
  })
}

export async function uploadGlobalStyleOptionImages(optionId: string, files: File[]): Promise<StyleImage[]> {
  const formData = new FormData()
  files.forEach(file => formData.append('images', file))
  return multipartRequest<StyleImage[]>(`/api/v1/catalog/style-options/${optionId}/reference-images/`, formData)
}

export async function getGlobalFamiliesPage(page = 1): Promise<CatalogFamilyPage> {
  return getFamilies(page)
}

export async function getGlobalOptionGroupsPage(page = 1): Promise<CatalogOptionGroupPage> {
  return apiRequest<CatalogOptionGroupPage>(`/api/v1/catalog/option-groups/?page=${page}`)
}

export async function updateFamilyOptionGroups(familyId: string, optionGroupIds: string[]): Promise<OptionGroup[]> {
  return apiRequest<OptionGroup[]>(`/api/v1/catalog/families/${familyId}/option-groups/`, {
    method: 'PUT',
    body: { option_group_ids: optionGroupIds },
  })
}
