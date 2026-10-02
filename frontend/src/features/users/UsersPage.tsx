import { useState, useMemo, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Search, ChevronLeft, ChevronRight, MoreHorizontal } from 'lucide-react'
import { MockUserAdapter } from './mocks'
import type { MembershipDTO, ShopStats } from './types'
import { UserForm } from './UserForm'
import { WorkFunctionsModal } from './WorkFunctionsModal'
import { ConfirmActionModal } from './ConfirmActionModal'
import { MemberActionsMenu } from './MemberActionsMenu'
import { CustomSelect } from '../../components/CustomSelect'
import './users.css'

export function UsersPage() {
  const { t } = useTranslation()
  
  const [memberships, setMemberships] = useState<MembershipDTO[]>([])
  const [stats, setStats] = useState<ShopStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  
  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState<'ALL' | 'ADMIN' | 'STAFF' | 'VIEWER'>('ALL')
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE' | 'INACTIVE'>('ALL')
  
  const [page, setPage] = useState(1)
  const pageSize = 20

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [credentialsReveal, setCredentialsReveal] = useState<{ user_code: string, initial_password: string } | null>(null)
  
  const [manageWorkFunctions, setManageWorkFunctions] = useState<MembershipDTO | null>(null)
  const [activeMemberMenu, setActiveMemberMenu] = useState<MembershipDTO | null>(null)
  const [actionMember, setActionMember] = useState<{ member: MembershipDTO, action: 'DEACTIVATE' | 'REACTIVATE' | 'REMOVE' | 'PROMOTE_STAFF' | 'DEMOTE_VIEWER' } | null>(null)
  const loadData = async () => {
    setIsLoading(true)
    try {
      const [mems, st] = await Promise.all([
        MockUserAdapter.getMemberships(),
        MockUserAdapter.getShopStats()
      ])
      setMemberships(mems)
      setStats(st)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadData()
  }, [])

  const filteredMemberships = useMemo(() => {
    let result = memberships
    
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      result = result.filter(m => 
        m.display_name.toLowerCase().includes(q) || 
        m.user_code.toLowerCase().includes(q)
      )
    }
    
    if (roleFilter !== 'ALL') {
      result = result.filter(m => m.role === roleFilter)
    }
    
    if (statusFilter !== 'ALL') {
      const isActive = statusFilter === 'ACTIVE'
      result = result.filter(m => m.is_active === isActive)
    }
    
    return result
  }, [memberships, searchQuery, roleFilter, statusFilter])

  const paginatedMemberships = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredMemberships.slice(start, start + pageSize)
  }, [filteredMemberships, page])

  const totalPages = Math.ceil(filteredMemberships.length / pageSize)

  const handleActionConfirm = async () => {
    if (!actionMember) return
    const { member, action } = actionMember
    
    try {
      if (action === 'DEACTIVATE') {
        await MockUserAdapter.updateMembershipStatus(member.id, false)
      } else if (action === 'REACTIVATE') {
        await MockUserAdapter.updateMembershipStatus(member.id, true)
      } else if (action === 'REMOVE') {
        await MockUserAdapter.removeMembership(member.id)
      } else if (action === 'PROMOTE_STAFF') {
        await MockUserAdapter.updateMembershipRole(member.id, 'STAFF')
      } else if (action === 'DEMOTE_VIEWER') {
        await MockUserAdapter.updateMembershipRole(member.id, 'VIEWER')
      }
      await loadData()
    } catch (e) {
      console.error(e)
    } finally {
      setActionMember(null)
    }
  }

  return (
    <div className="users-page">
      <div className="users-header">
        <div className="users-title-area">
          <h1>{t('users.title', 'Team')}</h1>
          {stats && (
            <p className="users-capacity">
              Users: {stats.user_count} / {stats.max_users}
            </p>
          )}
        </div>
        <button 
          className="btn-primary" 
          disabled={stats?.is_at_user_limit || isLoading}
          onClick={() => setIsFormOpen(true)}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
        >
          <Plus size={16} /> {t('users.addUser', 'Add user')}
        </button>
      </div>

      <div className="users-controls">
        <div className="users-search">
          <Search size={16} />
          <input 
            placeholder={t('users.searchPlaceholder', 'Search by name or User ID')}
            value={searchQuery}
            onChange={e => { setSearchQuery(e.target.value); setPage(1); }}
          />
        </div>
        <div className="users-filters">
          <CustomSelect 
            value={roleFilter} 
            onChange={val => { setRoleFilter(val as any); setPage(1) }} 
            className="users-select"
            options={[
              { value: 'ALL', label: 'All Roles' },
              { value: 'ADMIN', label: 'Admin' },
              { value: 'STAFF', label: 'Staff' },
              { value: 'VIEWER', label: 'Viewer' }
            ]} 
          />
          <CustomSelect 
            value={statusFilter} 
            onChange={val => { setStatusFilter(val as any); setPage(1) }} 
            className="users-select"
            options={[
              { value: 'ALL', label: 'All Statuses' },
              { value: 'ACTIVE', label: 'Active' },
              { value: 'INACTIVE', label: 'Inactive' }
            ]} 
          />
        </div>
      </div>

      {isLoading ? (
        <div className="users-loading">Loading...</div>
      ) : filteredMemberships.length === 0 ? (
        <div className="empty-state">
          <h3>No team members found</h3>
          <p>Try adjusting your search or filters.</p>
        </div>
      ) : (
        <>
          <div className="users-table-container">
            <table className="users-table">
              <thead>
                <tr>
                  <th className="col-user">User</th>
                  <th className="col-userid">User ID</th>
                  <th className="col-email">Email</th>
                  <th className="col-role">Role</th>
                  <th className="col-status">Status</th>
                  <th className="col-updated">Updated</th>
                  <th className="col-actions">Actions</th>
                </tr>
              </thead>
              <tbody>
                {paginatedMemberships.map(m => (
                  <tr key={m.id} className={!m.is_active ? 'inactive-row' : ''}>
                    <td className="col-user"><strong>{m.display_name}</strong></td>
                    <td className="col-userid"><span className="code-badge">{m.user_code}</span></td>
                    <td className="col-email">{m.user_email || '—'}</td>
                    <td className="col-role">
                      <span className={`role-badge role-${m.role.toLowerCase()}`}>{m.role}</span>
                    </td>
                    <td className="col-status">
                      <span className={`status-badge status-${m.is_active ? 'active' : 'inactive'}`}>
                        {m.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="col-updated">
                      {new Date(m.updated_at).toLocaleDateString()}
                    </td>
                    <td className="col-actions">
                      <div className="action-buttons">
                        {m.role !== 'ADMIN' ? (
                          <button className="btn-icon" title="Manage Member" onClick={() => setActiveMemberMenu(m)}>
                            <MoreHorizontal size={18} />
                          </button>
                        ) : (
                          <span className="admin-lock">Protected</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="users-list-mobile">
            {paginatedMemberships.map(m => (
              <div key={m.id} className={`user-card ${!m.is_active ? 'inactive-card' : ''}`}>
                <div className="uc-header">
                  <strong>{m.display_name}</strong>
                  <span className={`role-badge role-${m.role.toLowerCase()}`}>{m.role}</span>
                </div>
                <div className="uc-body">
                  <div><span className="code-badge">{m.user_code}</span></div>
                  {m.user_email && <div className="text-muted">{m.user_email}</div>}
                  <div className={`status-text ${m.is_active ? 'active' : 'inactive'}`}>
                    {m.is_active ? 'Active' : 'Inactive'}
                  </div>
                </div>
                <div className="uc-actions">
                  {m.role !== 'ADMIN' ? (
                    <button className="btn-secondary" onClick={() => setActiveMemberMenu(m)} style={{ width: '100%', justifyContent: 'center' }}>
                      Manage Member
                    </button>
                  ) : (
                    <span className="admin-lock">Protected Admin User</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button disabled={page === 1} onClick={() => setPage(p => p - 1)}>
                <ChevronLeft size={18} />
              </button>
              <span>{page} / {totalPages}</span>
              <button disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>
                <ChevronRight size={18} />
              </button>
            </div>
          )}
        </>
      )}

      {isFormOpen && (
        <UserForm 
          onClose={() => setIsFormOpen(false)} 
          onSuccess={(creds) => {
            setIsFormOpen(false)
            setCredentialsReveal({ user_code: creds.user_code!, initial_password: creds.initial_password! })
            void loadData()
          }} 
        />
      )}

      {credentialsReveal && (
        <div className="modal-overlay">
          <div className="modal-content credentials-modal">
            <h2>User Created Successfully</h2>
            <p className="warning-text">
              Please copy these generated credentials securely. 
              <strong> You will not be able to see this password again.</strong>
            </p>
            <div className="credentials-box">
              <div className="cred-row">
                <label>User ID</label>
                <code>{credentialsReveal.user_code}</code>
              </div>
              <div className="cred-row">
                <label>Initial Password</label>
                <code className="password">{credentialsReveal.initial_password}</code>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn-primary" onClick={() => setCredentialsReveal(null)}>I have saved them</button>
            </div>
          </div>
        </div>
      )}

      {activeMemberMenu && (
        <MemberActionsMenu 
          member={activeMemberMenu}
          onClose={() => setActiveMemberMenu(null)}
          onAction={(action) => {
            setActiveMemberMenu(null)
            if (action === 'WORK_FUNCTIONS') {
              setManageWorkFunctions(activeMemberMenu)
            } else {
              setActionMember({ member: activeMemberMenu, action })
            }
          }}
        />
      )}

      {manageWorkFunctions && (
        <WorkFunctionsModal 
          membership={manageWorkFunctions} 
          onClose={() => setManageWorkFunctions(null)} 
        />
      )}

      {actionMember && (
        <ConfirmActionModal 
          action={actionMember.action}
          member={actionMember.member}
          onConfirm={handleActionConfirm}
          onCancel={() => setActionMember(null)}
        />
      )}
    </div>
  )
}
