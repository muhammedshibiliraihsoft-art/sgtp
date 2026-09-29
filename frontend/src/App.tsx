import { useEffect, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  ArrowDown, ArrowLeft, ArrowRight, Bell, ChevronDown, CircleHelp,
  ClipboardList, FileText, Globe2, LayoutDashboard,
  Moon, MoreHorizontal, Plus, Search, Settings2, ShieldCheck, Sun,
  UsersRound, WandSparkles,
} from 'lucide-react'
import './App.css'

type Theme = 'light' | 'dark' | 'system'
const themeKey = 'sgtp-theme'

function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem(themeKey)
    return stored === 'light' || stored === 'dark' || stored === 'system' ? stored : 'system'
  })
  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const apply = () => {
      document.documentElement.dataset.theme = theme === 'system' ? (media.matches ? 'dark' : 'light') : theme
    }
    apply()
    media.addEventListener('change', apply)
    localStorage.setItem(themeKey, theme)
    return () => media.removeEventListener('change', apply)
  }, [theme])
  return [theme, setTheme] as const
}

function LanguageMenu() {
  const { i18n } = useTranslation()
  const options = [
    { code: 'en', label: 'English' }, { code: 'ar-KW', label: 'العربية' },
    { code: 'bn', label: 'বাংলা' }, { code: 'ur', label: 'اردو' },
  ]
  return <label className="select-control language-control">
    <Globe2 size={15} aria-hidden="true" />
    <select aria-label="Language" value={i18n.resolvedLanguage || 'en'} onChange={(event) => void i18n.changeLanguage(event.target.value)}>
      {options.map((option) => <option key={option.code} value={option.code}>{option.label}</option>)}
    </select><ChevronDown size={13} aria-hidden="true" />
  </label>
}

function ThemeMenu({ theme, onChange }: { theme: Theme; onChange: (value: Theme) => void }) {
  return <label className="select-control theme-control">
    {theme === 'dark' ? <Moon size={15} aria-hidden="true" /> : <Sun size={15} aria-hidden="true" />}
    <select aria-label="Color theme" value={theme} onChange={(event) => onChange(event.target.value as Theme)}>
      <option value="light">Light</option><option value="dark">Dark</option><option value="system">System</option>
    </select><ChevronDown size={13} aria-hidden="true" />
  </label>
}

function LoginPage() {
  const { t } = useTranslation()
  const [currentYear] = useState(() => new Date().getFullYear())
  const [notice, setNotice] = useState('')
  return <main className="login-page">
    <div className="login-art" aria-hidden="true"><div className="art-mark">s<span>.</span></div><div className="art-stitch" /><p>Crafted with care.<br />Run with clarity.</p><span className="art-caption">SUPPLIER · GARMENT · TAILOR PLATFORM</span></div>
    <section className="login-panel">
      <Link className="brand" to="/" aria-label="SGTP home"><span className="brand-mark">s</span><span>SGTP<span className="brand-dot">.</span></span></Link>
      <div className="login-content"><span className="eyebrow">YOUR WORKSPACE, IN GOOD ORDER</span><h1>{t('welcomeBack')}</h1><p className="muted">Sign in to continue to your tailoring workspace.</p>
        <form onSubmit={(event) => { event.preventDefault(); setNotice('Authentication is not connected in this foundation preview.') }}>
          <label className="field-label" htmlFor="identifier">Email or phone</label><input id="identifier" autoComplete="username" placeholder="Enter your account identifier" />
          <div className="password-label"><label className="field-label" htmlFor="password">Password</label><button className="text-button" type="button" disabled>Forgot password?</button></div><input id="password" type="password" autoComplete="current-password" placeholder="Enter your password" />
          <button className="primary-button sign-in" type="submit">Sign in <ArrowRight size={16} /></button>
          {notice && <p className="preview-notice" role="status">{notice}</p>}
        </form><div className="login-security"><ShieldCheck size={16} /> Sign-in will use approved SGTP authentication</div>
      </div><footer className="login-footer"><span>© {currentYear} SGTP</span><span className="quiet-button"><CircleHelp size={15} /> Help</span></footer>
    </section>
  </main>
}

