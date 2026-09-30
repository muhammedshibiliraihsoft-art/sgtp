import { useEffect, useState, useRef } from 'react'
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  ArrowRight, Bell, ChevronDown, CircleHelp,
  ClipboardList, Globe2, LayoutDashboard,
  Moon, MoreHorizontal, Plus, Search, Settings2, Sun,
  UsersRound, Scissors, CreditCard, BarChart3, Users,
  Wand2, Store, Sliders, Shirt, PackageOpen, LayoutGrid, X, Clock, ChevronRight
} from 'lucide-react'
import './App.css'
import { BrandLogo } from './components/BrandLogo'


type Theme = 'light' | 'dark' | 'system'
const themeKey = 'sgtp-theme'
export type Palette = 'blue' | 'indigo' | 'violet' | 'teal' | 'emerald' | 'navy' | 'rose' | 'amber'
const paletteKey = 'sgtp-palette'




function usePalette() {
  const [palette, setPalette] = useState<Palette>(() => {
    const stored = localStorage.getItem(paletteKey) as Palette
    return stored || 'blue'
  })
  useEffect(() => {
    document.documentElement.dataset.palette = palette
    localStorage.setItem(paletteKey, palette)
  }, [palette])
  return [palette, setPalette] as const
}



function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem(themeKey)
    return stored === 'light' || stored === 'dark' || stored === 'system' ? stored : 'system'
  })

  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>(() => {
    if (theme !== 'system') return theme as 'light' | 'dark'
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const apply = () => {
      const resolved = theme === 'system' ? (media.matches ? 'dark' : 'light') : theme
      document.documentElement.dataset.theme = resolved
      setResolvedTheme(resolved)
    }
    apply()
    media.addEventListener('change', apply)
    localStorage.setItem(themeKey, theme)
    return () => media.removeEventListener('change', apply)
  }, [theme])

  return [theme, setTheme, resolvedTheme] as const
}

