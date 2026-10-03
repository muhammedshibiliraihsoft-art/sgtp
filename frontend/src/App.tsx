import { useEffect, useState, useRef } from 'react'
import { Link, Navigate, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  ArrowRight, Bell, ChevronDown, CircleHelp,
  ClipboardList, Globe2, LayoutDashboard,
  Moon, MoreHorizontal, Plus, Search, Settings2, LogOut, ChevronUp, Sun,
  UsersRound, Scissors, CreditCard, BarChart3, Users,
  Wand2, Store, Sliders, Shirt, PackageOpen, LayoutGrid, X, Clock, ChevronRight,
  PanelLeftClose, PanelLeftOpen, Shield, Ruler
} from 'lucide-react'
import { UsersPage } from './features/users/UsersPage'
import './App.css'
import { BrandLogo } from './components/BrandLogo'
import { AuthProvider } from './services/AuthContext'
import { useAuth } from './services/useAuth'
import { BackOfficeDashboard, CreateShopPage, ShopDetailPage, ShopListPage } from './backoffice/BackOfficePages'
import { ClientsPage } from './features/clients/ClientsPage'
import { ClientDetailPage } from './features/clients/ClientDetailPage'
import desktopImg from './assets/images/login/desktop.png'
import phoneImg from './assets/images/login/phone.png'
import tabletPortraitImg from './assets/images/login/tablet-portrait.png'
import tabletLandscapeImg from './assets/images/login/tablet-landscape.png'
import sidebarLogo from './assets/brand/sidebar_logo.png'
import { CatalogPage } from './features/catalog/CatalogPage'
import { DesignsPage } from './features/designs/DesignsPage'
import { DesignEditor } from './features/designs/DesignEditor'
import { GlobalCatalogPage } from './backoffice/catalog/GlobalCatalogPage'
import { GlobalDesignTemplatesPage } from './backoffice/designs/GlobalDesignTemplatesPage'
import { GlobalTemplateEditor } from './backoffice/designs/GlobalTemplateEditor'
import { MaterialsInventoryPage } from './features/materials/MaterialsInventoryPage'
import { ClientMeasurementsPage } from './features/measurements/ClientMeasurementsPage'

type Theme = 'light' | 'dark' | 'system'
const themeKey = 'sgtp-theme'
export type Palette = 'default' | 'blue' | 'indigo' | 'violet' | 'teal' | 'navy'
const paletteKey = 'sgtp-palette'