function Workspace() {
  const [theme, setTheme] = useTheme()
  const location = useLocation()
  const isLogin = location.pathname === '/login'
  if (isLogin) return <LoginPage />
  return <div className="app-shell">
    <aside className="sidebar">
      <Link className="brand sidebar-brand" to="/" aria-label="SGTP home"><span className="brand-mark">s</span><span>SGTP<span className="brand-dot">.</span></span></Link>
      <div className="shop-switcher" aria-label="Sample workspace"><span className="shop-avatar">S</span><span className="shop-copy"><strong>Sample workspace</strong><small>Preview only · no Shop selection</small></span></div>
      <div className="side-label">WORKSPACE</div>
      <nav className="primary-nav" aria-label="Main navigation">
        <NavLink to="/" end className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}><LayoutDashboard size={17} />Overview</NavLink>
        <div className="nav-link nav-disabled" aria-disabled="true" title="Business screens are not part of this foundation task"><UsersRound size={17} />People<span className="nav-soon">Later</span></div>
        <div className="nav-link nav-disabled" aria-disabled="true"><ClipboardList size={17} />Work</div>
        <div className="nav-link nav-disabled" aria-disabled="true"><FileText size={17} />Records</div>
      </nav>
      <div className="sidebar-bottom"><div className="nav-link nav-disabled" aria-disabled="true"><Settings2 size={17} />Preferences</div><div className="nav-link nav-disabled" aria-disabled="true"><CircleHelp size={17} />Help & support</div>
        <div className="profile-wrap"><div className="profile-button"><span className="profile-avatar">P</span><span className="profile-copy"><strong>Preview account</strong><small>No live session</small></span></div><Link className="preview-signin" to="/login">Sign-in preview</Link></div>
      </div>
    </aside>
    <main className="main-area">
      <header className="topbar"><div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><strong>Overview</strong></div><div className="top-actions"><div className="search-box"><Search size={15} /><input aria-label="Search (preview only)" placeholder="Search preview only" disabled /><kbd>⌘ K</kbd></div><LanguageMenu /><ThemeMenu theme={theme} onChange={setTheme} /><button className="icon-button notification-button" aria-label="Notifications (preview only)" disabled><Bell size={17} /></button></div></header>
      <div className="content-wrap">
        <Routes><Route path="*" element={<Overview />} /></Routes>
      </div>
    </main>
  </div>
}

function Overview() {
  const { t } = useTranslation()
  const { i18n } = useTranslation()
  const [today] = useState(() => new Date())
  const ForwardIcon = i18n.dir() === 'rtl' ? ArrowLeft : ArrowRight
  return <div className="overview-page">
    <div className="welcome-row"><div><div className="eyebrow date-line">{new Intl.DateTimeFormat(i18n.resolvedLanguage || 'en', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }).format(today).toLocaleUpperCase(i18n.resolvedLanguage || 'en')} <span>·</span> WORKSPACE PREVIEW</div><h1>{t('goodMorning')}<span className="wave">✳</span></h1><p className="muted">A calm place to bring every detail together.</p></div><Link className="primary-button" to="/login"><Plus size={16} /> Get started</Link></div>
    <div className="preview-banner"><span className="banner-icon"><WandSparkles size={17} /></span><div><strong>Foundation preview</strong><p>This shell is ready for approved workflows. No live business data or backend actions are connected.</p></div><button className="banner-dismiss" aria-label="Dismiss preview notice">×</button></div>
    <section className="section-block"><div className="section-heading"><div><h2>At a glance</h2><p>Workspace indicators will appear here when approved data contracts are available.</p></div><button className="subtle-button" disabled>This week <ArrowDown size={14} /></button></div>
      <div className="metrics-grid"><Metric label="Active work" value="—" note="Waiting for connection" symbol="01"/><Metric label="Ready for pickup" value="—" note="Waiting for connection" symbol="02"/><Metric label="People" value="—" note="Waiting for connection" symbol="03"/><Metric label="To collect" value="—" note="Financial data not connected" symbol="04"/></div>
    </section>
    <section className="lower-grid"><div className="panel activity-panel"><div className="panel-heading"><div><h2>Recent activity</h2><p>Keep up with what is happening.</p></div><button className="icon-button" aria-label="More activity options"><MoreHorizontal size={18}/></button></div><div className="empty-state"><div className="empty-illustration"><span className="empty-ring ring-one"/><span className="empty-ring ring-two"/><ClipboardList size={23}/></div><strong>Your activity will show up here</strong><p>Once connected, recent workspace updates will appear in this space.</p></div></div>
      <div className="panel setup-panel"><div className="panel-heading"><div><h2>Workspace setup</h2><p>A considered start, at your pace.</p></div><span className="setup-count">0 / 3</span></div><div className="setup-list"><SetupItem title="Set up your profile" description="Add the details your team needs."/><SetupItem title="Choose your preferences" description="Language, appearance and more."/><SetupItem title="Invite your team" description="Team access is not connected yet." locked/></div><button className="setup-link">Explore preferences <ForwardIcon size={15}/></button></div></section>
    <footer className="content-footer"><span>Built for the craft.</span><span><span className="footer-dot"/> Secure workspace preview</span></footer>
  </div>
}

function Metric({ label, value, note, symbol }: { label: string; value: string; note: string; symbol: string }) {
  return <article className="metric-card"><div className="metric-top"><span>{label}</span><span className="metric-symbol">{symbol}</span></div><strong className="metric-value">{value}</strong><span className="metric-note">{note}</span></article>
}

function SetupItem({ title, description, locked = false }: { title: string; description: string; locked?: boolean }) {
  return <div className={`setup-item${locked ? ' setup-locked' : ''}`}><span className="setup-check">{locked ? <ShieldCheck size={14}/> : <span/>}</span><span className="setup-copy"><strong>{title}</strong><small>{description}</small></span><ArrowRight size={15} className="setup-arrow"/></div>
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
