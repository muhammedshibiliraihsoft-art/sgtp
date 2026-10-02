import { apiRequest, multipartRequest } from '../../services/apiClient'
import type { 
  CatalogFamilyPage, 
  OptionGroup, 
  ShopVariantPage, 
  ShopVariantInputRequest, 
  Variant,
  ShopStyleOptionPage,
  ShopStyleOptionInputRequest,
  StyleOption,
  StyleImage
} from './types'

// Shop Catalog API

export async function getFamilies(page = 1): Promise<CatalogFamilyPage> {
  return apiRequest<CatalogFamilyPage>(`/api/v1/catalog/families/?page=${page}`)
}

export async function getOptionGroups(familyId: string): Promise<OptionGroup[]> {
  return apiRequest<OptionGroup[]>(`/api/v1/catalog/families/${familyId}/option-groups/`)
}

export async function getShopVariants(shopId: string, page = 1, familyId?: string): Promise<ShopVariantPage> {
  const url = new URL(`/api/v1/shops/${shopId}/catalog/variants/`, window.location.origin)
  url.searchParams.set('page', page.toString())
  if (familyId) url.searchParams.set('family', familyId)
  return apiRequest<ShopVariantPage>(url.pathname + url.search)
}

export async function createShopVariant(shopId: string, data: ShopVariantInputRequest): Promise<Variant> {
  return apiRequest<Variant>(`/api/v1/shops/${shopId}/catalog/variants/`, {
    method: 'POST',
    body: data
  })
}

export async function getShopStyleOptions(shopId: string, page = 1, groupId?: string): Promise<ShopStyleOptionPage> {
  const url = new URL(`/api/v1/shops/${shopId}/catalog/style-options/`, window.location.origin)
  url.searchParams.set('page', page.toString())
  if (groupId) url.searchParams.set('group', groupId)
  return apiRequest<ShopStyleOptionPage>(url.pathname + url.search)
}

export async function createShopStyleOption(shopId: string, data: ShopStyleOptionInputRequest): Promise<StyleOption> {
  return apiRequest<StyleOption>(`/api/v1/shops/${shopId}/catalog/style-options/`, {
    method: 'POST',
    body: data
  })
}

export async function toggleShopStyleOptionActive(shopId: string, optionId: string, is_active: boolean): Promise<StyleOption> {
  return apiRequest<StyleOption>(`/api/v1/shops/${shopId}/catalog/style-options/${optionId}/`, {
    method: 'PATCH',
    body: { is_active }
  })
}

export async function uploadShopStyleOptionImage(shopId: string, optionId: string, file: File): Promise<StyleImage[]> {
  const formData = new FormData()
  formData.append('file', file)
  return multipartRequest<StyleImage[]>(`/api/v1/shops/${shopId}/catalog/style-options/${optionId}/reference-images/`, formData)
}
