import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ShopListPage } from './BackOfficePages'
import i18n from '../i18n'

const mock = vi.hoisted(() => ({ list: vi.fn() }))
vi.mock('../services/shops', () => ({ shopsService: { list: mock.list } }))

describe('Back Office Shop list', () => {
  afterEach(() => { cleanup(); vi.clearAllMocks() })

  it('sends one search request after rapid typing', async () => {
    await i18n.changeLanguage('en')
    mock.list.mockResolvedValue({ count: 0, next: null, previous: null, results: [] })
    render(<MemoryRouter><ShopListPage /></MemoryRouter>)
    await waitFor(() => expect(mock.list).toHaveBeenCalledTimes(1))
    const search = screen.getByRole('searchbox')
    fireEvent.change(search, { target: { value: 's' } })
    fireEvent.change(search, { target: { value: 'sh' } })
    fireEvent.change(search, { target: { value: 'shop' } })
    expect(mock.list).toHaveBeenCalledTimes(1)
    await waitFor(() => expect(mock.list).toHaveBeenCalledWith('shop', 1, { active: 'all', ordering: 'name' }))
    expect(mock.list).toHaveBeenCalledTimes(2)
  })
})
