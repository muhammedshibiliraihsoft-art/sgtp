import { useEffect, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, ArrowRight, Check, Copy, Plus, Store } from 'lucide-react'
import { shopsService, shopFieldErrors } from '../services/shops'
import type { CreatedShop, CreateShopInput, ShopDetail, ShopSummary } from '../services/shops'
import './backoffice.css'

function ErrorNotice({ message }: { message: string }) {
  return <div className="bo-error" role="alert">{message}</div>
}

function PageHeading({ eyebrow, title, subtitle, action }: {
  eyebrow: string; title: string; subtitle?: string; action?: ReactNode
}) {
  return <div className="bo-page-heading">
    <div><span className="bo-eyebrow">{eyebrow}</span><h1>{title}</h1>{subtitle && <p>{subtitle}</p>}</div>
    {action}
  </div>
}

function Status({ active }: { active: boolean }) {
  const { t } = useTranslation()
  return <span className={`bo-status ${active ? 'bo-status-active' : 'bo-status-inactive'}`}>
    <span aria-hidden="true" />{active ? t('backoffice.active') : t('backoffice.inactive')}
  </span>
}

function ShopOverview({ shop }: { shop: ShopSummary }) {
  const { t } = useTranslation()
  return <>
    <div className="bo-shop-identity"><span className="bo-shop-icon"><Store size={19} /></span>
      <div><strong>{shop.name}</strong><small>{shop.user_count} / {shop.max_users} {t('backoffice.users')}</small></div>
    </div>
    <Status active={shop.is_active} />
    <span className="bo-muted">{shop.default_locale || '—'}</span>
    <span className="bo-muted">{shop.default_currency || '—'}</span>
    <Link className="bo-text-link" to={`/backoffice/shops/${shop.id}`}>{t('backoffice.open')} <ArrowRight size={15} /></Link>
  </>
}

export function BackOfficeDashboard() {
  const { t } = useTranslation()
  return <div className="content-wrap bo-content">
    <PageHeading eyebrow={t('backoffice.eyebrow')} title={t('backoffice.dashboard')}
      subtitle={t('backoffice.dashboardIntro')}
      action={<Link className="primary-button bo-action" to="/backoffice/shops/new"><Plus size={17} />{t('backoffice.createShop')}</Link>} />
    <div className="bo-hero"><div className="bo-hero-icon"><Store size={27} /></div>
      <div><h2>{t('backoffice.manageShops')}</h2><p>{t('backoffice.manageIntro')}</p></div>
      <Link className="bo-secondary-button" to="/backoffice/shops">{t('backoffice.viewShops')} <ArrowRight size={16} /></Link>
    </div>
  </div>
}

