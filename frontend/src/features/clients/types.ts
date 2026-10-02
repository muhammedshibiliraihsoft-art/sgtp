export type Client = {
  id: string
  name: string
  phone: string
  phone_normalized: string
  email: string
  created_at: string
  updated_at: string
}

export type RelatedPerson = {
  id: string
  name: string
  phone: string
  phone_normalized: string
  email: string
  created_at: string
  updated_at: string
  primary_client_id: string
}

export type PaginatedResponse<T> = {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
