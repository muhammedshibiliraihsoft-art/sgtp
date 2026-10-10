export interface MembershipDTO {
  id: string
  tenant: string
  tenant_name: string
  user_code: string
  user_id?: string
  login_id?: string | null
  display_name: string
  user_email: string | null
  role: 'ADMIN' | 'STAFF' | 'VIEWER'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateShopUserResult {
  id: string
  email: string | null
  first_name: string
  last_name: string
  phone: string | null
  is_active: boolean
  role: 'ADMIN' | 'STAFF' | 'VIEWER'
  initial_password?: string
  user_code?: string
  login_id?: string
}

export type WorkFunctionCode = 'SALES' | 'MEASUREMENT' | 'CUTTING' | 'STITCHING' | 'FINISHING' | 'QC' | 'CASHIER'

export interface WorkFunctionSetResponse {
  membership_id: string
  shop_id: string
  functions: WorkFunctionCode[]
}

export interface ShopStats {
  user_count: number
  max_users: number
  is_at_user_limit: boolean
}

export interface CreateShopUserRequest {
  login_id?: string
  first_name: string
  last_name?: string
  email?: string
  phone?: string
  role: 'STAFF' | 'VIEWER'
}