function CustomSelect({ value, options, onChange, icon, ariaLabel }: { value: string, options: {value: string, label: string}[], onChange: (val: string) => void, icon?: React.ReactNode, ariaLabel: string }) {
  const [isOpen, setIsOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const selectedOption = options.find(o => o.value === value)

  return (
    <div ref={ref} className="custom-select">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        className="select-trigger"
      >
        {icon}
        <span className="select-value">{selectedOption ? selectedOption.label : value}</span>
        <ChevronDown size={13} aria-hidden="true" />
      </button>

      {isOpen && (
        <ul className="select-popover" role="listbox">
          {options.map(option => (
            <li
              key={option.value}
              role="option"
              aria-selected={option.value === value}
              className={`select-option ${option.value === value ? 'selected' : ''}`}
              onClick={() => {
                onChange(option.value)
                setIsOpen(false)
              }}
            >
              {option.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function LanguageMenu() {
  const { i18n } = useTranslation()
  const options = [
    { value: 'en', label: 'English' }, { value: 'ar-KW', label: 'العربية' },
    { value: 'bn', label: 'বাংলা' }, { value: 'ur', label: 'اردو' },
  ]
  return <CustomSelect
    value={i18n.resolvedLanguage || 'en'}
    options={options}
    onChange={(val) => void i18n.changeLanguage(val)}
    icon={<Globe2 size={15} />}
    ariaLabel="Language"
  />
}

function ThemeMenu({ theme, onChange }: { theme: Theme; onChange: (value: Theme) => void }) {
  const options = [
    { value: 'light', label: 'Light' },
    { value: 'dark', label: 'Dark' },
    { value: 'system', label: 'System' }
  ]
  return <CustomSelect
    value={theme}
    options={options}
    onChange={(val) => onChange(val as Theme)}
    icon={theme === 'dark' ? <Moon size={15} /> : <Sun size={15} />}
    ariaLabel="Color theme"
  />
}

function PaletteMenu({ palette, onChange }: { palette: Palette; onChange: (value: Palette) => void }) {
  const options = [
    { value: 'blue', label: 'Blue' }, { value: 'indigo', label: 'Indigo' },
    { value: 'violet', label: 'Violet' }, { value: 'teal', label: 'Teal' },
    { value: 'emerald', label: 'Emerald' }, { value: 'navy', label: 'Navy' },
    { value: 'rose', label: 'Rose' }, { value: 'amber', label: 'Amber' }
  ]
  return <CustomSelect
    value={palette}
    options={options}
    onChange={(val) => onChange(val as Palette)}
    ariaLabel="Palette"
  />
}


function LoginPage({ palette, resolvedTheme }: { palette: Palette, resolvedTheme: 'light' | 'dark' }) {
  const { t } = useTranslation()
  const [currentYear] = useState(() => new Date().getFullYear())
  const [notice, setNotice] = useState('')
  return <main className="login-page">
    <div className="login-art" aria-hidden="true"><div className="art-mark">s<span>.</span></div><div className="art-stitch" /><p>Crafted with care.<br />Run with clarity.</p><span className="art-caption">SUPPLIER · GARMENT · TAILOR PLATFORM</span></div>
    <section className="login-panel">
      <Link to="/" style={{ textDecoration: "none" }}><BrandLogo palette={palette} resolvedTheme={resolvedTheme} /></Link>
      <div className="login-content"><h1>{t('welcomeBack')}</h1><p className="muted" style={{ marginBottom: '30px' }}>Sign in to continue to your tailoring workspace.</p>
        <form onSubmit={(event) => { event.preventDefault(); setNotice('Authentication is not connected in this foundation preview.') }}>
          <label className="field-label" htmlFor="identifier">Email or phone</label><input id="identifier" autoComplete="username" placeholder="Enter your account identifier" />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><label className="field-label" htmlFor="password">Password</label><button className="icon-button" style={{ width: 'auto', fontSize: '12px', color: 'var(--color-primary)' }} type="button" disabled>Forgot?</button></div><input id="password" type="password" autoComplete="current-password" placeholder="Enter your password" />
          <button className="primary-button sign-in" type="submit">Sign in <ArrowRight size={16} /></button>
          {notice && <p style={{ marginTop: '8px', padding: '8px', background: 'var(--color-warning-soft)', borderRadius: '8px', fontSize: '11px', color: 'var(--color-warning)' }} role="status">{notice}</p>}
        </form>
      </div><footer style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--color-text-muted)' }}><span>© {currentYear} SGTP</span><span>Help</span></footer>
    </section>
  </main>
}

function DesktopSidebar({ palette, resolvedTheme }: { palette: Palette, resolvedTheme: 'light' | 'dark' }) {
  const { t } = useTranslation()
  return (
    <aside className="desktop-sidebar">
      <Link to="/" style={{ textDecoration: "none" }}><BrandLogo palette={palette} resolvedTheme={resolvedTheme} /></Link>

      <nav style={{ marginTop: '32px', flex: 1 }} aria-label="Main navigation">
        <NavLink to="/" end className={({ isActive }) => `nav-link-desktop${isActive ? ' active' : ''}`}><LayoutDashboard size={18} /> {t('nav.dashboard')}</NavLink>
        <NavLink to="/work" className={({ isActive }) => `nav-link-desktop${isActive ? ' active' : ''}`}><Scissors size={18} /> {t('nav.work')}</NavLink>
        <div className="nav-link-desktop nav-disabled" aria-disabled="true"><ClipboardList size={18} /> {t('nav.orders')}</div>
        <div className="nav-link-desktop nav-disabled" aria-disabled="true"><UsersRound size={18} /> {t('nav.clients')}</div>
        <div className="nav-link-desktop nav-disabled" aria-disabled="true"><CreditCard size={18} /> {t('nav.billing')}</div>
      </nav>

      <div style={{ paddingBottom: '16px' }}>
        <div className="nav-link-desktop nav-disabled" aria-disabled="true"><Settings2 size={18} /> Settings</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--color-border)' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--color-primary-soft)', color: 'var(--color-primary)', display: 'grid', placeItems: 'center', fontSize: '12px', fontWeight: 'bold' }}>AR</div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '12px', fontWeight: 600 }}>Ahammed Rafi</span>
            <span style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>Shop Admin</span>
          </div>
        </div>
      </div>
    </aside>
  )
}

function TopHeader({ theme, setTheme, palette, setPalette }: { theme: Theme, setTheme: (v: Theme) => void, palette: Palette, setPalette: (v: Palette) => void }) {
  return (
    <header className="topbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Store size={20} className="header-mobile-only" />
        <span style={{ fontSize: '14px', fontWeight: 600 }}>Modern Tailors <ChevronDown size={14} style={{ display: 'inline' }} /></span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div className="search-box header-desktop-only">
          <Search size={14} />
          <input aria-label="Search" placeholder="Search orders, clients..." disabled />
        </div>
        <button className="icon-button header-mobile-only" aria-label="Search"><Search size={18} /></button>
        <div className="header-desktop-only" style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <LanguageMenu />
          <ThemeMenu theme={theme} onChange={setTheme} />
          <PaletteMenu palette={palette} onChange={setPalette} />
        </div>
        <button className="icon-button" aria-label="Notifications" disabled style={{ position: 'relative' }}>
          <Bell size={18} />
          <span style={{ position: 'absolute', top: '6px', right: '6px', width: '6px', height: '6px', borderRadius: '50%', background: 'var(--color-danger)' }} />
        </button>
        <div className="header-mobile-only" style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--color-primary-soft)', color: 'var(--color-primary)', display: 'grid', placeItems: 'center', fontSize: '12px', fontWeight: 'bold' }}>AR</div>
      </div>
    </header>
  )
}

function BottomNavigation({ onMoreClick }: { onMoreClick: () => void }) {
  const { t } = useTranslation()
  return (
    <nav className="bottom-nav">
      <NavLink to="/" end className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}><LayoutDashboard size={20} />{t('nav.dashboard')}</NavLink>
      <NavLink to="/work" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}><Scissors size={20} />{t('nav.work')}</NavLink>
      <div className="nav-item nav-disabled" aria-disabled="true"><ClipboardList size={20} />{t('nav.orders')}</div>
      <div className="nav-item nav-disabled" aria-disabled="true"><UsersRound size={20} />{t('nav.clients')}</div>
      <button className="nav-item" onClick={onMoreClick}><MoreHorizontal size={20} />{t('nav.more')}</button>
    </nav>
  )
}

