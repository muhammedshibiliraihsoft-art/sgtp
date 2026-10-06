import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Archive, History, PackagePlus, Plus, RefreshCw } from 'lucide-react'
import { apiRequest } from '../../services/apiClient'
import { useCurrentShop } from '../../hooks/useCurrentShop'

type Page<T> = { count:number; results:T[]; next:string|null; previous:string|null }
type Material = { id:string; name:string; code:string; description:string; status:string; created_at:string; updated_at:string }
type Item = { material_id:string; name:string; code:string; category:string; unit:string; status:string; on_hand:string; reserved:string; available:string }
type Movement = { id:string; movement_type:string; quantity:string; unit_snapshot:string; on_hand_before:string; on_hand_after:string; reason:string; created_at:string }
const categories = ['FABRIC','BUTTON','ZIP','THREAD','HOOK','INTERLINING','OTHER']
const units = ['METRE','YARD','PIECE','ROLL']
async function allPages<T>(path:string):Promise<T[]> {
  const rows:T[]=[];let nextPath:string|null=path
  while(nextPath){const responsePage:Page<T>=await apiRequest<Page<T>>(nextPath);rows.push(...responsePage.results);if(!responsePage.next)break;const nextUrl:URL=new URL(responsePage.next,window.location.origin);nextPath=nextUrl.pathname+nextUrl.search}
  return rows
}

