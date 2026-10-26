import { apiRequest } from './apiClient'

export type ShopMember = {
  id: string
  user_code: string
  user_id: string
  login_id: string
  display_name: string
  user_email: string
  user_phone: string
  role: 'ADMIN' | 'STAFF' | 'VIEWER'
  is_active: boolean
}

type MembershipPage = {
  next: string | null
  results: ShopMember[]
}

export async function getShopMembers(shopId: string): Promise<ShopMember[]> {
  const query = new URLSearchParams({ tenant: shopId })
  const members: ShopMember[] = []
  let path: string | null = `/api/v1/memberships/?${query}`

  while (path) {
    const page: MembershipPage = await apiRequest<MembershipPage>(path)
    members.push(...page.results)
    path = page.next ? `${new URL(page.next, window.location.origin).pathname}${new URL(page.next, window.location.origin).search}` : null
  }

  return members
}
