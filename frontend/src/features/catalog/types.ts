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