function usePalette() {
  const [palette, setPalette] = useState<Palette>(() => {
    const stored = localStorage.getItem(paletteKey)
    const validPalettes = ['default', 'blue', 'indigo', 'violet', 'teal', 'navy']
    if (stored && validPalettes.includes(stored)) {
      return stored as Palette
    }
    return 'default'
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
    { value: 'default', label: 'Default' },
    { value: 'blue', label: 'Blue' }, { value: 'indigo', label: 'Indigo' },
    { value: 'violet', label: 'Violet' }, { value: 'teal', label: 'Teal' },
    { value: 'navy', label: 'Navy' }
  ]
  return <CustomSelect
    value={palette}
    options={options}
    onChange={(val) => onChange(val as Palette)}
    ariaLabel="Palette"
  />
}


function LoginPage() {
  const { t } = useTranslation()
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')

    if (!identifier.trim()) {
      setError('Please enter your User ID, email, or phone number.')
      return
    }
    if (!password) {
      setError('Please enter your password.')
      return
    }

    setIsLoading(true)
    try {
      const mustChangePassword = await signIn(identifier.trim(), password)
      navigate(mustChangePassword ? '/password-change' : '/', { replace: true })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to sign in right now. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="login-page">
      <div className="login-card">

        {/* Mobile-only Top Logo */}
        <div className="login-logo-slot mobile-top-logo">
          <BrandLogo layout="login" />
        </div>

        {/* Visual / Image Slot */}
        <div className="login-visual-slot" aria-hidden="true">
          <div className="login-visual-placeholder">
            <img src={phoneImg} alt="" className="login-img-phone" />
            <img src={tabletPortraitImg} alt="" className="login-img-tablet-portrait" />
            <img src={tabletLandscapeImg} alt="" className="login-img-tablet-landscape" />
            <img src={desktopImg} alt="" className="login-img-desktop" />
          </div>
        </div>

        {/* Form Area */}
        <section className="login-form-area">
          <div className="login-form-container">
            {/* Tablet/Desktop Form Logo */}
            <div className="login-logo-slot desktop-form-logo">
              <BrandLogo layout="login" />
            </div>

            <div className="login-header">
              <h1>{t('welcomeBack') === 'welcomeBack' ? 'Welcome back 👋' : t('welcomeBack')}</h1>
              <p className="login-subtitle">
                {t('login.subtitle') === 'login.subtitle' ? 'Please enter your email, phone number or username to continue.' : t('login.subtitle')}
              </p>
            </div>

            <form className="login-form" onSubmit={handleSubmit}>
              {error && (
                <div className="login-error-message" role="alert">
                  {error}
                </div>
              )}

              <div className="form-group">
                <div className="input-with-icon">
                  <UsersRound className="input-icon" size={18} aria-hidden="true" />
                  <input
                    id="identifier"
                    type="text"
                    autoComplete="username"
                    placeholder="Email / Phone / Username"
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    disabled={isLoading}
                    aria-label="User ID, Email, or Phone"
                  />
                </div>
              </div>

              <div className="form-group">
                <div className="input-with-icon">
                  <Settings2 className="input-icon" size={18} aria-hidden="true" />
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isLoading}
                    aria-label="Password"
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    <CircleHelp size={18} />
                  </button>
                </div>
              </div>

              <div className="form-actions">
                <span className="spacer"></span>
                <button
                  type="button"
                  className="forgot-password-link"
                  style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                  onClick={() => alert('FOLLOW-UP AUTH SCREEN REQUIRED — PASSWORD RESET')}
                >
                  Forgot password?
                </button>
              </div>

              <button className="primary-button submit-button" type="submit" disabled={isLoading}>
                {isLoading ? 'Logging in...' : 'Log in'} <ArrowRight size={18} />
              </button>
            </form>
          </div>

          <footer className="login-footer">
             {/* No "Sign up" per backend contract */}
          </footer>
        </section>

      </div>
    </main>
  )
}

function PasswordChangePage() {
  const { changePassword } = useAuth()
  const navigate = useNavigate()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      await changePassword(currentPassword, newPassword, confirmPassword)
      navigate('/login', { replace: true, state: { notice: 'Password changed. Sign in with your new password.' } })
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : 'Unable to change your password. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return <main className="login-page"><section className="login-form-area"><div className="login-form-container">
    <div className="login-header"><h1>Change your password</h1><p className="login-subtitle">Set a new password before continuing.</p></div>
    <form className="login-form" onSubmit={submit}>
      {error && <div className="login-error-message" role="alert">{error}</div>}
      <label className="field-label" htmlFor="current-password">Current password</label>
      <input id="current-password" type="password" autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required disabled={isLoading} />
      <label className="field-label" htmlFor="new-password">New password</label>
      <input id="new-password" type="password" autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required disabled={isLoading} />
      <label className="field-label" htmlFor="confirm-password">Confirm new password</label>
      <input id="confirm-password" type="password" autoComplete="new-password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required disabled={isLoading} />
      <button className="primary-button submit-button" type="submit" disabled={isLoading}>{isLoading ? 'Saving...' : 'Change password'}</button>
    </form>
  </div></section></main>
}

