import { apiRequest } from './apiClient'

export type PendingPinReset = {
  id: string; shop: string; shop_id: string; name: string;
  login_id: string | null; phone: string; requested_at: string; status: string
}

export const pinResetService = {
  request(phone: string) {
    return apiRequest<{ detail: string }>('/api/v1/auth/pin-reset-requests/', {
      method: 'POST', body: { phone }, authenticated: false, retryUnauthorized: false,
    })
  },
  pending() {
    return apiRequest<PendingPinReset[]>('/api/v1/auth/pin-reset-requests/pending/')
  },
  approve(id: string) {
    return apiRequest<{ id: string; status: string; login_id: string | null; temporary_password: string }>(`/api/v1/auth/pin-reset-requests/${encodeURIComponent(id)}/approve/`, { method: 'POST', body: {} })
  },
  reject(id: string) {
    return apiRequest<{ id: string; status: string }>(`/api/v1/auth/pin-reset-requests/${encodeURIComponent(id)}/reject/`, { method: 'POST', body: {} })
  },
}