export function ShopListPage() {
  const { t } = useTranslation()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [active, setActive] = useState<'all' | 'true' | 'false'>('all')
  const [ordering, setOrdering] = useState<'name' | '-name' | 'created_at' | '-created_at'>('name')
  const [shops, setShops] = useState<ShopSummary[]>([])
  const [count, setCount] = useState(0)
  const [hasNext, setHasNext] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let current = true
    shopsService.list(search, page, { active, ordering }).then((result) => {
      if (!current) return
      setShops(result.results)
      setCount(result.count)
      setHasNext(Boolean(result.next))
      setError('')
    }).catch((cause: unknown) => {
      if (current) setError(cause instanceof Error ? cause.message : t('backoffice.loadFailed'))
    }).finally(() => { if (current) setLoading(false) })
    return () => { current = false }
  }, [search, page, active, ordering, t])

  return <div className="content-wrap bo-content">
    <PageHeading eyebrow={t('backoffice.eyebrow')} title={t('backoffice.shops')}
      subtitle={t('backoffice.shopCount', { count })}
      action={<Link className="primary-button bo-action" to="/backoffice/shops/new"><Plus size={17} />{t('backoffice.createShop')}</Link>} />
    <div className="bo-toolbar"><label htmlFor="bo-shop-search">{t('backoffice.searchShops')}</label>
      <div className="bo-toolbar-controls"><input id="bo-shop-search" type="search" value={search} onChange={event => { setLoading(true); setSearch(event.target.value); setPage(1) }}
        placeholder={t('backoffice.searchPlaceholder')} />
        <label className="bo-filter-field" htmlFor="bo-shop-status">{t('backoffice.filterStatus')}<select id="bo-shop-status" value={active} onChange={event => { setLoading(true); setActive(event.target.value as typeof active); setPage(1) }}><option value="all">{t('backoffice.allShops')}</option><option value="true">{t('backoffice.active')}</option><option value="false">{t('backoffice.inactive')}</option></select></label>
        <label className="bo-filter-field" htmlFor="bo-shop-order">{t('backoffice.sortBy')}<select id="bo-shop-order" value={ordering} onChange={event => { setLoading(true); setOrdering(event.target.value as typeof ordering); setPage(1) }}><option value="name">{t('backoffice.nameAscending')}</option><option value="-name">{t('backoffice.nameDescending')}</option><option value="-created_at">{t('backoffice.newest')}</option><option value="created_at">{t('backoffice.oldest')}</option></select></label>
      </div>
    </div>
    {error && <ErrorNotice message={error} />}
    {loading ? <p className="bo-muted" role="status">{t('backoffice.loading')}</p> : shops.length === 0
      ? <div className="bo-empty"><Store size={24} /><h2>{t('backoffice.noShops')}</h2><p>{t('backoffice.noShopsHint')}</p></div>
      : <>
        <div className="bo-table" role="table" aria-label={t('backoffice.shops')}>
          <div className="bo-table-head" role="row"><span>{t('backoffice.shop')}</span><span>{t('backoffice.status')}</span><span>{t('backoffice.locale')}</span><span>{t('backoffice.currency')}</span><span /></div>
          {shops.map(shop => <div className="bo-table-row" role="row" key={shop.id}><ShopOverview shop={shop} /></div>)}
        </div>
        <div className="bo-mobile-list">{shops.map(shop => <article className="bo-card bo-mobile-shop" key={shop.id}>
          <div className="bo-mobile-shop-top"><div className="bo-shop-identity"><span className="bo-shop-icon"><Store size={19} /></span><div><strong>{shop.name}</strong><small>{shop.user_count} / {shop.max_users} {t('backoffice.users')}</small></div></div><Status active={shop.is_active} /></div>
          <Link className="bo-text-link" to={`/backoffice/shops/${shop.id}`}>{t('backoffice.open')} <ArrowRight size={15} /></Link>
        </article>)}</div>
        <div className="bo-pagination"><button type="button" className="bo-secondary-button" onClick={() => { setLoading(true); setPage(page - 1) }} disabled={page === 1}>{t('backoffice.previous')}</button>
          <span>{t('backoffice.page', { page })}</span><button type="button" className="bo-secondary-button" onClick={() => { setLoading(true); setPage(page + 1) }} disabled={!hasNext}>{t('backoffice.next')}</button></div>
      </>}
  </div>
}

type FieldProps = {
  label: string; name: string; value: string | number; onChange: (value: string) => void
  error?: string; required?: boolean; type?: string; hint?: string; min?: number
}

function Field({ label, name, value, onChange, error, required, type = 'text', hint, min }: FieldProps) {
  return <label className="bo-field" htmlFor={`bo-${name}`}><span>{label}{required && <span aria-hidden="true"> *</span>}</span>
    <input id={`bo-${name}`} name={name} type={type} value={value} onChange={event => onChange(event.target.value)} required={required} min={min} aria-invalid={Boolean(error)} aria-describedby={error ? `bo-${name}-error` : undefined} />
    {hint && <small>{hint}</small>}{error && <small className="bo-field-error" id={`bo-${name}-error`}>{error}</small>}
  </label>
}

const blankCreate: CreateShopInput = {
  name: '', slug: '', max_users: 5,
  first_admin: { first_name: '', last_name: '', email: '', phone: '' },
  contact_email: '', contact_phone: '', default_locale: null, default_timezone: null, default_currency: null,
  address_line1: '', address_line2: '', city: '', state: '', postal_code: '', country: '',
}

