import logoBlue from '../assets/brand/logoblue.png'

export function BrandLogo({ className, layout = 'header' }: { className?: string, layout?: 'header' | 'login' }) {
  return (
    <div className={`brand-container ${layout} ${className || ''}`} dir="ltr">
      <img src={logoBlue} alt="BirkOS Logo" className="brand-logo-img" />
    </div>
  )
}
