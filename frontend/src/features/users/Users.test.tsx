import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { UsersPage } from './UsersPage'
import { MockUserAdapter } from './mocks'

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback: string) => fallback || key,
    i18n: { language: 'en' }
  })
}))

// Mock adapter
vi.mock('./mocks', () => ({
  MockUserAdapter: {
    getMemberships: vi.fn(),
    getShopStats: vi.fn(),
    createShopUser: vi.fn(),
    updateMembershipRole: vi.fn(),
    updateMembershipStatus: vi.fn(),
    removeMembership: vi.fn(),
    getWorkFunctions: vi.fn(),
    setWorkFunctions: vi.fn()
  }
}))

const mockStats = { user_count: 5, max_users: 15, is_at_user_limit: false }
const mockMembers = [
  {
    id: 'm1',
    tenant: 't1',
    tenant_name: 'Shop',
    user_code: 'USR-1',
    display_name: 'Admin User',
    user_email: 'admin@test.com',
    role: 'ADMIN',
    is_active: true,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z'
  },
  {
    id: 'm2',
    tenant: 't1',
    tenant_name: 'Shop',
    user_code: 'USR-2',
    display_name: 'Staff User',
    user_email: null,
    role: 'STAFF',
    is_active: true,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z'
  }
]

describe('UsersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(MockUserAdapter.getMemberships).mockResolvedValue(mockMembers as any)
    vi.mocked(MockUserAdapter.getShopStats).mockResolvedValue(mockStats)
  })

  it('renders page and backend-aligned Membership fields', async () => {
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User') // Wait for data to load
    
    // Check fields
    expect(screen.getByText('Team')).toBeInTheDocument()
    expect(screen.getAllByText('USR-1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('admin@test.com').length).toBeGreaterThan(0)
    
    expect(screen.getAllByText('Staff User').length).toBeGreaterThan(0)
    expect(screen.getAllByText('USR-2').length).toBeGreaterThan(0)
  })

  it('Shop Admin Create User exposes STAFF/VIEWER only and no Shop selector', async () => {
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User') // Wait for data to load
    
    const addButton = screen.getAllByRole('button', { name: /Add user/i })[0]
    fireEvent.click(addButton)
    
    // Check roles using CustomSelect
    // Find the dropdown button containing "Staff (Operational access)" (the default selected option)
    const roleSelectButton = screen.getAllByRole('button', { name: /Staff \(Operational access\)/i })[0]
    fireEvent.click(roleSelectButton) // Open dropdown
    
    // Check that STAFF and VIEWER are available options
    expect(screen.getAllByRole('button', { name: /Staff \(Operational access\)/i }).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('button', { name: /Viewer \(Read-only\)/i }).length).toBeGreaterThan(0)
    
    // Check that ADMIN is NOT available
    expect(screen.queryByRole('button', { name: /Admin/i })).not.toBeInTheDocument()
    
    // Check no shop selector
    expect(screen.queryByLabelText(/Shop/i)).not.toBeInTheDocument()
  })

  it('Role change does not offer ADMIN', async () => {
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User') // Wait for data to load
    
    // Open action menu for a STAFF member
    const manageButtons = screen.getAllByTitle('Manage Member')
    fireEvent.click(manageButtons[0]) // Click first non-admin member's manage button

    // The "Demote to Viewer" action should exist
    expect(screen.getAllByText('Demote to Viewer').length).toBeGreaterThan(0)
    expect(screen.queryAllByText(/Promote to ADMIN/i).length).toBe(0)
  })
})