export function CreateShopPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [form, setForm] = useState<CreateShopInput>(blankCreate)
  const [created, setCreated] = useState<CreatedShop | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [copied, setCopied] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  const change = (key: keyof CreateShopInput, value: string | number | null) => setForm(previous => ({ ...previous, [key]: value }))
  const changeAdmin = (key: keyof CreateShopInput['first_admin'], value: string) => setForm(previous => ({ ...previous, first_admin: { ...previous.first_admin, [key]: value } }))

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    setFieldErrors({})
    try {
      const response = await shopsService.create({
        ...form,
        name: form.name.trim(), slug: form.slug.trim().toLowerCase(),
        first_admin: { ...form.first_admin, first_name: form.first_admin.first_name.trim(), email: form.first_admin.email.trim(), phone: form.first_admin.phone.trim() },
      })
      setCreated(response)
    } catch (cause: unknown) {
      setFieldErrors(shopFieldErrors(cause))
      setError(cause instanceof Error ? cause.message : t('backoffice.saveFailed'))
    } finally { setBusy(false) }
  }

  const copy = async (value: string, label: string) => {
    try { await navigator.clipboard.writeText(value); setCopied(label) }
    catch { setCopied(t('backoffice.copyFailed')) }
  }

  if (created) return <div className="content-wrap bo-content"><section className="bo-card bo-success" aria-live="polite">
    <div className="bo-success-icon"><Check size={25} /></div><span className="bo-eyebrow">{t('backoffice.eyebrow')}</span>
    <h1>{t('backoffice.createdTitle')}</h1><p>{t('backoffice.createdMessage', { name: created.name })}</p>
    <div className="bo-credential"><span>{t('backoffice.userId')}</span><strong>{created.first_admin_user_code}</strong>
      <button type="button" className="bo-secondary-button" onClick={() => void copy(created.first_admin_user_code, t('backoffice.userId'))}><Copy size={15} />{t('backoffice.copy')}</button></div>
    <div className="bo-credential"><span>{t('backoffice.temporaryPassword')}</span><strong>{showPassword ? created.initial_password : '••••••••••••'}</strong>
      <div className="bo-inline-actions"><button type="button" className="bo-secondary-button" onClick={() => setShowPassword(!showPassword)}>{showPassword ? t('backoffice.hide') : t('backoffice.show')}</button>
        <button type="button" className="bo-secondary-button" onClick={() => void copy(created.initial_password, t('backoffice.temporaryPassword'))}><Copy size={15} />{t('backoffice.copy')}</button></div></div>
    <p className="bo-sensitive-note">{t('backoffice.saveCredentialsNow')}</p>
    {copied && <p className="bo-muted" role="status">{copied === t('backoffice.copyFailed') ? copied : t('backoffice.copied', { item: copied })}</p>}
    <div className="bo-actions"><button type="button" className="bo-secondary-button" onClick={() => void copy(`${created.first_admin_user_code}\n${created.initial_password}`, t('backoffice.both'))}><Copy size={15} />{t('backoffice.copyBoth')}</button>
      <button type="button" className="primary-button" onClick={() => { const id = created.id; setCreated(null); navigate(`/backoffice/shops/${id}`, { replace: true }) }}>{t('backoffice.doneOpenShop')} <ArrowRight size={16} /></button></div>
  </section></div>

  return <div className="content-wrap bo-content">
    <Link className="bo-back" to="/backoffice/shops"><ArrowLeft size={16} />{t('backoffice.backToShops')}</Link>
    <PageHeading eyebrow={t('backoffice.eyebrow')} title={t('backoffice.createShop')} subtitle={t('backoffice.createIntro')} />
    <form className="bo-form" onSubmit={event => void submit(event)}>
      {error && <ErrorNotice message={error} />}
      <section className="bo-card"><div className="bo-section-heading"><span>01</span><div><h2>{t('backoffice.shopDetails')}</h2><p>{t('backoffice.shopDetailsHint')}</p></div></div>
        <div className="bo-form-grid"><Field label={t('backoffice.shopName')} name="name" value={form.name} onChange={value => change('name', value)} error={fieldErrors.name} required />
          <Field label={t('backoffice.slug')} name="slug" value={form.slug} onChange={value => change('slug', value)} error={fieldErrors.slug} hint={t('backoffice.slugHint')} required />
          <Field label={t('backoffice.maxUsers')} name="max_users" type="number" min={1} value={form.max_users} onChange={value => change('max_users', Number(value))} error={fieldErrors.max_users} required /></div></section>
      <section className="bo-card"><div className="bo-section-heading"><span>02</span><div><h2>{t('backoffice.firstAdmin')}</h2><p>{t('backoffice.firstAdminHint')}</p></div></div>
        <div className="bo-form-grid"><Field label={t('backoffice.firstName')} name="first_admin.first_name" value={form.first_admin.first_name} onChange={value => changeAdmin('first_name', value)} error={fieldErrors['first_admin.first_name']} required />
          <Field label={t('backoffice.lastName')} name="first_admin.last_name" value={form.first_admin.last_name || ''} onChange={value => changeAdmin('last_name', value)} error={fieldErrors['first_admin.last_name']} />
          <Field label={t('backoffice.email')} name="first_admin.email" type="email" value={form.first_admin.email} onChange={value => changeAdmin('email', value)} error={fieldErrors['first_admin.email']} required />
          <Field label={t('backoffice.phone')} name="first_admin.phone" type="tel" value={form.first_admin.phone} onChange={value => changeAdmin('phone', value)} error={fieldErrors['first_admin.phone']} hint={t('backoffice.phoneHint')} required /></div></section>
      <section className="bo-card"><div className="bo-section-heading"><span>03</span><div><h2>{t('backoffice.optionalSettings')}</h2><p>{t('backoffice.optionalHint')}</p></div></div>
        <div className="bo-form-grid"><Field label={t('backoffice.contactEmail')} name="contact_email" type="email" value={form.contact_email || ''} onChange={value => change('contact_email', value)} error={fieldErrors.contact_email} />
          <Field label={t('backoffice.contactPhone')} name="contact_phone" type="tel" value={form.contact_phone || ''} onChange={value => change('contact_phone', value)} error={fieldErrors.contact_phone} />
          <Field label={t('backoffice.addressLine1')} name="address_line1" value={form.address_line1 || ''} onChange={value => change('address_line1', value)} error={fieldErrors.address_line1} />
          <Field label={t('backoffice.addressLine2')} name="address_line2" value={form.address_line2 || ''} onChange={value => change('address_line2', value)} error={fieldErrors.address_line2} />
          <Field label={t('backoffice.city')} name="city" value={form.city || ''} onChange={value => change('city', value)} error={fieldErrors.city} />
          <Field label={t('backoffice.state')} name="state" value={form.state || ''} onChange={value => change('state', value)} error={fieldErrors.state} />
          <Field label={t('backoffice.postalCode')} name="postal_code" value={form.postal_code || ''} onChange={value => change('postal_code', value)} error={fieldErrors.postal_code} />
          <Field label={t('backoffice.country')} name="country" value={form.country || ''} onChange={value => change('country', value)} error={fieldErrors.country} />
          <label className="bo-field" htmlFor="bo-default_locale"><span>{t('backoffice.locale')}</span><select id="bo-default_locale" value={form.default_locale || ''} onChange={event => change('default_locale', event.target.value || null)}><option value="">{t('backoffice.useDefault')}</option><option value="en">English</option><option value="ar-KW">العربية</option><option value="bn">বাংলা</option><option value="ur">اردو</option></select></label>
          <Field label={t('backoffice.currency')} name="default_currency" value={form.default_currency || ''} onChange={value => change('default_currency', value.toUpperCase())} error={fieldErrors.default_currency} hint={t('backoffice.currencyHint')} />
          <Field label={t('backoffice.timezone')} name="default_timezone" value={form.default_timezone || ''} onChange={value => change('default_timezone', value)} error={fieldErrors.default_timezone} hint={t('backoffice.timezoneHint')} /></div></section>
      <div className="bo-actions"><Link className="bo-secondary-button" to="/backoffice/shops">{t('backoffice.cancel')}</Link><button className="primary-button" type="submit" disabled={busy}>{busy ? t('backoffice.saving') : t('backoffice.createShop')}</button></div>
    </form>
  </div>
}

