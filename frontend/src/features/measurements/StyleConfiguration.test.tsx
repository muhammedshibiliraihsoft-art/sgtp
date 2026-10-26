import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import i18n from '../../i18n'
import type { OptionGroup, StyleOption } from '../catalog/types'
import { StyleConfiguration } from './StyleConfiguration'

vi.mock('./PrivateReferenceImage', () => ({
  PrivateReferenceGallery: ({ images, alt }: { images: Array<{ content_url: string; alt_text?: string }>; alt: string }) => (
    <div aria-label={alt}>{images.map(image => <img key={image.content_url} src={image.content_url} alt={image.alt_text || alt} />)}</div>
  ),
}))

const group: OptionGroup = { id: 'cuff', name: 'Cuff', code: 'cuff', families: ['shirt'] }

beforeEach(async () => { await i18n.changeLanguage('en') })
afterEach(cleanup)

function makeOptions(count: number): StyleOption[] {
  return Array.from({ length: count }, (_, index) => ({
    id: `option-${index + 1}`,
    option_group: group.id,
    tenant: null,
    code: `cuff-${index + 1}`,
    name: `Cuff ${index + 1}`,
    is_active: true,
    is_global: index % 2 === 0,
    reference_images: [{
      id: `image-${index + 1}`,
      mime_type: 'image/jpeg',
      byte_size: 1024,
      width: 320,
      height: 240,
      sort_order: 0,
      alt_text: `Saved cuff ${index + 1}`,
      content_url: `/api/v1/catalog/style-options/option-${index + 1}/images/image-${index + 1}/content/`,
    }],
  }))
}

describe('Measurement style option mobile grid content', () => {
  it.each([8, 9])('renders all %i catalog options without changing their order or source images', count => {
    const options = makeOptions(count)
    const onSelectOption = vi.fn()
    const { container } = render(<StyleConfiguration
      groups={[group]}
      selected={{}}
      activeGroupId={group.id}
      optionsByGroup={{ [group.id]: options }}
      loadingGroupId={null}
      groupErrorId={null}
      onOpenGroup={vi.fn()}
      onSelectOption={onSelectOption}
      onRetryGroup={vi.fn()}
      canWrite
    />)

    const choices = container.querySelectorAll('.measurement-option-select')
    expect(choices).toHaveLength(count)
    expect(screen.getAllByRole('img')).toHaveLength(count)
    expect(screen.getByRole('img', { name: 'Saved cuff 1' })).toHaveAttribute('src', options[0].reference_images[0].content_url)
    expect(screen.getAllByText('Global').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Shop').length).toBeGreaterThan(0)

    fireEvent.click(choices[0])
    fireEvent.click(choices[1])
    expect(onSelectOption).toHaveBeenNthCalledWith(1, group.id, options[0])
    expect(onSelectOption).toHaveBeenNthCalledWith(2, group.id, options[1])
  })
})