function MoreSheet({ isOpen, onClose, theme, setTheme }: { isOpen: boolean, onClose: () => void, theme: Theme, setTheme: (v: Theme) => void }) {
  const { t } = useTranslation()
  if (!isOpen) return null;
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 50, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', background: 'rgba(0,0,0,0.4)' }} onClick={onClose}>
      <div style={{ background: 'var(--color-surface)', borderTopLeftRadius: '24px', borderTopRightRadius: '24px', padding: '24px', paddingBottom: 'calc(24px + env(safe-area-inset-bottom))', display: 'flex', flexDirection: 'column', gap: '24px', maxHeight: '90vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
        <div style={{ width: '36px', height: '4px', borderRadius: '2px', background: 'var(--color-border)', margin: '0 auto' }} />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '20px', fontWeight: 600, margin: 0 }}>{t('nav.more')}</h2>
          <button className="icon-button" onClick={onClose}><X size={20} /></button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-primary)' }}><CreditCard size={24} /><span style={{ fontSize: '12px', color: 'var(--color-text)', fontWeight: 500 }}>{t('more.billing')}</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-primary)' }}><BarChart3 size={24} /><span style={{ fontSize: '12px', color: 'var(--color-text)', fontWeight: 500 }}>{t('more.reports')}</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-primary)' }}><Users size={24} /><span style={{ fontSize: '12px', color: 'var(--color-text)', fontWeight: 500 }}>{t('more.members')}</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-primary)' }}><LayoutGrid size={24} /><span style={{ fontSize: '12px', color: 'var(--color-text)', fontWeight: 500 }}>{t('more.workFunctions')}</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-primary)' }}><Settings2 size={24} /><span style={{ fontSize: '12px', color: 'var(--color-text)', fontWeight: 500 }}>{t('more.settings')}</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-primary)' }}><Store size={24} /><span style={{ fontSize: '12px', color: 'var(--color-text)', fontWeight: 500 }}>{t('more.shopProfile')}</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-primary)' }}><Sliders size={24} /><span style={{ fontSize: '12px', color: 'var(--color-text)', fontWeight: 500 }}>{t('more.preferences')}</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-primary)' }}><CircleHelp size={24} /><span style={{ fontSize: '12px', color: 'var(--color-text)', fontWeight: 500 }}>{t('more.help')}</span></div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '8px', paddingTop: '16px', borderTop: '1px solid var(--color-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--color-primary-soft)', color: 'var(--color-primary)', display: 'grid', placeItems: 'center', fontSize: '14px', fontWeight: 'bold' }}>AR</div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '14px', fontWeight: 600 }}>Ahammed Rafi</span>
              <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Shop Admin</span>
            </div>
          </div>
          <button className="icon-button" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
             {theme === 'dark' ? <Moon size={20} /> : <Sun size={20} />}
          </button>
        </div>
      </div>
    </div>
  )
}