function SidebarContainer({ 
  isPinned, setIsPinned, 
  children,
  isAccountPopoverOpen
}: { 
  isPinned: boolean, 
  setIsPinned: (v: boolean) => void,
  children: React.ReactNode,
  isAccountPopoverOpen?: boolean
}) {
  const [isPeek, setIsPeek] = useState(false);
  const status = useRef({ hovered: false, focused: false });
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const evaluateState = (delay: number) => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      const active = status.current.hovered || status.current.focused || !!isAccountPopoverOpen;
      setIsPeek(active);
    }, delay);
  };

  useEffect(() => {
    evaluateState(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAccountPopoverOpen]);

  useEffect(() => {
    return () => clearTimeout(timer.current);
  }, []);

  const handleMouseEnter = () => {
    status.current.hovered = true;
    evaluateState(150);
  };

  const handleMouseLeave = () => {
    status.current.hovered = false;
    evaluateState(250);
  };

  const handleFocus = () => {
    status.current.focused = true;
    evaluateState(0);
  };

  const handleBlur = (e: React.FocusEvent) => {
    if (!e.currentTarget.contains(e.relatedTarget)) {
      status.current.focused = false;
      evaluateState(250);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape' && isPeek && !isPinned) {
      status.current.hovered = false;
      status.current.focused = false;
      setIsPeek(false);
      (document.activeElement as HTMLElement)?.blur();
    }
  };

  const isExpanded = isPinned || isPeek;
  const stateClass = isPinned ? 'pinned' : isPeek ? 'peek' : 'collapsed';

  return (
    <>
      <div className={`desktop-sidebar-spacer ${stateClass}`} aria-hidden="true" />
      <aside 
        className={`desktop-sidebar ${stateClass}`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={handleFocus}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
      >
        <div className="sidebar-brand-header">
          <img src={sidebarLogo} alt="BirkOS" className="sidebar-logo-img" />
          <button 
            className="sidebar-toggle-btn"
            onClick={() => {
              const newPinned = !isPinned;
              setIsPinned(newPinned);
              if (!newPinned) {
                status.current.hovered = false;
                setIsPeek(false);
              }
            }}
            aria-expanded={isExpanded}
            aria-label={isPinned ? "Collapse sidebar" : "Expand sidebar"}
            title={isPinned ? "Collapse sidebar" : "Expand sidebar"}
          >
            {isPinned ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
          </button>
        </div>
        {children}
      </aside>
    </>
  );
}

function DesktopSidebar({ isPinned, setIsPinned }: { isPinned: boolean, setIsPinned: (v: boolean) => void }) {
  const { t } = useTranslation()
  const { signOut, user } = useAuth()
  const navigate = useNavigate()
  const [isAccountOpen, setIsAccountOpen] = useState(false)
  const accountRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (accountRef.current && !accountRef.current.contains(event.target as Node)) {
        setIsAccountOpen(false)
      }
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') setIsAccountOpen(false)
    }
    if (isAccountOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      document.addEventListener('keydown', handleEscape)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isAccountOpen])

  return (
    <SidebarContainer isPinned={isPinned} setIsPinned={setIsPinned} isAccountPopoverOpen={isAccountOpen}>
      <nav style={{ flex: 1 }} aria-label="Main navigation">
        <NavLink to="/" end className={({ isActive }) => `nav-link-desktop${isActive ? ' active' : ''}`}><LayoutDashboard size={18} /> <span className="nav-label">{t('nav.dashboard')}</span></NavLink>
        <NavLink to="/work" className={({ isActive }) => `nav-link-desktop${isActive ? ' active' : ''}`}><Scissors size={18} /> <span className="nav-label">{t('nav.work')}</span></NavLink>
        <div className="nav-link-desktop nav-disabled" aria-disabled="true"><ClipboardList size={18} /> <span className="nav-label">{t('nav.orders')}</span></div>
        <NavLink to="/designs" className={({ isActive }) => `nav-link-desktop${isActive ? ' active' : ''}`}><Wand2 size={18} /> <span className="nav-label">{t('nav.designs', 'Designs')}</span></NavLink>
        <NavLink to="/catalog" className={({ isActive }) => `nav-link-desktop${isActive ? ' active' : ''}`}><Shirt size={18} /> <span className="nav-label">{t('nav.catalog', 'Catalog')}</span></NavLink>
        <NavLink to="/clients" className={({ isActive }) => `nav-link-desktop${isActive ? ' active' : ''}`}><UsersRound size={18} /> <span className="nav-label">{t('nav.clients')}</span></NavLink>
        <div className="nav-link-desktop nav-disabled" aria-disabled="true"><CreditCard size={18} /> <span className="nav-label">{t('nav.billing')}</span></div>
        <NavLink to="/users" className={({ isActive }) => `nav-link-desktop${isActive ? ' active' : ''}`}><Shield size={18} /> <span className="nav-label">{t('nav.team', 'Team')}</span></NavLink>
      </nav>

      <div className="account-container" ref={accountRef}>
        <button
          className="account-trigger"
          onClick={() => setIsAccountOpen(!isAccountOpen)}
          aria-expanded={isAccountOpen}
          aria-label="Account menu"
        >
          <div className="account-avatar glass-effect">AR</div>
          <span className="account-shop-name">Modern Tailors</span>
          <ChevronUp size={14} style={{ transform: isAccountOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} className="account-chevron" />
        </button>

        {isAccountOpen && (
          <div className="account-popover">
            <div className="popover-header">
              <span className="popover-shop-primary">Modern Tailors</span>
              <span className="popover-user-secondary">{user ? `${user.first_name} ${user.last_name}`.trim() : ''}</span>
            </div>
            <div className="popover-actions">
              <button className="popover-action"><Settings2 size={14} /> Settings</button>
              <button className="popover-action" onClick={() => { void signOut().catch(() => undefined).finally(() => navigate('/login', { replace: true })) }}><LogOut size={14} /> Sign out</button>
            </div>
          </div>
        )}
      </div>
    </SidebarContainer>
  )
}

function BackOfficeSidebar({ isPinned, setIsPinned }: { isPinned: boolean, setIsPinned: (v: boolean) => void }) {
  const { t } = useTranslation()
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [isAccountOpen, setIsAccountOpen] = useState(false)
  const accountRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (accountRef.current && !accountRef.current.contains(event.target as Node)) {
        setIsAccountOpen(false)
      }
    }
    if (isAccountOpen) document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isAccountOpen])

  return <SidebarContainer isPinned={isPinned} setIsPinned={setIsPinned} isAccountPopoverOpen={isAccountOpen}>
    <nav style={{ flex: 1 }} aria-label={t('backoffice.navigation')}>
      <NavLink to="/backoffice" end className={({ isActive }) => `nav-link-desktop${isActive ? ' active' : ''}`}><LayoutDashboard size={18} /><span className="nav-label">{t('backoffice.dashboard')}</span></NavLink>
      <NavLink to="/backoffice/shops" className={({ isActive }) => `nav-link-desktop${isActive ? ' active' : ''}`}><Store size={18} /><span className="nav-label">{t('backoffice.shops')}</span></NavLink>
      <NavLink to="/backoffice/measurements" className={({ isActive }) => `nav-link-desktop${isActive ? ' active' : ''}`}><Ruler size={18} /><span className="nav-label">{t('measurements.title')}</span></NavLink>
      <NavLink to="/backoffice/designs" className={({ isActive }) => `nav-link-desktop${isActive ? ' active' : ''}`}><Wand2 size={18} /><span className="nav-label">{t('backoffice.designs', 'Global Designs')}</span></NavLink>
      <NavLink to="/backoffice/catalog" className={({ isActive }) => `nav-link-desktop${isActive ? ' active' : ''}`}><Shirt size={18} /><span className="nav-label">{t('backoffice.catalog', 'Global Catalog')}</span></NavLink>
    </nav>
    <div className="account-container" ref={accountRef}>
      <button
        className="account-trigger"
        onClick={() => setIsAccountOpen(!isAccountOpen)}
        aria-expanded={isAccountOpen}
        aria-label="Account menu"
      >
        <div className="account-avatar glass-effect">{user?.first_name?.slice(0, 1).toUpperCase() || 'M'}</div>
        <span className="account-shop-name">{user ? `${user.first_name} ${user.last_name}`.trim() : ''}</span>
        <ChevronUp size={14} style={{ transform: isAccountOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} className="account-chevron" />
      </button>

      {isAccountOpen && (
        <div className="account-popover">
          <div className="popover-header">
            <span className="popover-shop-primary">{user ? `${user.first_name} ${user.last_name}`.trim() : ''}</span>
            <span className="popover-user-secondary">{t('backoffice.mainSupplier')}</span>
          </div>
          <div className="popover-actions">
            <button className="popover-action" onClick={() => { void signOut().catch(() => undefined).finally(() => navigate('/login', { replace: true })) }}><LogOut size={14} /> {t('backoffice.signOut')}</button>
          </div>
        </div>
      )}
    </div>
  </SidebarContainer>
}

