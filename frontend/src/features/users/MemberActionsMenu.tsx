import { Briefcase, UserCheck, UserCog, UserX, X, KeyRound } from 'lucide-react'
import type { MembershipDTO } from './types'

interface Props {
  member: MembershipDTO
  onAction: (action: 'WORK_FUNCTIONS' | 'RESET_PIN' | 'PROMOTE_STAFF' | 'DEMOTE_VIEWER' | 'DEACTIVATE' | 'REACTIVATE' | 'REMOVE') => void
  onClose: () => void
}

export function MemberActionsMenu({ member, onAction, onClose }: Props) {
  return (
    <>
      <div className="modal-overlay" onClick={onClose} />
      <div className="action-menu-container" role="dialog" aria-modal="true" aria-label={`Manage ${member.display_name}`} tabIndex={-1}>
        <div className="action-menu-header">
          <h3>Manage {member.display_name}</h3>
          <button data-dialog-close className="btn-icon" onClick={onClose} aria-label="Close actions"><X size={20} /></button>
        </div>
        
        <div className="action-menu-list">
          {member.is_active && member.user_id && member.role === 'STAFF' && <button className="action-menu-item" onClick={() => onAction('RESET_PIN')}><KeyRound size={18} /><span>Reset PIN</span></button>}
          <button className="action-menu-item" onClick={() => onAction('WORK_FUNCTIONS')}>
            <Briefcase size={18} />
            <span>Work Functions</span>
          </button>

          {member.role === 'VIEWER' ? (
            <button className="action-menu-item" onClick={() => onAction('PROMOTE_STAFF')}>
              <UserCheck size={18} />
              <span>Promote to Staff</span>
            </button>
          ) : (
            <button className="action-menu-item" onClick={() => onAction('DEMOTE_VIEWER')}>
              <UserCog size={18} />
              <span>Demote to Viewer</span>
            </button>
          )}

          {member.is_active ? (
            <button className="action-menu-item text-warning" onClick={() => onAction('DEACTIVATE')}>
              <UserX size={18} />
              <span>Deactivate Account</span>
            </button>
          ) : (
            <button className="action-menu-item" onClick={() => onAction('REACTIVATE')}>
              <UserCheck size={18} />
              <span>Reactivate Account</span>
            </button>
          )}

          <div className="action-divider" />
          
          <button className="action-menu-item text-danger" onClick={() => onAction('REMOVE')}>
            <UserX size={18} />
            <span>Remove from Shop</span>
          </button>
        </div>
      </div>
    </>
  )
}
