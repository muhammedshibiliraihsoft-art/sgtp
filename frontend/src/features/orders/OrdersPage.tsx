import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Archive, ArrowLeft, ChevronRight, ClipboardList, Search } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { ApiError } from '../../services/apiClient'
import { useCurrentShop } from '../../hooks/useCurrentShop'
import { clientsApi } from '../clients/api'
import type { Client, RelatedPerson } from '../clients/types'
import { getAllShopDesigns } from '../designs/api'
import { getAllGlobalDesigns } from '../../backoffice/designs/api'
import type { Design, DesignSelection } from '../designs/types'
import { getShopFamilyOptionGroups } from '../catalog/api'
import type { FamilyOptionGroupConfig } from '../catalog/types'
import { measurementApi } from '../measurements/api'
import type { InventoryFabric, MeasurementProfile, MeasurementSet } from '../measurements/types'
import { getShopMembers, type ShopMember } from '../../services/memberships'
import { ordersApi } from './api'
import type { Order, OrderPriority, OrderStatus } from './types'
import { BillingPanel } from '../billing/BillingPanel'
import './orders.css'

const STAGES: OrderStatus[] = ['REQUEST', 'CUTTING', 'STITCHING', 'CHECK', 'FINISHING', 'QC', 'COMPLETED']
const PRIORITIES: OrderPriority[] = ['NORMAL', 'URGENT', 'VERY_URGENT']
const STAGE_FUNCTION: Partial<Record<OrderStatus, string>> = {
  REQUEST: 'SALES', CUTTING: 'CUTTING', STITCHING: 'STITCHING', CHECK: 'CHECK', FINISHING: 'FINISHING', QC: 'QC',
}
const display = (value: string) => value === 'QC' ? 'QC' : value.replaceAll('_', ' ').toLowerCase().replace(/^./, first => first.toUpperCase())
const errorText = (cause: unknown) => cause instanceof Error ? cause.message : 'Unable to complete this request.'
type DesignChoice = { id: string; name: string; family: string; selections: DesignSelection[] }

function publishedChoices(designs: Design[]): DesignChoice[] {
  return designs.flatMap(design => {
    if (design.status !== 'ACTIVE' || design.family_status !== 'ACTIVE') return []
    const version = design.latest_published_version ?? (design.latest_version?.status === 'PUBLISHED' ? design.latest_version : null)
    return version ? [{ id: version.id, name: `${design.name} · v${version.number}`, family: design.family, selections: version.selections ?? [] }] : []
  })
}

