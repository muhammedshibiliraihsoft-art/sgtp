import { describe, expect, it } from 'vitest'
import i18n from './i18n'

describe('locale foundation', () => {
  it('registers all V1 locales with English fallback', () => {
    expect(i18n.options.supportedLngs).toEqual(expect.arrayContaining(['en', 'ar-KW', 'bn', 'ur']))
    expect(i18n.options.fallbackLng).toEqual(expect.arrayContaining(['en']))
  })

  it('resolves right-to-left direction for Arabic and Urdu only', () => {
    expect(i18n.dir('ar-KW')).toBe('rtl')
    expect(i18n.dir('ur')).toBe('rtl')
    expect(i18n.dir('en')).toBe('ltr')
    expect(i18n.dir('bn')).toBe('ltr')
  })
})
