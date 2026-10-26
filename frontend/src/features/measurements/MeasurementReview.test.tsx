import { cleanup, render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import i18n from '../../i18n'
import { MeasurementReview } from './MeasurementReview'

describe('measurement final review summary', () => {
  afterEach(cleanup)
  beforeEach(async () => {
    await i18n.changeLanguage('en')
  })

  it('keeps the summary values in one compact, labeled review list', () => {
    render(<MeasurementReview
      client={{ id: 'client-1', name: 'Mina Client', phone: '', phone_normalized: '', email: '', created_at: '', updated_at: '' }}
      wearer={null}
      family={{ id: 'family-1', name: 'Long Dress', code: 'long-dress' }}
      groups={[]}
      selectedStyles={{}}
      designName="Evening design"
      designSaved={true}
      measurementSet={null}
      historyCount={0}
      fabric={null}
    />)

    expect(screen.getByRole('heading', { name: 'Garment preparation summary' })).toBeInTheDocument()
    const summary = document.querySelector('.measurement-review-summary-list')
    expect(summary).toBeInTheDocument()
    expect(within(summary as HTMLElement).getByText('Client and wearer')).toBeInTheDocument()
    expect(within(summary as HTMLElement).getByText('Mina Client')).toBeInTheDocument()
    expect(within(summary as HTMLElement).getByText('Garment')).toBeInTheDocument()
    expect(within(summary as HTMLElement).getByText('Long Dress')).toBeInTheDocument()
    expect(within(summary as HTMLElement).getByText('Evening design')).toBeInTheDocument()
  })
})