function OrderList({ shopId, canViewDeleted }: { shopId: string; canViewDeleted: boolean }) {
  const { t } = useTranslation()
  const [orders, setOrders] = useState<Order[]>([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<OrderStatus | ''>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const requestId = useRef(0)
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    const timer = window.setTimeout(() => { setPage(1); setSearch(query.trim()) }, 250)
    return () => window.clearTimeout(timer)
  }, [query])
  useEffect(() => {
    const id = ++requestId.current
    setLoading(true); setError('')
    void ordersApi.list(shopId, { page, search, status }).then(result => {
      if (id !== requestId.current) return
      setOrders(result.results); setCount(result.count)
    }).catch(cause => { if (id === requestId.current) setError(errorText(cause)) })
      .finally(() => { if (id === requestId.current) setLoading(false) })
    return () => { requestId.current += 1 }
  }, [shopId, page, search, status, retryCount])

  return <div className="content-wrap orders-page">
    <header className="orders-heading orders-list-heading"><div><span className="orders-eyebrow"><ClipboardList size={16} /> {t('nav.orders')}</span><h1>{t('nav.orders')}</h1><p>{t('orders.subtitle', 'Track each garment from request to completion.')}</p></div>{canViewDeleted && <Link className="orders-secondary orders-archive-link" to="/orders/deleted"><Archive size={16} />{t('orders.archive.title', 'Deleted Orders')}</Link>}</header>
    <div className="orders-toolbar"><label className="orders-search"><Search size={17} /><input value={query} onChange={event => setQuery(event.target.value)} placeholder={t('orders.search', 'Search work number or client')} aria-label={t('orders.search', 'Search work number or client')} /></label><label className="orders-filter">{t('orders.stage', 'Stage')}<select value={status} onChange={event => { setStatus(event.target.value as OrderStatus | ''); setPage(1) }}><option value="">{t('orders.allStages', 'All stages')}</option>{STAGES.map(stage => <option key={stage} value={stage}>{display(stage)}</option>)}</select></label></div>
    {error && <div className="orders-error" role="alert">{error}<button type="button" onClick={() => setRetryCount(current => current + 1)}>{t('orders.retry', 'Retry')}</button></div>}
    {loading ? <p className="orders-empty" role="status">{t('orders.loading', 'Loading orders…')}</p> : error ? null : !orders.length ? <p className="orders-empty">{t('orders.empty', 'No orders found.')}</p> : <div className="orders-grid">{orders.map(order => <Link key={order.id} className="orders-card" to={`/orders/${order.id}`}><div className="orders-card-top"><strong>{order.work_number}</strong><ChevronRight size={18} /></div><span className="orders-stage">{display(order.status)}</span><div className="orders-card-meta"><span>{t('orders.priority', 'Priority')}: {display(order.priority)}</span><span>{order.due_date ? `${t('orders.due', 'Due')} ${order.due_date}` : t('orders.noDueDate', 'No due date')}</span>{order.due_indicator && <span className={`orders-due orders-due-${order.due_indicator.toLowerCase()}`}>{display(order.due_indicator)}</span>}</div></Link>)}</div>}
    {count > 20 && <div className="orders-pages"><button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)}>{t('orders.previous', 'Previous')}</button><span>{page} / {Math.ceil(count / 20)}</span><button type="button" disabled={page * 20 >= count} onClick={() => setPage(page + 1)}>{t('orders.next', 'Next')}</button></div>}
  </div>
}

