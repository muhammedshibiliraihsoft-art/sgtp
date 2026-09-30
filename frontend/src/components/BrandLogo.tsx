import type { Palette } from '../App'

const logoModules = import.meta.glob<{ default: string }>('../assets/brand/birky-*.png', { eager: true })
const THEME_LOGOS: Record<string, string> = {}
for (const path in logoModules) {
  const match = path.match(/birky-(.+)\.png$/)
  if (match) {
    THEME_LOGOS[match[1]] = logoModules[path].default || (logoModules[path] as any)
  }
}

export function BrandLogo({ palette, resolvedTheme, className }: { palette: Palette, resolvedTheme: 'light' | 'dark', className?: string }) {
  const exactKey = `${palette}-${resolvedTheme}`
  const themeKey = palette
  const originalKey = 'original'

  const logoSrc = THEME_LOGOS[exactKey] || THEME_LOGOS[themeKey] || THEME_LOGOS[originalKey]

  if (!logoSrc) {
    return (
      <span className={`brand ${className || ''}`} aria-label="SGTP home">
        <span className="brand-mark">s</span><span>SGTP<span className="brand-dot">.</span></span>
      </span>
    )
  }

  return (
    <img
      src={logoSrc}
      alt="SGTP Brand Logo"
      className={`brand-logo-img ${className || ''}`}
      style={{ display: 'block', maxWidth: '100%', height: 'auto', maxHeight: '32px' }}
      dir="ltr"
    />
  )
}
