import logoLight from '../assets/images/logo-light.webp'
import logoDark from '../assets/images/logo-dark.webp'
import './BrandLogo.css'

export function BrandLogo({ className, layout = 'header' }: { className?: string, layout?: 'header' | 'login' }) {
  return (
    <div className={`brand-container ${layout} ${className || ''}`} dir="ltr">
      <img src={logoLight} alt="BirkOS Logo" className="brand-logo-img light-theme-logo" />
      <img src={logoDark} alt="BirkOS Logo" className="brand-logo-img dark-theme-logo" />
    </div>
  )
}
