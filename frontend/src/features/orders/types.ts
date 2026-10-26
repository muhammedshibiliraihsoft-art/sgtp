export type OrderStatus = 'REQUEST' | 'CUTTING' | 'STITCHING' | 'CHECK' | 'FINISHING' | 'QC' | 'COMPLETED'
export type OrderPriority = 'NORMAL' | 'URGENT' | 'VERY_URGENT'
export type DueIndicator = 'UPCOMING' | 'DUE_SOON' | 'DUE_TODAY' | 'OVERDUE' | null

export interface Order {
  id: string
  work_number: string
  client_id: string
  related_person_id: string | null
  design_version_id: string
  measurement_set_id: string
  material_id: string | null
  assigned_membership_id: string | null
  status: OrderStatus
  priority: OrderPriority
  due_date: string | null
  due_indicator: DueIndicator
  notes: string
  created_at: string
  updated_at: string
}

export interface OrderPage {
  count: number
  next: string | null
  previous: string | null
  results: Order[]
}

export interface DeletedOrder {
  id: string
  work_number: string
  client_name: string
  design_name: string
  status: OrderStatus
  priority: OrderPriority
  due_date: string | null
  created_at: string
  deleted: string
  deleted_date: string
}

export interface DeletedOrderPage {
  count: number
  next: string | null
  previous: string | null
  results: DeletedOrder[]
}

export interface CreateOrderInput {
  client_id: string
  related_person_id?: string | null
  design_version_id: string
  measurement_set_id: string
  material_id?: string | null
  priority?: OrderPriority
  due_date?: string | null
  notes?: string
}

export interface UpdateOrderInput {
  priority?: OrderPriority
  due_date?: string | null
  notes?: string
}
