export interface CatalogFamily {
  id: string
  name: string
  code: string
  description?: string
  is_active: boolean
}

export interface CatalogFamilyPage {
  count: number
  next: string | null
  previous: string | null
  results: CatalogFamily[]
}

export interface OptionGroup {
  id: string
  name: string
  code: string
  description?: string
  is_active: boolean
}

export interface CatalogOptionGroupPage {
  count: number
  next: string | null
  previous: string | null
  results: OptionGroup[]
}

export interface Variant {
  id: string
  family_id: string
  family_name: string
  name: string
  code: string
  is_active: boolean
  is_global: boolean
  tenant_id: string | null
}

export interface ShopVariantPage {
  count: number
  next: string | null
  previous: string | null
  results: Variant[]
}

export interface StyleImage {
  id: string
  file_name: string
  content_type: string
  size_bytes: number
  content_url: string
  uploaded_at: string
}

export interface StyleOption {
  id: string
  group_id: string
  group_name: string
  code: string
  name: string
  is_active: boolean
  is_global: boolean
  tenant_id: string | null
  reference_images: StyleImage[]
}

export interface ShopStyleOptionPage {
  count: number
  next: string | null
  previous: string | null
  results: StyleOption[]
}

// Request Types
export interface ShopVariantInputRequest {
  family_id: string
  name: string
  code?: string
}

export interface ShopStyleOptionInputRequest {
  group_id: string
  name: string
  code?: string
}
