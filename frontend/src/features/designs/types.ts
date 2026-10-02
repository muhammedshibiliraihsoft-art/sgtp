export interface DesignReference {
  id: string
  file_name: string
  content_type: string
  size_bytes: number
  content_url: string
  uploaded_at: string
}

export interface DesignSelection {
  id: string
  style_option_id: string
  style_option_name: string
  group_id: string
  group_name: string
}

export interface DesignVersion {
  id: string
  design_id: string
  number: number
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
  created_at: string
  published_at: string | null
  selections: DesignSelection[]
  references: DesignReference[]
}

export interface Design {
  id: string
  tenant_id: string | null
  family_id: string
  family_name: string
  variant_id: string
  variant_name: string
  status: 'ACTIVE' | 'ARCHIVED'
  latest_version: DesignVersion
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
}

export interface PublishResponse {
  published: DesignVersion
  next_draft: DesignVersion
}

export interface SelectionCreateRequest {
  style_option_id: string
}