function OrderCreate({ shopId }: { shopId: string }) {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [clientId, setClientId] = useState(params.get('client') ?? '')
  const [client, setClient] = useState<Client | null>(null)
  const [clientQuery, setClientQuery] = useState('')
  const [clientMatches, setClientMatches] = useState<Client[]>([])
  const [related, setRelated] = useState<RelatedPerson[]>([])
  const [wearerId, setWearerId] = useState(params.get('wearer') ?? '')
  const [designs, setDesigns] = useState<DesignChoice[]>([])
  const [designParts, setDesignParts] = useState<FamilyOptionGroupConfig[]>([])
  const [designPartsLoading, setDesignPartsLoading] = useState(false)
  const [designVersionId, setDesignVersionId] = useState(params.get('design') ?? '')
  const sourceDesignId = params.get('sourceDesign')
  const [profiles, setProfiles] = useState<MeasurementProfile[]>([])
  const [sets, setSets] = useState<MeasurementSet[]>([])
  const [measurementSetId, setMeasurementSetId] = useState(params.get('measurement') ?? '')
  const [fabrics, setFabrics] = useState<InventoryFabric[]>([])
  const [fabricsLoaded, setFabricsLoaded] = useState(false)
  const [fabricLoadError, setFabricLoadError] = useState('')
  const [materialId, setMaterialId] = useState(params.get('material') ?? '')
  const [priority, setPriority] = useState<OrderPriority>('NORMAL')
  const [dueDate, setDueDate] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const chosenDesign = designs.find(item => item.id === designVersionId)
  const locale = ['ar-KW', 'bn', 'ur'].includes(i18n.resolvedLanguage || i18n.language)
    ? (i18n.resolvedLanguage || i18n.language)
    : 'en'
  const validDesignVersionId = chosenDesign?.id ?? ''
  const familyProfiles = profiles.filter(item => item.family === chosenDesign?.family)
  const matchingProfile = familyProfiles.find(item => item.variant === null) ?? (familyProfiles.length === 1 ? familyProfiles[0] : undefined)
  const selectedMaterialExists = fabrics.some(item => item.material_id === materialId)
  const materialNeedsResolution = Boolean(materialId) && (!fabricsLoaded || !selectedMaterialExists)

  useEffect(() => {
    if (!clientId) { setClient(null); setRelated([]); setProfiles([]); return }
    let active = true
    setLoading(true)
    void Promise.all([clientsApi.detail(shopId, clientId), clientsApi.relatedAll(shopId, clientId)]).then(([record, people]) => {
      if (!active) return
      setClient(record); setRelated(people)
    }).catch(cause => { if (active) setError(errorText(cause)) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [shopId, clientId])

  useEffect(() => {
    if (clientQuery.trim().length < 2) { setClientMatches([]); return }
    let active = true
    const timer = window.setTimeout(() => { void clientsApi.list(shopId, clientQuery, 1).then(page => { if (active) setClientMatches(page.results) }).catch(cause => { if (active) setError(errorText(cause)) }) }, 250)
    return () => { active = false; window.clearTimeout(timer) }
  }, [shopId, clientQuery])

  useEffect(() => {
    let active = true
    setFabrics([])
    setFabricsLoaded(false)
    setFabricLoadError('')
    void Promise.all([getAllShopDesigns(shopId, {}, locale), getAllGlobalDesigns(undefined, locale)]).then(([shopDesigns, globalDesigns]) => {
      if (!active) return
      setDesigns(publishedChoices([...shopDesigns, ...globalDesigns]))
    }).catch(cause => { if (active) setError(errorText(cause)) })
    void measurementApi.fabrics(shopId).then(items => {
      if (active) setFabrics(items)
    }).catch(cause => {
      if (active) setFabricLoadError(errorText(cause))
    }).finally(() => {
      if (active) setFabricsLoaded(true)
    })
    return () => { active = false }
  }, [shopId, locale])

  useEffect(() => {
    if (!chosenDesign) { setDesignParts([]); setDesignPartsLoading(false); return }
    let active = true
    setDesignParts([])
    setDesignPartsLoading(true)
    void getShopFamilyOptionGroups(shopId, chosenDesign.family, locale)
      .then(groups => { if (active) setDesignParts(groups) })
      .catch(() => { if (active) setDesignParts([]) })
      .finally(() => { if (active) setDesignPartsLoading(false) })
    return () => { active = false }
  }, [shopId, locale, chosenDesign?.id, chosenDesign?.family])

  useEffect(() => {
    if (!clientId) return
    let active = true
    const owner = wearerId ? { kind: 'related_person' as const, id: wearerId } : { kind: 'client' as const }
    void measurementApi.profiles(shopId, clientId, owner).then(rows => { if (active) setProfiles(rows) }).catch(cause => { if (active) setError(errorText(cause)) })
    return () => { active = false }
  }, [shopId, clientId, wearerId])

  useEffect(() => {
    if (!clientId || !matchingProfile) { setSets([]); return }
    let active = true
    const owner = wearerId ? { kind: 'related_person' as const, id: wearerId } : { kind: 'client' as const }
    void measurementApi.sets(shopId, clientId, owner, matchingProfile.id).then(rows => { if (active) setSets(rows) }).catch(cause => { if (active) setError(errorText(cause)) })
    return () => { active = false }
  }, [shopId, clientId, wearerId, matchingProfile?.id])

  const selectedMeasurement = sets.find(item => item.id === measurementSetId && item.profile === matchingProfile?.id)
  const selectedSet = selectedMeasurement?.id ?? ''
  const selectedGroups = chosenDesign?.selections ?? []
  const designPartsWithSelections = designParts.map(part => ({
    ...part,
    selection: selectedGroups.find(item => item.option_group === part.option_group.id),
  }))
  const unmappedSelections = selectedGroups.filter(selection => !designParts.some(part => part.option_group.id === selection.option_group))
  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!client || !validDesignVersionId || !selectedSet || materialNeedsResolution || saving) return
    setSaving(true); setError('')
    try {
      const order = await ordersApi.create(shopId, {
        client_id: clientId, related_person_id: wearerId || null,
        design_version_id: validDesignVersionId, measurement_set_id: selectedSet,
        material_id: materialId || null, priority, due_date: dueDate || null, notes: notes.trim(),
      })
      navigate(`/orders/${order.id}`, { replace: true })
    } catch (cause) { setError(errorText(cause)) } finally { setSaving(false) }
  }

  return <div className="content-wrap orders-page"><header className="orders-heading"><div><Link className="orders-back" to="/orders"><ArrowLeft size={17} /> {t('nav.orders')}</Link><h1>{t('work.newOrder')}</h1><p>{t('orders.oneGarment', 'One garment creates one order. Choose a published design and saved measurements.')}</p></div></header>
    {error && <p className="orders-error" role="alert">{error}</p>}
    <form className="orders-form" onSubmit={event => void submit(event)}>
      <section className="orders-panel"><h2>01 · {t('orders.client', 'Client and wearer')}</h2>{!client ? <><label>{t('orders.findClient', 'Find client')}<input value={clientQuery} onChange={event => setClientQuery(event.target.value)} placeholder={t('orders.searchClient', 'Enter client name or phone')} /></label><div className="orders-client-results">{clientMatches.map(item => <button key={item.id} type="button" onClick={() => { setClientId(item.id); setWearerId(''); setClientQuery(''); setClientMatches([]) }}>{item.name}<ChevronRight size={17} /></button>)}</div></> : <><div className="orders-selected"><strong>{client.name}</strong><button type="button" onClick={() => { setClientId(''); setWearerId(''); setMeasurementSetId('') }}>{t('orders.change', 'Change')}</button></div><label>{t('orders.wearer', 'Wearer')}<select value={wearerId} onChange={event => { setWearerId(event.target.value); setMeasurementSetId('') }}><option value="">{client.name}</option>{related.map(person => <option key={person.id} value={person.id}>{person.name}</option>)}</select></label></>}{loading && <small>{t('orders.loading', 'Loading…')}</small>}</section>
      <section className="orders-panel"><h2>02 · {t('orders.garment', 'Garment and design')}</h2><label>{t('orders.publishedDesign', 'Published design')}<select value={designVersionId} onChange={event => { const nextDesign = designs.find(item => item.id === event.target.value); setDesignVersionId(event.target.value); if (nextDesign?.family !== chosenDesign?.family) setMeasurementSetId('') }} required><option value="">{t('orders.chooseDesign', 'Choose a published design')}</option>{designs.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>{!designs.length && <p className="orders-help">{t('orders.publishDesign', 'No published design is available. Publish a design version before creating the order.')}</p>}{chosenDesign && <div className="orders-review"><h3>{t('orderReview.designParts')}</h3>{designPartsLoading ? <p className="orders-help" role="status">{t('orderReview.loadingDesign')}</p> : <dl className="orders-summary">{designPartsWithSelections.map(part => <div key={part.id}><dt>{part.option_group.name}</dt><dd>{part.selection ? <>{part.selection.style_option_name} <span className="orders-review-code">({part.selection.selected_code})</span></> : <span className="orders-help">{t('orderReview.noOption')}</span>}</dd></div>)}{unmappedSelections.map(selection => <div key={selection.id}><dt>{selection.style_option_name}</dt><dd>{selection.style_option_name} <span className="orders-review-code">({selection.selected_code})</span></dd></div>)}{!designPartsWithSelections.length && !unmappedSelections.length && <div><dt>{t('orderReview.designParts')}</dt><dd>{t('orderReview.noDesignOptions')}</dd></div>}</dl>}</div>}{sourceDesignId && !designVersionId && <Link to={`/designs/${sourceDesignId}`}>{t('orders.openDesign', 'Open saved design to publish it')}</Link>}</section>
      <section className="orders-panel"><h2>03 · {t('orders.measurements', 'Measurements')}</h2><label>{t('orders.savedVersion', 'Saved measurement version')}<select value={selectedSet} onChange={event => setMeasurementSetId(event.target.value)} disabled={!matchingProfile} required><option value="">{t('orders.chooseMeasurements', 'Choose a saved version')}</option>{sets.filter(item => item.profile === matchingProfile?.id).map(item => <option key={item.id} value={item.id}>Version {item.version} · {item.values.length} values</option>)}</select></label>{client && chosenDesign && !matchingProfile && <p className="orders-help">{t('orders.measureFirst', 'No matching garment measurements were found for this wearer. Save them before creating the order.')}</p>}{selectedMeasurement && <div className="orders-review"><h3>{t('orderReview.measurementValues', { version: selectedMeasurement.version })}</h3>{selectedMeasurement.values.length ? <dl className="orders-summary">{selectedMeasurement.values.map(value => <div key={value.id}><dt>{value.label}</dt><dd>{value.value} {value.unit}</dd></div>)}</dl> : <p className="orders-help">{t('orderReview.noMeasurementValues')}</p>}</div>}{client && <Link to={`/clients/${client.id}/measurements`}>{t('orders.openMeasurements', 'Open Measurements')}</Link>}</section>
      <section className="orders-panel"><h2>04 · {t('orders.delivery', 'Delivery details')}</h2><div className="orders-form-grid"><label>{t('orders.priority', 'Priority')}<select value={priority} onChange={event => setPriority(event.target.value as OrderPriority)}>{PRIORITIES.map(item => <option key={item} value={item}>{display(item)}</option>)}</select></label><label>{t('orders.due', 'Due date')}<input type="date" value={dueDate} onChange={event => setDueDate(event.target.value)} /></label></div><label>{t('orders.fabric', 'Fabric / material (optional)')}<select value={materialId} onChange={event => setMaterialId(event.target.value)}><option value="">{t('orders.noFabric', 'No material selected')}</option>{materialId && !selectedMaterialExists && <option value={materialId}>{t('orders.materialUnverifiedOption', 'Previously selected material (unverified)')}</option>}{fabrics.map(item => <option key={item.material_id} value={item.material_id}>{item.name}</option>)}</select></label>{materialNeedsResolution ? <p className="orders-help" role={fabricsLoaded ? 'alert' : 'status'}>{!fabricsLoaded ? t('orders.materialChecking', 'Checking the preselected material…') : fabricLoadError ? t('orders.materialLoadFailed', 'The preselected material could not be verified. Choose another material or explicitly select No material.') : t('orders.materialUnavailable', 'The preselected material is unavailable. Choose another material or explicitly select No material.')}</p> : !materialId && fabricLoadError ? <p className="orders-help" role="status">{t('orders.materialOptionsFailed', 'Material options could not be loaded. You can still create without a material.')}</p> : null}<label>{t('orders.notes', 'Notes')}<textarea value={notes} onChange={event => setNotes(event.target.value)} maxLength={5000} rows={3} /></label></section>
      <div className="orders-actions"><Link className="orders-secondary" to="/orders">{t('orders.back', 'Back')}</Link><button className="orders-primary" type="submit" disabled={!clientId || !designVersionId || !selectedSet || materialNeedsResolution || saving}>{saving ? t('orders.saving', 'Creating…') : t('orders.create', 'Create order')}</button></div>
    </form>
  </div>
}

function OrderDetail({ shopId, id, isAdmin, canManageBilling, currency, workFunctions }: { shopId: string; id: string; isAdmin: boolean; canManageBilling: boolean; currency: string | null; workFunctions: string[] }) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [order, setOrder] = useState<Order | null>(null)
  const [client, setClient] = useState<Client | null>(null)
  const [members, setMembers] = useState<ShopMember[]>([])
  const [priority, setPriority] = useState<OrderPriority>('NORMAL')
  const [dueDate, setDueDate] = useState('')
  const [notes, setNotes] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const nextStage = order ? STAGES[STAGES.indexOf(order.status) + 1] : undefined
  const canAdvance = Boolean(order && nextStage && (workFunctions.includes(STAGE_FUNCTION[order.status] || '') || (order.status === 'REQUEST' && workFunctions.includes('MEASUREMENT'))))

  useEffect(() => {
    let active = true
    void ordersApi.detail(shopId, id).then(record => { if (active) { setOrder(record); setPriority(record.priority); setDueDate(record.due_date ?? ''); setNotes(record.notes) } }).catch(cause => { if (active) setError(errorText(cause)) })
    if (isAdmin) void getShopMembers(shopId).then(rows => { if (active) setMembers(rows.filter(item => item.is_active && item.role !== 'VIEWER')) }).catch(() => undefined)
    return () => { active = false }
  }, [shopId, id, isAdmin])
  useEffect(() => {
    if (!order) return
    let active = true
    void clientsApi.detail(shopId, order.client_id).then(record => { if (active) setClient(record) }).catch(() => undefined)
    return () => { active = false }
  }, [shopId, order?.client_id])

  const act = async (operation: () => Promise<Order>, message: string) => {
    setBusy(true); setError(''); setNotice('')
    try {
      const updated = await operation()
      setOrder(updated)
      setNotice(message)
    } catch (cause) {
      setError(errorText(cause))
      if (cause instanceof ApiError && cause.status === 409) {
        try { setOrder(await ordersApi.detail(shopId, id)) } catch { /* Keep the conflict visible if refresh also fails. */ }
      }
    } finally { setBusy(false) }
  }
  const remove = async () => {
    if (!order || !window.confirm(t('orders.confirmRemove', 'Remove this Request-stage order?'))) return
    setBusy(true); setError('')
    try { await ordersApi.remove(shopId, order.id); navigate('/orders', { replace: true }) } catch (cause) { setError(errorText(cause)); setBusy(false) }
  }

  return <div className="content-wrap orders-page"><header className="orders-heading"><div><Link className="orders-back" to="/orders"><ArrowLeft size={17} /> {t('nav.orders')}</Link><h1>{order?.work_number ?? t('orders.loading', 'Loading order…')}</h1><p>{order ? `${display(order.status)} · ${display(order.priority)}` : ''}</p></div></header>
    {error && <p className="orders-error" role="alert">{error}</p>}{notice && <p className="orders-notice" role="status">{notice}</p>}
    {order && <div className="orders-detail-grid"><section className="orders-panel"><h2>{t('orders.summary', 'Order summary')}</h2><dl className="orders-summary"><div><dt>{t('orders.client', 'Client')}</dt><dd>{client ? <Link to={`/clients/${client.id}`}>{client.name}</Link> : order.client_id}</dd></div><div><dt>{t('orders.wearer', 'Wearer')}</dt><dd>{order.related_person_id ? t('orders.relatedWearer', 'Related person') : t('orders.primaryClient', 'Client')}</dd></div><div><dt>{t('orders.stage', 'Stage')}</dt><dd>{display(order.status)}</dd></div><div><dt>{t('orders.priority', 'Priority')}</dt><dd>{display(order.priority)}</dd></div><div><dt>{t('orders.due', 'Due date')}</dt><dd>{order.due_date ?? '—'}{order.due_indicator ? ` · ${display(order.due_indicator)}` : ''}</dd></div><div><dt>{t('orders.design', 'Design version')}</dt><dd>{order.design_version_id.slice(0, 8)}</dd></div><div><dt>{t('orders.measurements', 'Measurements')}</dt><dd><Link to={`/clients/${order.client_id}/measurements`}>{t('orders.openMeasurements', 'Open Measurements')}</Link></dd></div><div><dt>{t('orders.fabric', 'Material')}</dt><dd>{order.material_id ? order.material_id.slice(0, 8) : '—'}</dd></div></dl></section>
      <section className="orders-panel"><h2>{t('orders.workflow', 'Workflow')}</h2><ol className="orders-timeline">{STAGES.map((stage, index) => {
        const currentIndex = STAGES.indexOf(order.status)
        const isCurrent = stage === order.status
        const isNext = index === currentIndex + 1
        const stateClass = isCurrent ? 'current' : index < currentIndex ? 'past' : ''
        return <li key={stage} className={stateClass}>{isCurrent ? <span aria-current="step">{display(stage)}</span> : isNext ? <button type="button" className="orders-stage-action" disabled={busy || !canAdvance} onClick={() => void act(() => ordersApi.advance(shopId, id, order.status), t('orders.advanced', 'Moved to the next stage.'))}>{display(stage)}</button> : <span>{display(stage)}</span>}</li>
      })}</ol>{!canAdvance && order.status !== 'COMPLETED' && <p className="orders-help">{t('orders.functionRequired', 'The current stage function and assignment are required to advance.')}</p>}</section>
      {isAdmin && order.status !== 'COMPLETED' && <section className="orders-panel"><h2>{t('orders.manage', 'Manage order')}</h2><label>{t('orders.assign', 'Assign worker')}<select value={order.assigned_membership_id ?? ''} onChange={event => void act(() => ordersApi.assign(shopId, id, event.target.value || null), t('orders.assigned', 'Assignment updated.'))} disabled={busy}><option value="">{t('orders.unassigned', 'Unassigned')}</option>{members.map(item => <option key={item.id} value={item.id}>{item.display_name}</option>)}</select></label><p className="orders-help">{t('orders.assignmentNote', 'The backend checks stage eligibility. Assignment clears after every transition.')}</p><div className="orders-form-grid"><label>{t('orders.priority', 'Priority')}<select value={priority} onChange={event => setPriority(event.target.value as OrderPriority)}>{PRIORITIES.map(item => <option key={item} value={item}>{display(item)}</option>)}</select></label><label>{t('orders.due', 'Due date')}<input type="date" value={dueDate} onChange={event => setDueDate(event.target.value)} /></label></div><label>{t('orders.notes', 'Notes')}<textarea value={notes} onChange={event => setNotes(event.target.value)} maxLength={5000} rows={3} /></label><div className="orders-actions"><button type="button" className="orders-secondary" disabled={busy} onClick={() => void act(() => ordersApi.update(shopId, id, { priority, due_date: dueDate || null, notes: notes.trim() }), t('orders.saved', 'Order updated.'))}>{t('orders.save', 'Save changes')}</button>{order.status === 'REQUEST' && <button type="button" className="orders-danger" disabled={busy} onClick={() => void remove()}>{t('orders.remove', 'Remove request')}</button>}</div></section>}
    </div>}
    {order && <BillingPanel shopId={shopId} workId={order.id} currency={currency} canManage={canManageBilling} />}
  </div>
}

export function OrdersPage() {
  const { id } = useParams<{ id?: string }>()
  const isNew = useLocation().pathname === '/orders/new'
  const { shop, shopId, role, workFunctions, isLoading } = useCurrentShop()
  const canCreate = role === 'ADMIN' || (role === 'STAFF' && (workFunctions.includes('SALES') || workFunctions.includes('MEASUREMENT')))
  if (isLoading) return <div className="content-wrap orders-page" role="status">Loading Shop…</div>
  if (!shopId) return <div className="content-wrap orders-page" role="alert">No Shop context is available.</div>
  if (isNew) return canCreate ? <OrderCreate shopId={shopId} /> : <div className="content-wrap orders-page" role="alert">You do not have permission to create an order.</div>
  return id ? <OrderDetail shopId={shopId} id={id} isAdmin={role === 'ADMIN'} canManageBilling={role === 'ADMIN' || (role === 'STAFF' && workFunctions.includes('CASHIER'))} currency={shop?.default_currency ?? null} workFunctions={workFunctions} /> : <OrderList shopId={shopId} canViewDeleted={role === 'ADMIN'} />
}
