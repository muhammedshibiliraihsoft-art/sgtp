import type { MembershipDTO, CreateShopUserRequest, CreateShopUserResult, WorkFunctionCode, WorkFunctionSetResponse, ShopStats } from './types'

let memberships: MembershipDTO[] = [
  {
    id: 'mem-1',
    tenant: 'shop-1',
    tenant_name: 'Modern Tailors',
    user_code: 'USR-ABCD-1234',
    display_name: 'Admin User',
    user_email: 'admin@moderntailors.com',
    role: 'ADMIN',
    is_active: true,
    created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'mem-2',
    tenant: 'shop-1',
    tenant_name: 'Modern Tailors',
    user_code: 'USR-XYZW-5678',
    display_name: 'Sameera',
    user_email: null,
    role: 'STAFF',
    is_active: true,
    created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'mem-3',
    tenant: 'shop-1',
    tenant_name: 'Modern Tailors',
    user_code: 'USR-LMNP-9012',
    display_name: 'Rashid',
    user_email: 'rashid@example.com',
    role: 'VIEWER',
    is_active: false,
    created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
  }
]

let workFunctions: Record<string, WorkFunctionCode[]> = {
  'mem-2': ['MEASUREMENT', 'CUTTING'],
  'mem-3': []
}

const generateId = () => Math.random().toString(36).substring(2, 9)
const generateUserCode = () => `USR-${Math.random().toString(36).substring(2, 6).toUpperCase()}-${Math.random().toString(36).substring(2, 6).toUpperCase()}`
const generatePassword = () => Math.random().toString(36).substring(2, 10) + 'A1!'

export const MockUserAdapter = {
  getMemberships: async (): Promise<MembershipDTO[]> => {
    return new Promise(resolve => setTimeout(() => resolve([...memberships]), 500))
  },

  createShopUser: async (data: CreateShopUserRequest): Promise<CreateShopUserResult> => {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (memberships.length >= 15) {
          reject(new Error('Shop user limit reached.'))
          return
        }

        const newId = `mem-${generateId()}`
        const newUserCode = generateUserCode()
        
        const newMember: MembershipDTO = {
          id: newId,
          tenant: 'shop-1',
          tenant_name: 'Modern Tailors',
          user_code: newUserCode,
          display_name: `${data.first_name} ${data.last_name || ''}`.trim(),
          user_email: data.email || null,
          role: data.role,
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        
        memberships.push(newMember)
        
        resolve({
          id: `usr-${generateId()}`,
          email: data.email || null,
          first_name: data.first_name,
          last_name: data.last_name || '',
          phone: data.phone || null,
          is_active: true,
          role: data.role,
          initial_password: generatePassword(),
          user_code: newUserCode
        })
      }, 600)
    })
  },

  updateMembershipRole: async (membershipId: string, role: 'STAFF' | 'VIEWER'): Promise<MembershipDTO> => {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const mem = memberships.find(m => m.id === membershipId)
        if (!mem) return reject(new Error('Membership not found'))
        if (mem.role === 'ADMIN') return reject(new Error('Cannot modify ADMIN role'))
        
        mem.role = role
        mem.updated_at = new Date().toISOString()
        resolve({ ...mem })
      }, 400)
    })
  },

  updateMembershipStatus: async (membershipId: string, is_active: boolean): Promise<MembershipDTO> => {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const mem = memberships.find(m => m.id === membershipId)
        if (!mem) return reject(new Error('Membership not found'))
        if (mem.role === 'ADMIN') return reject(new Error('Cannot modify ADMIN lifecycle'))
        
        mem.is_active = is_active
        mem.updated_at = new Date().toISOString()
        resolve({ ...mem })
      }, 400)
    })
  },

  removeMembership: async (membershipId: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const mem = memberships.find(m => m.id === membershipId)
        if (!mem) return reject(new Error('Membership not found'))
        if (mem.role === 'ADMIN') return reject(new Error('Cannot remove ADMIN'))
        
        memberships = memberships.filter(m => m.id !== membershipId)
        delete workFunctions[membershipId]
        resolve()
      }, 500)
    })
  },

  getWorkFunctions: async (membershipId: string): Promise<WorkFunctionSetResponse> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          membership_id: membershipId,
          shop_id: 'shop-1',
          functions: workFunctions[membershipId] || []
        })
      }, 300)
    })
  },

  setWorkFunctions: async (membershipId: string, functions: WorkFunctionCode[]): Promise<WorkFunctionSetResponse> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        workFunctions[membershipId] = [...functions]
        resolve({
          membership_id: membershipId,
          shop_id: 'shop-1',
          functions: workFunctions[membershipId]
        })
      }, 400)
    })
  },

  getShopStats: async (): Promise<ShopStats> => {
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          user_count: memberships.length,
          max_users: 15,
          is_at_user_limit: memberships.length >= 15
        })
      }, 200)
    })
  }
}
