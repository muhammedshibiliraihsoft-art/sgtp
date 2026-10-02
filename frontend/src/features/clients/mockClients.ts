import type { Client, RelatedPerson } from './types'

export const mockClients: Client[] = [
  {
    id: 'c1',
    name: 'Ahmed Al-Rashid',
    phone: '+965 99123456',
    phone_normalized: '+96599123456',
    email: 'ahmed.r@example.com',
    created_at: '2026-09-10T10:00:00Z',
    updated_at: '2026-09-28T14:30:00Z'
  },
  {
    id: 'c2',
    name: 'Mohammed Ali',
    phone: '+965 55566777',
    phone_normalized: '+96555566777',
    email: '',
    created_at: '2026-09-12T09:15:00Z',
    updated_at: '2026-09-12T09:15:00Z'
  },
  {
    id: 'c3',
    name: 'Fathima Khalid',
    phone: '',
    phone_normalized: '',
    email: 'fathima.k@example.com',
    created_at: '2026-09-20T11:45:00Z',
    updated_at: '2026-09-29T16:20:00Z'
  },
  {
    id: 'c4',
    name: 'Omar Farooq',
    phone: '+965 66778899',
    phone_normalized: '+96566778899',
    email: 'omar.f@example.com',
    created_at: '2026-09-01T08:00:00Z',
    updated_at: '2026-09-15T12:00:00Z'
  },
  {
    id: 'c5',
    name: 'Zainab Hussein',
    phone: '+965 99887766',
    phone_normalized: '+96599887766',
    email: 'zainab.h@example.com',
    created_at: '2026-08-15T14:20:00Z',
    updated_at: '2026-08-15T14:20:00Z'
  },
  {
    id: 'c6',
    name: 'Rahul Sharma',
    phone: '+91 9876543210',
    phone_normalized: '+919876543210',
    email: 'rahul.s@example.com',
    created_at: '2026-09-22T09:30:00Z',
    updated_at: '2026-09-22T09:30:00Z'
  },
  {
    id: 'c7',
    name: 'Priya Patel',
    phone: '+91 8765432109',
    phone_normalized: '+918765432109',
    email: '',
    created_at: '2026-09-25T15:10:00Z',
    updated_at: '2026-09-26T10:00:00Z'
  }
]

export const mockRelatedPersons: RelatedPerson[] = [
  {
    id: 'rp1',
    name: 'Tariq Al-Rashid',
    phone: '+965 99123457',
    phone_normalized: '+96599123457',
    email: 'tariq.r@example.com',
    created_at: '2026-09-10T10:10:00Z',
    updated_at: '2026-09-10T10:10:00Z',
    primary_client_id: 'c1'
  },
  {
    id: 'rp2',
    name: 'Sara Ali',
    phone: '',
    phone_normalized: '',
    email: '',
    created_at: '2026-09-12T09:25:00Z',
    updated_at: '2026-09-12T09:25:00Z',
    primary_client_id: 'c2'
  }
]
