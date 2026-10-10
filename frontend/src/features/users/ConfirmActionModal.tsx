import { useState } from 'react'
import type { MembershipDTO } from './types'

interface Props {
  member: MembershipDTO
  action: 'DEACTIVATE' | 'REACTIVATE' | 'REMOVE' | 'PROMOTE_STAFF' | 'DEMOTE_VIEWER'
  onConfirm: (loginId?: string) => void
  onCancel: () => void
}

export function ConfirmActionModal({ member, action, onConfirm, onCancel }: Props) {
  const [loginId, setLoginId] = useState('')
  const needsLoginId = action === 'PROMOTE_STAFF' && !member.login_id
  const loginIdIsValid = /^[a-zA-Z][a-zA-Z0-9_]{2,31}$/.test(loginId)
  let title = ''
  let message = ''
  let confirmText = ''
  let btnClass = 'btn-primary'

  switch (action) {
    case 'DEACTIVATE':
      title = 'Deactivate Member'
      message = `Are you sure you want to deactivate ${member.display_name}? They will no longer have access to the shop.`
      confirmText = 'Deactivate'
      btnClass = 'btn-primary danger'
      break
    case 'REACTIVATE':
      title = 'Reactivate Member'
      message = `Are you sure you want to reactivate ${member.display_name}? They will regain access to the shop.`
      confirmText = 'Reactivate'
      break
    case 'REMOVE':
      title = 'Remove from Shop'
      message = `Remove ${member.display_name} from this Shop? Their membership will be marked removed and will no longer grant access.`
      confirmText = 'Remove'
      btnClass = 'btn-primary danger'
      break
    case 'PROMOTE_STAFF':
      title = 'Promote to Staff'
      message = `Change ${member.display_name}'s role to STAFF? A temporary PIN will be generated and existing sessions revoked.`
      confirmText = 'Confirm Role Change'
      break
    case 'DEMOTE_VIEWER':
      title = 'Change Role to Viewer'
      message = `Are you sure you want to change ${member.display_name}'s role to VIEWER? They will lose operational access.`
      confirmText = 'Confirm Role Change'
      break
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="member-action-title" tabIndex={-1}>
      <div className="modal-content">
        <h2 id="member-action-title">{title}</h2>
        <p>{message}</p>
        {action === 'PROMOTE_STAFF' && !member.login_id && <div className="form-group">
          <label htmlFor="promote-staff-login-id">User ID *</label>
          <input id="promote-staff-login-id" required pattern="[a-zA-Z][a-zA-Z0-9_]{2,31}" value={loginId} onChange={event => setLoginId(event.target.value)} />
        </div>}
        <div className="modal-actions">
          <button data-dialog-close className="btn-secondary" onClick={onCancel}>Cancel</button>
          <button className={btnClass} disabled={needsLoginId && !loginIdIsValid} onClick={() => onConfirm(loginId || undefined)}>{confirmText}</button>
        </div>
      </div>
    </div>
  )
}
