export type ApiPage<T> = {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface CatalogFamily {
  id: string
  name: string
  code: string
  status?: 'ACTIVE' | 'ARCHIVED'
  has_image?: boolean
  image_content_url?: string | null
}

export interface CatalogFamilyTranslation extends TranslationInput {
  description: string
}

export interface CatalogFamilyDetail extends CatalogFamily {
  translations: CatalogFamilyTranslation[]
  option_groups: OptionGroup[]
}

export interface CatalogFamilyInput {
  code: string
  translations: TranslationInput[]
}

export interface CatalogFamilyImageMetadata {
  has_image: boolean
  image_content_url: string | null
  mime_type: string
  byte_size: number | null
  width: number | null
  height: number | null
}

export type CatalogFamilyPage = ApiPage<CatalogFamily>

export interface OptionGroup {
  id: string
  name: string
  code: string
  families: string[]
}

export type CatalogOptionGroupPage = ApiPage<OptionGroup>

export interface Variant {
  id: string
  family: string
  name: string
  code: string
  is_default: boolean
  is_global: boolean
  is_active: boolean
}

export interface VariantDetail extends Variant {
  description: string
  translations: Array<TranslationInput & { description: string }>
  created_at: string
  updated_at: string
}

export type VariantStatus = 'ACTIVE' | 'ARCHIVED' | 'all'
export type VariantSource = 'all' | 'global' | 'shop'

export interface VariantQuery {
  page?: number
  family?: string
  search?: string
  status?: VariantStatus
  source?: VariantSource
}

export type ShopVariantPage = ApiPage<Variant>

export interface StyleImage {
  id: string
  mime_type: string
  byte_size: number
  width: number
  height: number
  sort_order: number
  alt_text: string
  content_url: string
}

export interface StyleOption {
  id: string
  option_group: string
  tenant: string | null
  code: string
  name: string
  is_active: boolean
  is_global: boolean
  reference_images: StyleImage[]
}

export type ShopStyleOptionPage = ApiPage<StyleOption>

export interface TranslationInput {
  locale: 'en' | 'ar-KW' | 'bn' | 'ur'
  name: string
  description?: string
}

export interface ShopVariantInputRequest {
  family_id: string
  code: string
  translations: TranslationInput[]
}

export interface ShopStyleOptionInputRequest {
  option_group_id: string
  code: string
  translations: TranslationInput[]
}
