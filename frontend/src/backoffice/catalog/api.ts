import { apiRequest, multipartRequest } from '../../services/apiClient'
import { uploadPrivateMediaBatch } from '../../services/privateMediaUpload'
import type { CatalogFamilyPage, CatalogOptionGroupPage, ShopStyleOptionInputRequest, ShopStyleOptionPage, StyleImage, StyleOption } from '../../features/catalog/types'

export function getGlobalFamilies(page = 1): Promise<CatalogFamilyPage> {
  return apiRequest<CatalogFamilyPage>(`/api/v1/catalog/families/?page=${page}`)
}

export function getGlobalOptionGroups(page = 1): Promise<CatalogOptionGroupPage> {
  return apiRequest<CatalogOptionGroupPage>(`/api/v1/catalog/option-groups/?page=${page}`)
}

export function getGlobalStyleOptions(page = 1): Promise<ShopStyleOptionPage> {
  return apiRequest<ShopStyleOptionPage>(`/api/v1/catalog/style-options/?page=${page}`)
}

export function createGlobalStyleOption(data: ShopStyleOptionInputRequest): Promise<StyleOption> {
  return apiRequest<StyleOption>('/api/v1/catalog/style-options/', { method: 'POST', body: data })
}

export function setGlobalStyleOptionActive(optionId: string, is_active: boolean): Promise<StyleOption> {
  return apiRequest<StyleOption>(`/api/v1/catalog/style-options/${optionId}/`, { method: 'PATCH', body: { is_active } })
}

export function uploadGlobalStyleOptionImages(optionId: string, files: File[]): Promise<StyleImage[]> {
  const legacyPath = `/api/v1/catalog/style-options/${optionId}/reference-images/`
  return uploadPrivateMediaBatch<StyleImage[]>({
    path: '/api/v1/catalog/media/uploads/', kind: 'style_option', targetId: optionId, files,
    fallback: () => { const formData = new FormData(); files.forEach(file => formData.append('images', file)); return multipartRequest<StyleImage[]>(legacyPath, formData) },
  })
}