function WorkPreviewPage() {
  const { t } = useTranslation()
  const visibleCount = 2

  const renderCard = (id: string, name: string, user: string, badge: string, badgeType: string) => (
    <div key={id} className="work-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', gap: '12px' }}>
          <div style={{ color: 'var(--color-primary)', paddingTop: '4px' }}><Shirt size={24} strokeWidth={1.5} /></div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>{id}</span>
            <strong style={{ fontSize: '13px', fontWeight: 600 }}>{name}</strong>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '2px' }}>{user}</span>
          </div>
        </div>
        <button className="icon-button" style={{ width: '24px', height: '24px' }}><MoreHorizontal size={16} /></button>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
        <span style={{ padding: '2px 8px', borderRadius: '12px', fontSize: '10px', fontWeight: 600 }} className={`badge-${badgeType}`}>{badge}</span>
        <div style={{ width: '20px', height: '20px', borderRadius: '50%', background: 'var(--color-surface-subtle)', display: 'grid', placeItems: 'center', fontSize: '9px', fontWeight: 'bold', color: 'var(--color-text-muted)' }}>AB</div>
      </div>
    </div>
  )

  const MOCK_STAGES = {
    cutting: { title: t('work.stages.cutting'), icon: <Scissors size={18} />, total: 8, records: [{ id: '#ORD-1024', name: "Men's Shirt", user: 'Fathima', badge: 'New', badgeType: 'new' }, { id: '#ORD-1021', name: "Kids Frock", user: 'Sameera', badge: 'New', badgeType: 'new' }, { id: '#ORD-1018', name: "Dress", user: 'Ali', badge: 'New', badgeType: 'new' }] },
    stitching: { title: t('work.stages.stitching'), icon: <Wand2 size={18} />, total: 7, records: [{ id: '#ORD-1015', name: "Abaya", user: 'Shahana', badge: 'Active', badgeType: 'active' }, { id: '#ORD-1011', name: "Kurta", user: 'Faisal', badge: 'Active', badgeType: 'active' }, { id: '#ORD-1009', name: "Pants", user: 'Zara', badge: 'Active', badgeType: 'active' }] },
    finishing: { title: t('work.stages.finishing'), icon: <LayoutGrid size={18} />, total: 5, records: [{ id: '#ORD-1007', name: "Wedding Dress", user: 'Ramees', badge: 'Review', badgeType: 'review' }, { id: '#ORD-1004', name: "Shirt", user: 'Junaid', badge: 'Review', badgeType: 'review' }, { id: '#ORD-1002', name: "Suit", user: 'Tariq', badge: 'Review', badgeType: 'review' }] },
    ready: { title: t('work.stages.ready'), icon: <PackageOpen size={18} />, total: 4, records: [{ id: '#ORD-0991', name: "Thobe", user: 'Ibrahim', badge: 'Ready', badgeType: 'ready' }, { id: '#ORD-0987', name: "Saree Blouse", user: 'Naseema', badge: 'Ready', badgeType: 'ready' }, { id: '#ORD-0985', name: "Jacket", user: 'Omar', badge: 'Ready', badgeType: 'ready' }] }
  }

  const renderStage = (key: keyof typeof MOCK_STAGES) => {
    const stage = MOCK_STAGES[key]
    const visibleRecords = stage.records.slice(0, visibleCount)
    const remaining = stage.total - visibleRecords.length

    return (
      <div className="work-column">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 600, color: 'var(--color-primary)' }}>{stage.icon} {stage.title}</div>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)' }}>{stage.total}</span>
        </div>
        {visibleRecords.map(r => renderCard(r.id, r.name, r.user, r.badge, r.badgeType))}
        {remaining > 0 && (
          <button className="more-affordance" aria-label={`Show ${remaining} more ${stage.title} records`}>
            <div className="more-affordance-icon">
              <Plus size={14} strokeWidth={2.5} />
            </div>
            <span className="more-affordance-text">{t('work.more', { count: remaining })}</span>
            <ChevronRight size={14} className="more-affordance-chevron" />
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="content-wrap">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '32px', fontWeight: 600, margin: '0 0 8px 0', letterSpacing: '-0.5px' }}>{t('work.title')}</h1>
          <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '14px' }}>{t('work.subtitle')}</p>
        </div>
        <button className="primary-button"><Plus size={16} /> {t('work.newOrder')}</button>
      </div>

      <div className="phone-stage-selector">
        {(Object.keys(MOCK_STAGES) as Array<keyof typeof MOCK_STAGES>).map(key => {
          const stage = MOCK_STAGES[key]
          return (
            <button key={key} className="phone-stage-card" aria-label={`${stage.title}, ${stage.total} items`}>
              <div className="stage-icon-wrap">{stage.icon}</div>
              <div className="stage-info">
                <span className="stage-title">{stage.title}</span>
                <span className="stage-count">{stage.total}</span>
              </div>
            </button>
          )
        })}
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-primary)', fontSize: '13px', fontWeight: 500 }}><ClipboardList size={16} /> {t('work.metrics.newOrders')}</div>
          <span className="metric-value">24</span>
          <span className="metric-note">Across your pipeline</span>
        </div>
        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-info)', fontSize: '13px', fontWeight: 500 }}><Settings2 size={16} /> {t('work.metrics.inProgress')}</div>
          <span className="metric-value">8</span>
          <span className="metric-note">Currently in production</span>
        </div>
        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-success)', fontSize: '13px', fontWeight: 500 }}><PackageOpen size={16} /> {t('work.metrics.ready')}</div>
          <span className="metric-value">12</span>
          <span className="metric-note">This week</span>
        </div>
        <div className="metric-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-warning)', fontSize: '13px', fontWeight: 500 }}><Clock size={16} /> {t('work.metrics.overdue')}</div>
          <span className="metric-value">3</span>
          <span className="metric-note">Needs attention</span>
        </div>
      </div>

      <div className="work-board">
        {renderStage('cutting')}
        {renderStage('stitching')}
        {renderStage('finishing')}
        {renderStage('ready')}
      </div>
    </div>
  )
}

