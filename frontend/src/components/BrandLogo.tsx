import logoBlue from '../assets/brand/logoblue.png'

export function BrandLogo({ className, layout = 'sidebar' }: { className?: string, layout?: 'sidebar' | 'header' | 'login' }) {
  return (
    <div className={`brand-container ${layout} ${className || ''}`} dir="ltr">
      <img src={logoBlue} alt="BMS Logo" className="brand-logo-img" />
      <span className="brand-text">BMS</span>
    </div>
  )
}
