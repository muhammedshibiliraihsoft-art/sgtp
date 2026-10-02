export interface DesignReference {
  id: string
  source?: 'design' | 'style_option'
  style_option_id?: string
  style_option_image_id?: string
  file_name?: string
  mime_type: string
  byte_size: number
  width: number
  height: number
  alt_text?: string
  content_url: string
}

export interface DesignSelection {
  id: string
  option_group: string
  style_option: string
  selected_code: string
  selected_name_en: string
  style_option_name: string
  style_option_translations: Array<{ locale: string; name: string; description: string }>
  style_option_images: Array<{
    id: string
    mime_type: string
    byte_size: number
    width: number
    height: number
    sort_order: number
    alt_text: string
    content_url: string
  }>
}

export interface DesignVersion {
  id: string
  number: number
  name: string
  translations: Array<{ locale: string; name: string; description: string }>
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
  published_at: string | null
  selections: DesignSelection[]
  references: DesignReference[]
}

export interface Design {
  id: string
  tenant: string | null
  family: string
  variant: string
  name: string
  status: 'ACTIVE' | 'ARCHIVED'
  latest_version: DesignVersion | null
  created_at: string
  updated_at: string
}

export interface ShopDesignPage {
  count: number
  next: string | null
  previous: string | null
  results: Design[]
}

export interface DesignCreateRequest {
  family_id: string
  variant_id: string
  name: string
  translations?: Array<{ locale: 'en' | 'ar-KW' | 'bn' | 'ur'; name: string; description?: string }>
}

export interface PublishResponse {
  published: DesignVersion
  next_draft: DesignVersion
}

export interface SelectionCreateRequest {
  style_option_id: string
}
