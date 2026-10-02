import { useState, useEffect } from 'react'
import { MockUserAdapter } from './mocks'
import type { MembershipDTO, WorkFunctionCode } from './types'

import { Tag, Ruler, Scissors, Layers, Sparkles, ClipboardCheck, Calculator } from 'lucide-react'

interface Props {
  membership: MembershipDTO
  onClose: () => void
}

const FUNCTIONS: { code: WorkFunctionCode, label: string, icon: React.ReactNode }[] = [
  { code: 'SALES', label: 'Sales', icon: <Tag size={16} /> },
  { code: 'MEASUREMENT', label: 'Measurement', icon: <Ruler size={16} /> },
  { code: 'CUTTING', label: 'Cutting', icon: <Scissors size={16} /> },
  { code: 'STITCHING', label: 'Stitching', icon: <Layers size={16} /> },
  { code: 'FINISHING', label: 'Finishing', icon: <Sparkles size={16} /> },
  { code: 'QC', label: 'Quality control', icon: <ClipboardCheck size={16} /> },
  { code: 'CASHIER', label: 'Cashier', icon: <Calculator size={16} /> }
]

export function WorkFunctionsModal({ membership, onClose }: Props) {
  const [functions, setFunctions] = useState<WorkFunctionCode[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    MockUserAdapter.getWorkFunctions(membership.id)
      .then(res => setFunctions(res.functions))
      .catch(() => setError('Failed to load work functions'))
      .finally(() => setIsLoading(false))
  }, [membership.id])

  const toggleFunction = (code: WorkFunctionCode) => {
    if (functions.includes(code)) {
      setFunctions(functions.filter(f => f !== code))
    } else {
      setFunctions([...functions, code])
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    setError(null)
    try {
      await MockUserAdapter.setWorkFunctions(membership.id, functions)
      onClose()
    } catch (e: any) {
      setError(e.message || 'Failed to save work functions')
      setIsSaving(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Work Functions</h2>
        <p className="modal-subtitle">Manage functions for {membership.display_name}</p>
        
        {error && <div className="form-error">{error}</div>}
        
        {isLoading ? (
          <div>Loading...</div>
        ) : (
          <div>
            <p className="form-hint">Select the operational functions this member performs. These are descriptive and do not grant system permissions.</p>
            <div className="wf-grid">
              {FUNCTIONS.map(f => {
                const isSelected = functions.includes(f.code)
                return (
                  <div 
                    key={f.code} 
                    className={`wf-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => toggleFunction(f.code)}
                  >
                    {f.icon}
                    <span>{f.label}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose} disabled={isSaving || isLoading}>Cancel</button>
          <button className="btn-primary" onClick={handleSave} disabled={isSaving || isLoading}>
            {isSaving ? 'Saving...' : 'Save Functions'}
          </button>
        </div>
      </div>
    </div>
  )
}
