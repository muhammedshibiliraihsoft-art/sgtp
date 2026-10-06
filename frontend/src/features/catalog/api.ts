import { apiRequest, multipartRequest } from '../../services/apiClient'
import { uploadPrivateMediaBatch } from '../../services/privateMediaUpload'
import type {
  ApiPage,
  CatalogFamily,
  CatalogFamilyDetail,
  CatalogFamilyImageMetadata,
  CatalogFamilyInput,
  CatalogFamilyPage,
  CatalogOptionGroupPage,
  OptionGroup,
  ShopStyleOptionInputRequest,
  ShopStyleOptionPage,
  ShopVariantInputRequest,
  ShopVariantPage,
  TranslationInput,
  StyleImage,
  StyleOption,
  Variant,
  VariantDetail,
  VariantQuery,
  VariantStatus,
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

export async function getFamilies(page = 1, search = '', status: 'ACTIVE' | 'ARCHIVED' | 'all' = 'ACTIVE'): Promise<CatalogFamilyPage> {
  const url = new URL('/api/v1/catalog/families/', window.location.origin)
  url.searchParams.set('page', String(page))
  url.searchParams.set('status', status)
  if (search.trim()) url.searchParams.set('search', search.trim())
  return apiRequest<CatalogFamilyPage>(url.pathname + url.search)
}

export function getAllFamilies(locale = 'en'): Promise<CatalogFamily[]> {
  const url = new URL('/api/v1/catalog/families/', window.location.origin)
  url.searchParams.set('locale', locale)
  return getAllPages<CatalogFamily>(url.pathname + url.search)
}

export async function getOptionGroups(familyId?: string, locale = 'en'): Promise<OptionGroup[]> {
  if (familyId) {
    return apiRequest<OptionGroup[]>(`/api/v1/catalog/families/${familyId}/option-groups/?locale=${encodeURIComponent(locale)}`)
  }
  return getAllPages<OptionGroup>(`/api/v1/catalog/option-groups/?locale=${encodeURIComponent(locale)}`)
}

export async function getShopVariants(shopId: string, page = 1, familyId?: string): Promise<ShopVariantPage> {
  const url = new URL(`/api/v1/shops/${shopId}/catalog/variants/`, window.location.origin)
  url.searchParams.set('page', page.toString())
  if (familyId) url.searchParams.set('family', familyId)
  return apiRequest<ShopVariantPage>(url.pathname + url.search)
}

function variantQueryUrl(path: string, query: VariantQuery = {}) {
  const url = new URL(path, window.location.origin)
  url.searchParams.set('page', String(query.page ?? 1))
  if (query.family) url.searchParams.set('family', query.family)
  if (query.search?.trim()) url.searchParams.set('search', query.search.trim())
  if (query.status && query.status !== 'ACTIVE') url.searchParams.set('status', query.status)
  if (query.source && query.source !== 'all') url.searchParams.set('source', query.source)
  return url.pathname + url.search
}

export function getShopVariantsPage(shopId: string, query: VariantQuery = {}): Promise<ShopVariantPage> {
  return apiRequest<ShopVariantPage>(variantQueryUrl(`/api/v1/shops/${shopId}/catalog/variants/`, query))
}

export function getGlobalVariantsPage(query: VariantQuery = {}): Promise<ShopVariantPage> {
  return apiRequest<ShopVariantPage>(variantQueryUrl('/api/v1/catalog/variants/', { ...query, source: undefined }))
}

export function getShopVariant(shopId: string, variantId: string): Promise<VariantDetail> {
  return apiRequest<VariantDetail>(`/api/v1/shops/${shopId}/catalog/variants/${variantId}/`)
}

export function updateShopVariant(shopId: string, variantId: string, translations: TranslationInput[]): Promise<VariantDetail> {
  return apiRequest<VariantDetail>(`/api/v1/shops/${shopId}/catalog/variants/${variantId}/`, { method: 'PATCH', body: { translations } })
}

export function setShopVariantStatus(shopId: string, variantId: string, active: boolean): Promise<VariantDetail> {
  return apiRequest<VariantDetail>(`/api/v1/shops/${shopId}/catalog/variants/${variantId}/${active ? 'reactivate' : 'archive'}/`, { method: 'POST', body: {} })
}

export function getGlobalVariant(variantId: string): Promise<VariantDetail> {
  return apiRequest<VariantDetail>(`/api/v1/catalog/variants/${variantId}/`)
}

export function createGlobalVariant(data: ShopVariantInputRequest): Promise<VariantDetail> {
  return apiRequest<VariantDetail>('/api/v1/catalog/variants/', { method: 'POST', body: data })
}

export function updateGlobalVariant(variantId: string, translations: TranslationInput[]): Promise<VariantDetail> {
  return apiRequest<VariantDetail>(`/api/v1/catalog/variants/${variantId}/`, { method: 'PATCH', body: { translations } })
}

export function setGlobalVariantStatus(variantId: string, active: boolean): Promise<VariantDetail> {
  return apiRequest<VariantDetail>(`/api/v1/catalog/variants/${variantId}/${active ? 'reactivate' : 'archive'}/`, { method: 'POST', body: {} })
}

export function setGlobalVariantDefault(variantId: string): Promise<VariantDetail> {
  return apiRequest<VariantDetail>(`/api/v1/catalog/variants/${variantId}/set-default/`, { method: 'POST', body: {} })
}

export function getAllShopVariants(shopId: string, familyId?: string, locale = 'en', status?: VariantStatus): Promise<Variant[]> {
  const url = new URL(`/api/v1/shops/${shopId}/catalog/variants/`, window.location.origin)
  if (familyId) url.searchParams.set('family', familyId)
  url.searchParams.set('locale', locale)
  if (status && status !== 'ACTIVE') url.searchParams.set('status', status)
  return getAllPages<Variant>(url.pathname + url.search)
}

export function getAllGlobalVariants(familyId?: string, locale = 'en', status?: VariantStatus): Promise<Variant[]> {
  const url = new URL('/api/v1/catalog/variants/', window.location.origin)
  if (familyId) url.searchParams.set('family', familyId)
  url.searchParams.set('locale', locale)
  if (status && status !== 'ACTIVE') url.searchParams.set('status', status)
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

export function getAllShopStyleOptions(shopId: string, groupId?: string, locale = 'en'): Promise<StyleOption[]> {
  const url = new URL(`/api/v1/shops/${shopId}/catalog/style-options/`, window.location.origin)
  if (groupId) url.searchParams.set('option_group', groupId)
  url.searchParams.set('locale', locale)
  return getAllPages<StyleOption>(url.pathname + url.search)
}

export async function createShopStyleOption(shopId: string, data: ShopStyleOptionInputRequest): Promise<StyleOption> {
  return apiRequest<StyleOption>(`/api/v1/shops/${shopId}/catalog/style-options/`, {
    method: 'POST',
    body: data,
  })
}

export async function updateShopStyleOptionTranslations(shopId: string, optionId: string, translations: TranslationInput[]): Promise<StyleOption> {
  return apiRequest<StyleOption>(`/api/v1/shops/${shopId}/catalog/style-options/${optionId}/`, {
    method: 'PATCH',
    body: { translations },
  })
}

export async function toggleShopStyleOptionActive(shopId: string, optionId: string, is_active: boolean): Promise<StyleOption> {
  return apiRequest<StyleOption>(`/api/v1/shops/${shopId}/catalog/style-options/${optionId}/`, {
    method: 'PATCH',
    body: { is_active },
  })
}

export async function uploadShopStyleOptionImages(shopId: string, optionId: string, files: File[], onProgress?: (fileIndex: number, percent: number) => void): Promise<StyleImage[]> {
  if (files.length !== 1) throw new Error('Upload exactly one image per style option.')
  const legacyPath = `/api/v1/shops/${shopId}/catalog/style-options/${optionId}/reference-images/`
  return uploadPrivateMediaBatch<StyleImage[]>({
    path: `/api/v1/shops/${shopId}/catalog/media/uploads/`, kind: 'style_option', targetId: optionId, files, onProgress,
    fallback: () => { const formData = new FormData(); files.forEach(file => formData.append('images', file)); return multipartRequest<StyleImage[]>(legacyPath, formData) },
  })
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
  if (files.length !== 1) throw new Error('Upload exactly one image per style option.')
  const legacyPath = `/api/v1/catalog/style-options/${optionId}/reference-images/`
  return uploadPrivateMediaBatch<StyleImage[]>({
    path: '/api/v1/catalog/media/uploads/', kind: 'style_option', targetId: optionId, files,
    fallback: () => { const formData = new FormData(); files.forEach(file => formData.append('images', file)); return multipartRequest<StyleImage[]>(legacyPath, formData) },
  })
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

export function getFamilyDetail(familyId: string): Promise<CatalogFamilyDetail> {
  return apiRequest<CatalogFamilyDetail>(`/api/v1/catalog/families/${familyId}/`)
}

export function createGlobalFamily(data: CatalogFamilyInput): Promise<CatalogFamily> {
  return apiRequest<CatalogFamily>('/api/v1/catalog/families/', { method: 'POST', body: data })
}

export function updateGlobalFamily(familyId: string, translations: TranslationInput[]): Promise<CatalogFamilyDetail> {
  return apiRequest<CatalogFamilyDetail>(`/api/v1/catalog/families/${familyId}/`, {
    method: 'PATCH', body: { translations },
  })
}

export function setGlobalFamilyStatus(familyId: string, active: boolean): Promise<CatalogFamily> {
  return apiRequest<CatalogFamily>(`/api/v1/catalog/families/${familyId}/${active ? 'reactivate' : 'archive'}/`, {
    method: 'POST', body: {},
  })
}

export function uploadGlobalFamilyImage(familyId: string, image: File): Promise<CatalogFamilyImageMetadata> {
  const legacyPath = `/api/v1/catalog/families/${familyId}/image/`
  return uploadPrivateMediaBatch<CatalogFamilyImageMetadata>({
    path: '/api/v1/catalog/media/uploads/', kind: 'family', targetId: familyId, files: [image],
    fallback: () => { const formData = new FormData(); formData.append('image', image); return multipartRequest<CatalogFamilyImageMetadata>(legacyPath, formData) },
  })
}

export function removeGlobalFamilyImage(familyId: string): Promise<void> {
  return apiRequest<void>(`/api/v1/catalog/families/${familyId}/image/`, { method: 'DELETE' })
}