function Workspace() {
  const [theme, setTheme, resolvedTheme] = useTheme()
  const [palette, setPalette] = usePalette()
  const location = useLocation()
  const [isMoreOpen, setIsMoreOpen] = useState(false)
  const isLogin = location.pathname === '/login'

  useEffect(() => { setIsMoreOpen(false) }, [location.pathname])

  if (isLogin) return <LoginPage palette={palette} resolvedTheme={resolvedTheme} />

  return <div className="app-shell">
    <DesktopSidebar palette={palette} resolvedTheme={resolvedTheme} />
    <main className="main-area">
      <TopHeader theme={theme} setTheme={setTheme} palette={palette} setPalette={setPalette} />
      <Routes>
        <Route path="/work" element={<WorkPreviewPage />} />
        <Route path="*" element={<div className="content-wrap"><h1 style={{fontSize:'24px'}}>{location.pathname === '/' ? 'Dashboard' : 'Preview'}</h1><p style={{color:'var(--color-text-muted)'}}>Navigate to Work to see the layout.</p><Link to="/work" style={{color:'var(--color-primary)'}}>Go to Work</Link></div>} />
      </Routes>
    </main>
    <BottomNavigation onMoreClick={() => setIsMoreOpen(true)} />
    <MoreSheet isOpen={isMoreOpen} onClose={() => setIsMoreOpen(false)} theme={theme} setTheme={setTheme} />
  </div>
}

export default function App() {
  const { i18n } = useTranslation()
  useEffect(() => {
    const language = i18n.resolvedLanguage || 'en'
    document.documentElement.lang = language
    document.documentElement.dir = i18n.dir(language)
  }, [i18n, i18n.resolvedLanguage])
  return <Workspace />
}