function BackOfficeBottomNavigation() {
  const { t } = useTranslation()
  const { signOut } = useAuth()
  const navigate = useNavigate()
  return <nav className="bottom-nav bo-bottom-nav" aria-label={t('backoffice.navigation')}>
    <NavLink to="/backoffice" end className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}><LayoutDashboard size={20} />{t('backoffice.dashboard')}</NavLink>
    <NavLink to="/backoffice/shops" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}><Store size={20} />{t('backoffice.shops')}</NavLink>
    <NavLink to="/backoffice/measurements" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}><Ruler size={20} />{t('measurements.title')}</NavLink>
    <button type="button" className="nav-item" onClick={() => { void signOut().catch(() => undefined).finally(() => navigate('/login', { replace: true })) }}><LogOut size={20} />{t('backoffice.signOut')}</button>
  </nav>
}

function TopHeader({ 
  theme, setTheme, 
  palette, setPalette,
  isSidebarPinned, setIsSidebarPinned 
}: { 
  theme: Theme, setTheme: (v: Theme) => void, 
  palette: Palette, setPalette: (v: Palette) => void,
  isSidebarPinned?: boolean,
  setIsSidebarPinned?: (v: boolean) => void
}) {
  const location = useLocation()
  const isBackOffice = location.pathname.startsWith('/backoffice')

  const getPageContext = () => {
    if (isBackOffice) return { main: location.pathname === '/backoffice' ? 'Back Office' : location.pathname === '/backoffice/measurements' ? 'Measurements' : location.pathname.endsWith('/new') ? 'Create Shop' : 'Shops' }
    if (location.pathname === '/work') return { main: 'Work' }
    if (location.pathname === '/') return { main: 'Dashboard' }
    if (location.pathname.startsWith('/orders')) return { main: 'Orders' }
    if (location.pathname.startsWith('/clients')) return { main: 'Clients' }
    if (location.pathname.startsWith('/users')) return { main: 'Team' }
    if (location.pathname.startsWith('/billing')) return { main: 'Billing' }
    return { main: 'Dashboard' }
  }

  const ctx = getPageContext()

  return (
    <header className="topbar">
      <div style={{ display: 'flex', alignItems: 'center' }}>
        {setIsSidebarPinned && (
          <button 
            className={`top-header-toggle-btn ${!isSidebarPinned ? 'visible' : ''}`}
            onClick={() => setIsSidebarPinned(!isSidebarPinned)}
            aria-label="Expand sidebar"
            title="Expand sidebar"
          >
            <PanelLeftOpen size={18} />
          </button>
        )}
        <Link to={isBackOffice ? '/backoffice' : '/'} style={{ display: 'flex', textDecoration: 'none' }}>
          <BrandLogo layout="header" />
        </Link>
        <div className="page-context">
          <span className="page-context-main">{ctx.main}</span>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {isBackOffice ? <div className="bo-top-controls"><LanguageMenu /><ThemeMenu theme={theme} onChange={setTheme} /><PaletteMenu palette={palette} onChange={setPalette} /></div> : <>
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
        <button className="icon-button glass-effect" aria-label="Notifications" disabled style={{ position: 'relative' }}>
          <Bell size={18} />
          <span style={{ position: 'absolute', top: '6px', right: '6px', width: '6px', height: '6px', borderRadius: '50%', background: 'var(--color-danger)' }} />
        </button>
        </>}
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
      <NavLink to="/clients" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}><UsersRound size={20} />{t('nav.clients')}</NavLink>
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
          <Link to="/users" onClick={onClose} style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-primary)' }}><Users size={24} /><span style={{ fontSize: '12px', color: 'var(--color-text)', fontWeight: 500 }}>{t('more.members')}</span></Link>
          <Link to="/designs" onClick={onClose} style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-primary)' }}><Wand2 size={24} /><span style={{ fontSize: '12px', color: 'var(--color-text)', fontWeight: 500 }}>{t('nav.designs', 'Designs')}</span></Link>
          <Link to="/catalog" onClick={onClose} style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-primary)' }}><Shirt size={24} /><span style={{ fontSize: '12px', color: 'var(--color-text)', fontWeight: 500 }}>{t('nav.catalog', 'Catalog')}</span></Link>
          <Link to="/measurements" onClick={onClose} style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-primary)' }}><Ruler size={24} /><span style={{ fontSize: '12px', color: 'var(--color-text)', fontWeight: 500 }}>{t('measurements.title')}</span></Link>
          <Link to="/materials" onClick={onClose} style={{ textDecoration: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px', border: '1px solid var(--color-border)', borderRadius: '12px', color: 'var(--color-primary)' }}><PackageOpen size={24} /><span style={{ fontSize: '12px', color: 'var(--color-text)', fontWeight: 500 }}>Materials & Inventory</span></Link>
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
  const { ready, user, passwordChangeRequired } = useAuth()
  const [theme, setTheme] = useTheme()
  const [palette, setPalette] = usePalette()
  const location = useLocation()
  const [isMoreOpen, setIsMoreOpen] = useState(false)
  const [isSidebarPinned, setIsSidebarPinned] = useState(false)
  const isLogin = location.pathname === '/login'
  const isPasswordChange = location.pathname === '/password-change'

  useEffect(() => { setIsMoreOpen(false) }, [location.pathname])

  if (!ready) return <main className="login-page" aria-busy="true"><p>Loading your session…</p></main>
  if (isLogin) return user && !passwordChangeRequired ? <Navigate to={user.is_main_supplier_admin ? '/backoffice' : '/'} replace /> : <LoginPage />
  if (isPasswordChange) return passwordChangeRequired ? <PasswordChangePage /> : user ? <Navigate to={user.is_main_supplier_admin ? '/backoffice' : '/'} replace /> : <Navigate to="/login" replace />
  if (!user || passwordChangeRequired) return <Navigate to={passwordChangeRequired ? '/password-change' : '/login'} replace />

  if (user.is_main_supplier_admin) return <div className="app-shell">
    <BackOfficeSidebar isPinned={isSidebarPinned} setIsPinned={setIsSidebarPinned} />
    <main className="main-area">
      <TopHeader 
        theme={theme} setTheme={setTheme} 
        palette={palette} setPalette={setPalette} 
        isSidebarPinned={isSidebarPinned}
        setIsSidebarPinned={setIsSidebarPinned}
      />
      <Routes>
        <Route path="/backoffice" element={<BackOfficeDashboard />} />
        <Route path="/backoffice/shops" element={<ShopListPage />} />
        <Route path="/backoffice/shops/new" element={<CreateShopPage />} />
        <Route path="/backoffice/shops/:shopId" element={<ShopDetailPage />} />
        <Route path="/backoffice/measurements" element={<ClientMeasurementsPage />} />
        <Route path="/backoffice/catalog" element={<GlobalCatalogPage />} />
        <Route path="/backoffice/designs" element={<GlobalDesignTemplatesPage />} />
        <Route path="/backoffice/designs/:designId" element={<GlobalTemplateEditor />} />
        <Route path="*" element={<Navigate to="/backoffice" replace />} />
      </Routes>
    </main>
    <BackOfficeBottomNavigation />
  </div>

  if (location.pathname.startsWith('/backoffice')) return <Navigate to="/" replace />

  return <div className="app-shell">
    <DesktopSidebar isPinned={isSidebarPinned} setIsPinned={setIsSidebarPinned} />
    <main className="main-area">
      <TopHeader 
        theme={theme} setTheme={setTheme} 
        palette={palette} setPalette={setPalette} 
        isSidebarPinned={isSidebarPinned}
        setIsSidebarPinned={setIsSidebarPinned}
      />
      <Routes>
        <Route path="/work" element={<WorkPreviewPage />} />
        <Route path="/clients" element={<ClientsPage />} />
        <Route path="/clients/:clientId" element={<ClientDetailPage />} />
        <Route path="/clients/:clientId/measurements" element={<ClientMeasurementsPage />} />
        <Route path="/measurements" element={<ClientMeasurementsPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="/materials" element={<MaterialsInventoryPage />} />
        <Route path="/catalog" element={<CatalogPage />} />
        <Route path="/designs" element={<DesignsPage />} />
        <Route path="/designs/:designId" element={<DesignEditor />} />
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
  return <AuthProvider><Workspace /></AuthProvider>
}
