import type { ApiPage } from '../catalog/types'

export type MeasurementUnit = 'CM' | 'INCH'

export type MeasurementOwner =
  | { kind: 'client' }
  | { kind: 'related_person'; id: string }

export interface MeasurementProfile {
  id: string
  client: string | null
  related_person: string | null
  family: string
  variant: string | null
  created_at: string
}

export interface MeasurementDefinition {
  id: string
  code: string
  group_code: string
  sort_order: number
  is_active: boolean
  is_global: boolean
  translations: Array<{ locale: string; name: string; description: string }>
  mappings: Array<{ family_id: string; variant_id: string | null; sort_order: number }>
}

export interface MeasurementValue {
  id: string
  definition: string
  definition_code_snapshot: string
  label_snapshot: string
  label: string
  translations: Record<string, string>
  value: string
  unit: MeasurementUnit
}

export interface MeasurementSet {
  id: string
  profile: string
  version: number
  copied_from: string | null
  created_at: string
  values: MeasurementValue[]
}

export interface ComparisonRow {
  definition_id: string
  code: string
  label: string
  from_value: string | null
  from_unit: MeasurementUnit | null
  to_value: string | null
  to_unit: MeasurementUnit | null
  difference: string | null
  unit_mismatch: boolean
}

export interface MeasurementComparison {
  from_set_id: string
  to_set_id: string
  results: ComparisonRow[]
}

export interface InventoryFabric {
  material_id: string
  name: string
  code: string
  category: string
  unit: string
  status: string
  on_hand: string
  reserved: string
  available: string
}

export type MeasurementPage<T> = ApiPage<T>
