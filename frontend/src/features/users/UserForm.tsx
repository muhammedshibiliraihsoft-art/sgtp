import { useState } from 'react'
import { usersApi } from './api'
import type { CreateShopUserRequest, CreateShopUserResult, WorkFunctionCode } from './types'
import { Tag, Ruler, Scissors, Layers, Sparkles, ClipboardCheck, Calculator } from 'lucide-react'
import { CustomSelect } from '../../components/CustomSelect'

const FUNCTIONS: { code: WorkFunctionCode, label: string, icon: React.ReactNode }[] = [
  { code: 'SALES', label: 'Sales', icon: <Tag size={16} /> },
  { code: 'MEASUREMENT', label: 'Measurement', icon: <Ruler size={16} /> },
  { code: 'CUTTING', label: 'Cutting', icon: <Scissors size={16} /> },
  { code: 'STITCHING', label: 'Stitching', icon: <Layers size={16} /> },
  { code: 'FINISHING', label: 'Finishing', icon: <Sparkles size={16} /> },
  { code: 'QC', label: 'Quality control', icon: <ClipboardCheck size={16} /> },
  { code: 'CASHIER', label: 'Cashier', icon: <Calculator size={16} /> }
]

interface UserFormProps {
  shopId: string
  onClose: () => void
  onSuccess: (result: CreateShopUserResult) => void
}

export function UserForm({ shopId, onClose, onSuccess }: UserFormProps) {
  const [formData, setFormData] = useState<CreateShopUserRequest>({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    role: 'STAFF'
  })
  const [selectedFunctions, setSelectedFunctions] = useState<WorkFunctionCode[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    
    try {
      const result = await usersApi.createUser(shopId, formData)
      if (formData.role === 'STAFF' && selectedFunctions.length > 0) {
        const memberships = await usersApi.findCreatedMembership(shopId, result.user_code || '')
        const createdMembership = memberships.results.find(member => member.user_code === result.user_code)
        if (!createdMembership) throw new Error('User was created, but the Shop membership could not be loaded to assign work functions.')
        await usersApi.setFunctions(shopId, createdMembership.id, selectedFunctions)
      }
      onSuccess(result)
    } catch (err: any) {
      setError(err.message || 'Failed to create user')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="add-member-title" tabIndex={-1}>
      <div className="modal-content">
        <h2 id="add-member-title">Add Team Member</h2>
        {error && <div className="form-error">{error}</div>}
        
        <form onSubmit={handleSubmit} className="user-form">
          <div className="form-row">
            <div className="form-group">
              <label>First Name *</label>
              <input 
                required 
                value={formData.first_name}
                onChange={e => setFormData({...formData, first_name: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label>Last Name</label>
              <input 
                value={formData.last_name}
                onChange={e => setFormData({...formData, last_name: e.target.value})}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Email</label>
              <input 
                type="email"
                value={formData.email}
                onChange={e => setFormData({...formData, email: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label>Phone</label>
              <input 
                type="tel"
                value={formData.phone}
                onChange={e => setFormData({...formData, phone: e.target.value})}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Role *</label>
            <CustomSelect 
              value={formData.role}
              onChange={val => setFormData({...formData, role: val as 'STAFF' | 'VIEWER'})}
              options={[
                { value: 'STAFF', label: 'Staff (Operational access)' },
                { value: 'VIEWER', label: 'Viewer (Read-only)' }
              ]}
            />
            <small className="form-hint" style={{ display: 'block', marginTop: 4 }}>Admin roles cannot be created from this interface.</small>
          </div>

          {formData.role === 'STAFF' && (
            <div className="form-group">
              <label>Work Functions</label>
              <p className="form-hint">Select the operational functions this member performs.</p>
              <div className="wf-grid">
                {FUNCTIONS.map(f => {
                  const isSelected = selectedFunctions.includes(f.code)
                  return (
                    <button type="button" aria-pressed={isSelected}
                      key={f.code} 
                      className={`wf-card ${isSelected ? 'selected' : ''}`}
                      onClick={() => {
                        if (isSelected) setSelectedFunctions(selectedFunctions.filter(code => code !== f.code))
                        else setSelectedFunctions([...selectedFunctions, f.code])
                      }}
                    >
                      {f.icon}
                      <span>{f.label}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          <div className="modal-actions">
            <button data-dialog-close type="button" className="btn-secondary" onClick={onClose} disabled={isSubmitting}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
