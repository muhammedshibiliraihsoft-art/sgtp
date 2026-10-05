import { apiRequest, binaryRequest } from '../../services/apiClient'
import type {
  InventoryFabric,
  MeasurementComparison,
  MeasurementDefinition,
  MeasurementOwner,
  MeasurementPage,
  MeasurementProfile,
  MeasurementSet,
} from './types'

async function allPages<T>(path: string) {
  const results: T[] = []
  let next: string | null = path
  while (next) {
    const page: MeasurementPage<T> = await apiRequest<MeasurementPage<T>>(next)
    results.push(...page.results)
    if (!page.next) break
    const url: URL = new URL(page.next, window.location.origin)
    next = `${url.pathname}${url.search}`
  }
  return results
}

function profilePath(shopId: string, clientId: string, owner: MeasurementOwner) {
  const client = `/api/v1/shops/${encodeURIComponent(shopId)}/clients/${encodeURIComponent(clientId)}`
  return owner.kind === 'client'
    ? `${client}/measurement-profiles/`
    : `${client}/related-persons/${encodeURIComponent(owner.id)}/measurement-profiles/`
}

export const measurementApi = {
  definitions(shopId: string, familyId: string, variantId: string | null, locale: string): Promise<MeasurementDefinition[]> {
    const query = new URLSearchParams({ family_id: familyId, locale })
    if (variantId) query.set('variant_id', variantId)
    return allPages<MeasurementDefinition>(
      `/api/v1/shops/${encodeURIComponent(shopId)}/measurement-definitions/?${query}`,
    )
  },
  profiles(shopId: string, clientId: string, owner: MeasurementOwner): Promise<MeasurementProfile[]> {
    return allPages<MeasurementProfile>(profilePath(shopId, clientId, owner))
  },
  createProfile(shopId: string, clientId: string, owner: MeasurementOwner, familyId: string, variantId: string | null) {
    return apiRequest<MeasurementProfile>(profilePath(shopId, clientId, owner), {
      method: 'POST',
      body: { family_id: familyId, variant_id: variantId },
    })
  },
  sets(shopId: string, clientId: string, owner: MeasurementOwner, profileId: string): Promise<MeasurementSet[]> {
    return allPages<MeasurementSet>(`${profilePath(shopId, clientId, owner)}${encodeURIComponent(profileId)}/sets/`)
  },
  saveSet(shopId: string, clientId: string, owner: MeasurementOwner, profileId: string, values: Array<{ definition_id: string; value: string; unit: 'CM' | 'INCH' }>) {
    return apiRequest<MeasurementSet>(`${profilePath(shopId, clientId, owner)}${encodeURIComponent(profileId)}/sets/`, {
      method: 'POST',
      body: { values },
    })
  },
  copySet(shopId: string, clientId: string, owner: MeasurementOwner, profileId: string, setId: string) {
    return apiRequest<MeasurementSet>(`${profilePath(shopId, clientId, owner)}${encodeURIComponent(profileId)}/sets/${encodeURIComponent(setId)}/copy/`, {
      method: 'POST',
    })
  },
  compare(shopId: string, clientId: string, owner: MeasurementOwner, profileId: string, fromSetId: string, toSetId: string) {
    const query = new URLSearchParams({ from_set_id: fromSetId, to_set_id: toSetId })
    return apiRequest<MeasurementComparison>(`${profilePath(shopId, clientId, owner)}${encodeURIComponent(profileId)}/compare/?${query}`)
  },
  exportWorksheet(shopId: string, clientId: string, owner: MeasurementOwner, profileId: string, setId?: string, designId?: string) {
    const query = new URLSearchParams()
    if (setId) query.set('measurement_set_id', setId)
    if (designId) query.set('design_id', designId)
    const suffix = query.size ? `?${query}` : ''
    return binaryRequest(`${profilePath(shopId, clientId, owner)}${encodeURIComponent(profileId)}/worksheet.pdf${suffix}`)
  },
  async fabrics(shopId: string) {
    const path = `/api/v1/shops/${encodeURIComponent(shopId)}/inventory/items/?category=FABRIC`
    const results: InventoryFabric[] = []
    let next: string | null = path
    while (next) {
      const page: MeasurementPage<InventoryFabric> = await apiRequest<MeasurementPage<InventoryFabric>>(next)
      results.push(...page.results)
      if (!page.next) break
      const url: URL = new URL(page.next, window.location.origin)
      next = `${url.pathname}${url.search}`
    }
    return results
  },
}