type EditDraft = Pick<ShopDetail, 'name' | 'slug' | 'max_users' | 'contact_email' | 'contact_phone' | 'default_locale' | 'default_currency' | 'default_timezone' | 'address_line1' | 'address_line2' | 'city' | 'state' | 'postal_code' | 'country'>

export function ShopDetailPage() {
  const { t } = useTranslation()
  const { shopId } = useParams()
  const [shop, setShop] = useState<ShopDetail | null>(null)
  const [draft, setDraft] = useState<EditDraft | null>(null)
  const [editing, setEditing] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!shopId) return
    let current = true
    shopsService.detail(shopId).then(result => { if (current) { setShop(result); setDraft({ name: result.name, slug: result.slug, max_users: result.max_users, contact_email: result.contact_email, contact_phone: result.contact_phone, default_locale: result.default_locale, default_currency: result.default_currency, default_timezone: result.default_timezone, address_line1: result.address_line1, address_line2: result.address_line2, city: result.city, state: result.state, postal_code: result.postal_code, country: result.country }) } })
      .catch((cause: unknown) => { if (current) setError(cause instanceof Error ? cause.message : t('backoffice.loadFailed')) })
    return () => { current = false }
  }, [shopId, t])

  const change = (key: keyof EditDraft, value: string | number | null) => setDraft(previous => previous ? { ...previous, [key]: value } : previous)

  const save = async (event: FormEvent) => {
    event.preventDefault()
    if (!shopId || !draft) return
    setBusy(true); setError(''); setFieldErrors({})
    try {
      const result = await shopsService.update(shopId, draft)
      setShop(result); setEditing(false)
    } catch (cause: unknown) {
      setFieldErrors(shopFieldErrors(cause))
      setError(cause instanceof Error ? cause.message : t('backoffice.saveFailed'))
    } finally { setBusy(false) }
  }

  const changeActive = async () => {
    if (!shopId || !shop || !window.confirm(t(shop.is_active ? 'backoffice.confirmDeactivate' : 'backoffice.confirmActivate', { name: shop.name }))) return
    setBusy(true); setError('')
    try { await shopsService.setActive(shopId, !shop.is_active); setShop(await shopsService.detail(shopId)) }
    catch (cause: unknown) { setError(cause instanceof Error ? cause.message : t('backoffice.saveFailed')) }
    finally { setBusy(false) }
  }

  return <div className="content-wrap bo-content">
    <Link className="bo-back" to="/backoffice/shops"><ArrowLeft size={16} />{t('backoffice.backToShops')}</Link>
    {error && <ErrorNotice message={error} />}
    {!shop || !draft ? !error && <p role="status" className="bo-muted">{t('backoffice.loading')}</p> : <>
      <PageHeading eyebrow={t('backoffice.eyebrow')} title={shop.name} subtitle={shop.slug}
        action={<Status active={shop.is_active} />} />
      <div className="bo-detail-actions"><button type="button" className="bo-secondary-button" onClick={() => setEditing(!editing)}>{editing ? t('backoffice.cancel') : t('backoffice.editShop')}</button>
        <button type="button" className="bo-secondary-button" disabled={busy} onClick={() => void changeActive()}>{shop.is_active ? t('backoffice.deactivate') : t('backoffice.activate')}</button></div>
      {editing ? <form className="bo-form" onSubmit={event => void save(event)}><section className="bo-card"><h2>{t('backoffice.shopDetails')}</h2><div className="bo-form-grid">
        <Field label={t('backoffice.shopName')} name="name" value={draft.name} onChange={value => change('name', value)} error={fieldErrors.name} required />
        <Field label={t('backoffice.slug')} name="slug" value={draft.slug} onChange={value => change('slug', value)} error={fieldErrors.slug} required />
        <Field label={t('backoffice.maxUsers')} name="max_users" type="number" min={1} value={draft.max_users} onChange={value => change('max_users', Number(value))} error={fieldErrors.max_users} required />
        <Field label={t('backoffice.contactEmail')} name="contact_email" type="email" value={draft.contact_email} onChange={value => change('contact_email', value)} error={fieldErrors.contact_email} />
        <Field label={t('backoffice.contactPhone')} name="contact_phone" type="tel" value={draft.contact_phone} onChange={value => change('contact_phone', value)} error={fieldErrors.contact_phone} />
        <Field label={t('backoffice.addressLine1')} name="address_line1" value={draft.address_line1} onChange={value => change('address_line1', value)} error={fieldErrors.address_line1} />
        <Field label={t('backoffice.addressLine2')} name="address_line2" value={draft.address_line2} onChange={value => change('address_line2', value)} error={fieldErrors.address_line2} />
        <Field label={t('backoffice.city')} name="city" value={draft.city} onChange={value => change('city', value)} error={fieldErrors.city} />
        <Field label={t('backoffice.state')} name="state" value={draft.state} onChange={value => change('state', value)} error={fieldErrors.state} />
        <Field label={t('backoffice.postalCode')} name="postal_code" value={draft.postal_code} onChange={value => change('postal_code', value)} error={fieldErrors.postal_code} />
        <Field label={t('backoffice.country')} name="country" value={draft.country} onChange={value => change('country', value)} error={fieldErrors.country} />
        <label className="bo-field" htmlFor="bo-detail-locale"><span>{t('backoffice.locale')}</span><select id="bo-detail-locale" value={draft.default_locale || ''} onChange={event => change('default_locale', event.target.value || null)}><option value="">{t('backoffice.useDefault')}</option><option value="en">English</option><option value="ar-KW">العربية</option><option value="bn">বাংলা</option><option value="ur">اردو</option></select></label>
        <Field label={t('backoffice.currency')} name="default_currency" value={draft.default_currency || ''} onChange={value => change('default_currency', value.toUpperCase())} error={fieldErrors.default_currency} />
        <Field label={t('backoffice.timezone')} name="default_timezone" value={draft.default_timezone || ''} onChange={value => change('default_timezone', value)} error={fieldErrors.default_timezone} />
      </div></section><div className="bo-actions"><button type="submit" className="primary-button" disabled={busy}>{busy ? t('backoffice.saving') : t('backoffice.saveChanges')}</button></div></form>
        : <div className="bo-card"><h2>{t('backoffice.shopDetails')}</h2><dl className="bo-detail-grid">
          <div><dt>{t('backoffice.shopName')}</dt><dd>{shop.name}</dd></div><div><dt>{t('backoffice.slug')}</dt><dd>{shop.slug}</dd></div>
          <div><dt>{t('backoffice.users')}</dt><dd>{shop.user_count} / {shop.max_users}</dd></div><div><dt>{t('backoffice.locale')}</dt><dd>{shop.default_locale || '—'}</dd></div>
          <div><dt>{t('backoffice.currency')}</dt><dd>{shop.default_currency || '—'}</dd></div><div><dt>{t('backoffice.timezone')}</dt><dd>{shop.default_timezone || '—'}</dd></div>
          <div><dt>{t('backoffice.contactEmail')}</dt><dd>{shop.contact_email || '—'}</dd></div><div><dt>{t('backoffice.contactPhone')}</dt><dd>{shop.contact_phone || '—'}</dd></div>
          <div><dt>{t('backoffice.address')}</dt><dd>{[shop.address_line1, shop.address_line2, shop.city, shop.state, shop.postal_code, shop.country].filter(Boolean).join(', ') || '—'}</dd></div>
          <div><dt>{t('backoffice.createdAt')}</dt><dd>{new Date(shop.created_at).toLocaleDateString()}</dd></div>
        </dl></div>}
    </>}
  </div>
}