export function MaterialsInventoryPage() {
  const { shopId, role, isLoading: shopLoading } = useCurrentShop()
  const [tab, setTab] = useState<'inventory'|'materials'>('inventory')
  const [items, setItems] = useState<Item[]>([])
  const [materialRows, setMaterialRows] = useState<Material[]>([])
  const [selected, setSelected] = useState<Item|null>(null)
  const [movements, setMovements] = useState<Movement[]>([])
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const materialsLoaded = useRef(false)
  const loadRequestId = useRef(0)
  const ledgerRequestId = useRef(0)
  const activeShopId = useRef(shopId)
  const materials = useMemo(() => materialRows.filter(material => !query.trim() || `${material.name} ${material.code} ${material.description}`.toLowerCase().includes(query.trim().toLowerCase())), [materialRows, query])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [dialog, setDialog] = useState<'new-item'|'new-material'|'enable-material'|'stock-in'|'opening'|'adjust'|null>(null)
  const [legacyMaterial,setLegacyMaterial]=useState<Material|null>(null)
  const [form, setForm] = useState({ name:'', code:'', description:'', category:'FABRIC', stock_unit:'METRE', quantity:'', reason:'', direction:'IN' })
  const canManage = role === 'ADMIN'

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query.trim()), 250)
    return () => window.clearTimeout(timer)
  }, [query])

  useEffect(() => {
    if (activeShopId.current === shopId) return
    activeShopId.current = shopId
    loadRequestId.current += 1
    ledgerRequestId.current += 1
    materialsLoaded.current = false
    setMaterialRows([])
    setItems([])
    setSelected(null)
    setMovements([])
    setError('')
  }, [shopId])

  const load = useCallback(async (refreshMaterials = false) => {
    if (!shopId) { setBusy(shopLoading); return }
    const requestId = ++loadRequestId.current
    setBusy(true); setError('')
    try {
      const [inventory, materialRows] = await Promise.all([
        allPages<Item>(`/api/v1/shops/${shopId}/inventory/items/${debouncedQuery ? `?search=${encodeURIComponent(debouncedQuery)}` : ''}`),
        refreshMaterials || !materialsLoaded.current ? allPages<Material>(`/api/v1/shops/${shopId}/materials/`) : Promise.resolve(null),
      ])
      if (requestId !== loadRequestId.current) return
      if (materialRows) { setMaterialRows(materialRows); materialsLoaded.current = true }
      setItems(inventory)
    } catch (cause) { if (requestId === loadRequestId.current) setError(cause instanceof Error ? cause.message : 'Could not load Shop materials and inventory.') }
    finally { if (requestId === loadRequestId.current) setBusy(false) }
  }, [shopId, shopLoading, debouncedQuery])
  useEffect(() => { if (tab === 'inventory') void load() }, [load, tab])

  const openLedger = async (item: Item) => {
    if (!shopId) return
    const requestId = ++ledgerRequestId.current
    const requestedShopId = shopId
    setSelected(item); setError('')
    try {
      const page = await apiRequest<Page<Movement>>(`/api/v1/shops/${requestedShopId}/inventory/items/${item.material_id}/movements/`)
      if (requestId !== ledgerRequestId.current || activeShopId.current !== requestedShopId) return
      setMovements(page.results)
    } catch (cause) { if (requestId === ledgerRequestId.current && activeShopId.current === requestedShopId) setError(cause instanceof Error ? cause.message : 'Could not load stock history.') }
  }
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); if (!shopId) return
    setError(''); setMessage('')
    try {
      if (dialog === 'new-item') {
        await apiRequest(`/api/v1/shops/${shopId}/inventory/items/`, { method:'POST', body:{ name:form.name, code:form.code, description:form.description, category:form.category, stock_unit:form.stock_unit } })
      } else if (dialog === 'new-material') {
        await apiRequest(`/api/v1/shops/${shopId}/materials/`, { method:'POST', body:{ name:form.name, code:form.code, description:form.description } })
      } else if(dialog==='enable-material'&&legacyMaterial){
        await apiRequest(`/api/v1/shops/${shopId}/materials/${legacyMaterial.id}/enable-inventory/`,{method:'POST',body:{category:form.category,stock_unit:form.stock_unit}})
      } else if (selected && dialog) {
        const route = dialog === 'stock-in' ? 'stock-in' : dialog === 'opening' ? 'opening' : 'adjust'
        const body = dialog === 'adjust' ? { quantity:form.quantity, reason:form.reason, direction:form.direction } : { quantity:form.quantity, reason:form.reason }
        await apiRequest(`/api/v1/shops/${shopId}/inventory/items/${selected.material_id}/${route}/`, { method:'POST', body })
      }
      setDialog(null); setForm({ name:'', code:'', description:'', category:'FABRIC', stock_unit:'METRE', quantity:'', reason:'', direction:'IN' }); await load(true)
      if (selected) await openLedger(selected)
      setMessage('Saved successfully.')
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'The request could not be completed.') }
  }
  const archive = async (item: Item) => {
    if (!shopId || !window.confirm(`Archive ${item.name}? Stock must be zero and no quantity reserved.`)) return
    try { await apiRequest(`/api/v1/shops/${shopId}/inventory/items/${item.material_id}/archive/`, { method:'POST', body:{} }); setSelected(null); await load() }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not archive item.') }
  }

  return <div className="content-wrap">
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:16,flexWrap:'wrap'}}><div><h1>Materials & Inventory</h1><p style={{color:'var(--color-text-muted)'}}>Manage Shop materials and track stock through an immutable movement history.</p></div><button className="btn-secondary" onClick={() => void load(true)}><RefreshCw size={16}/> Refresh</button></div>
    <div style={{display:'flex',gap:8,borderBottom:'1px solid var(--color-border)',margin:'20px 0'}}>{(['inventory','materials'] as const).map(value=><button key={value} className="btn-secondary" onClick={()=>setTab(value)} aria-pressed={tab===value}>{value==='inventory'?'Inventory':'Materials'}</button>)}</div>
    <div style={{display:'flex',gap:12,marginBottom:16,flexWrap:'wrap'}}><input aria-label="Search" placeholder={`Search ${tab}…`} value={query} onChange={e=>setQuery(e.target.value)} style={{flex:'1 1 280px',minHeight:42,padding:'8px 12px',borderRadius:8,border:'1px solid var(--color-border)',background:'var(--color-surface)',color:'var(--color-text)'}}/>{canManage&&<button className="btn-primary" onClick={()=>{setForm({name:'',code:'',description:'',category:'FABRIC',stock_unit:'METRE',quantity:'',reason:'',direction:'IN'});setDialog(tab==='inventory'?'new-item':'new-material')}}><Plus size={16}/> {tab==='inventory'?'New inventory item':'New material'}</button>}</div>
    {error&&<div className="login-error-message" role="alert">{error}</div>}{message&&<div className="duplicate-warning" role="status">{message}</div>}
    {busy?<div className="empty-state" aria-busy="true">Loading…</div>:!shopId?<div className="empty-state">Shop context unavailable.</div>:tab==='inventory'?<div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(250px,1fr))',gap:14}}>{items.map(item=><article key={item.material_id} className="info-card" style={{padding:18,cursor:'pointer'}} onClick={()=>void openLedger(item)}><div style={{display:'flex',justifyContent:'space-between',gap:8}}><strong>{item.name}</strong><span className="code-badge">{item.category}</span></div><p>{item.code||'—'} · {item.unit}</p><div>On hand: <b>{item.on_hand}</b></div><div>Reserved: {item.reserved} · Available: <b>{item.available}</b></div>{canManage&&<div style={{display:'flex',gap:6,flexWrap:'wrap',marginTop:12}}><button className="btn-secondary" onClick={e=>{e.stopPropagation();setSelected(item);setDialog('opening')}}>Opening stock</button><button className="btn-secondary" onClick={e=>{e.stopPropagation();setSelected(item);setDialog('stock-in')}}><PackagePlus size={15}/> Stock in</button><button className="btn-secondary" onClick={e=>{e.stopPropagation();setSelected(item);setDialog('adjust')}}>Adjust</button><button className="btn-secondary" onClick={e=>{e.stopPropagation();void archive(item)}}><Archive size={15}/></button></div>}</article>)}</div>:<div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(240px,1fr))',gap:12}}>{materials.map(material=><article key={material.id} className="info-card" style={{padding:18}}><strong>{material.name}</strong><p>{material.code||'—'}</p><small>{material.description||'No description'} · {material.status}</small>{canManage&&<div style={{display:'flex',gap:8,marginTop:12}}><button className="btn-secondary" onClick={()=>{setLegacyMaterial(material);setDialog('enable-material')}}>Enable inventory</button><button className="btn-secondary" onClick={async()=>{if(window.confirm(`Archive ${material.name}?`)){try{await apiRequest(`/api/v1/shops/${shopId}/materials/${material.id}/archive/`,{method:'POST',body:{}});await load(true)}catch(cause){setError(cause instanceof Error?cause.message:'Could not archive material.')}}}}>Archive</button></div>}</article>)}</div>}
    {selected&&<section className="info-card" style={{padding:18,marginTop:20}}><div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}><h2><History size={18}/> Stock history — {selected.name}</h2><button className="btn-secondary" onClick={()=>setSelected(null)}>Close</button></div>{movements.length===0?<p>No stock movements.</p>:<div style={{overflowX:'auto'}}><table className="users-table"><thead><tr><th>Date</th><th>Movement</th><th>Quantity</th><th>Before</th><th>After</th><th>Reason</th></tr></thead><tbody>{movements.map(m=><tr key={m.id}><td>{new Date(m.created_at).toLocaleString()}</td><td>{m.movement_type}</td><td>{m.quantity} {m.unit_snapshot}</td><td>{m.on_hand_before}</td><td>{m.on_hand_after}</td><td>{m.reason}</td></tr>)}</tbody></table></div>}</section>}
    {dialog&&<div className="modal-overlay" role="dialog" aria-modal="true"><form className="modal-content" onSubmit={submit}><h2>{dialog==='new-item'?'New inventory item':dialog==='new-material'?'New material':dialog==='enable-material'?'Enable inventory for '+legacyMaterial?.name:dialog==='stock-in'?'Stock in':dialog==='opening'?'Opening stock':'Adjust stock'}</h2>{dialog==='new-item'||dialog==='new-material'?<><label>Name<input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label><label>Code<input value={form.code} onChange={e=>setForm({...form,code:e.target.value})}/></label><label>Description<textarea value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></label>{dialog==='new-item'&&<><label>Category<select value={form.category} onChange={e=>setForm({...form,category:e.target.value})}>{categories.map(x=><option key={x}>{x}</option>)}</select></label><label>Stock unit<select value={form.stock_unit} onChange={e=>setForm({...form,stock_unit:e.target.value})}>{units.map(x=><option key={x}>{x}</option>)}</select></label><p>Opening quantity is a separate stock movement, after the item is created.</p></>}</>:dialog==='enable-material'?<><label>Category<select value={form.category} onChange={e=>setForm({...form,category:e.target.value})}>{categories.map(x=><option key={x}>{x}</option>)}</select></label><label>Stock unit<select value={form.stock_unit} onChange={e=>setForm({...form,stock_unit:e.target.value})}>{units.map(x=><option key={x}>{x}</option>)}</select></label><p>This explicitly classifies an existing Material and creates a zero balance. Opening quantity is added as a separate movement.</p></>:<><label>Quantity<input type="number" min="0.0001" step={selected?.unit==='PIECE'||selected?.unit==='ROLL'?'1':'0.0001'} required value={form.quantity} onChange={e=>setForm({...form,quantity:e.target.value})}/></label><label>Reason<input required maxLength={300} value={form.reason} onChange={e=>setForm({...form,reason:e.target.value})}/></label>{dialog==='adjust'&&<label>Direction<select value={form.direction} onChange={e=>setForm({...form,direction:e.target.value})}><option value="IN">Add stock</option><option value="OUT">Remove stock</option></select></label>}</>}<div className="modal-actions"><button type="button" className="btn-secondary" onClick={()=>setDialog(null)}>Cancel</button><button className="btn-primary" type="submit">Save</button></div></form></div>}
  </div>
}
