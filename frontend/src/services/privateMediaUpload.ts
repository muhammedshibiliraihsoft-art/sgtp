import { ApiError, apiRequest } from './apiClient'

interface UploadTicket {
  upload_url: string
  upload_token: string
  headers: Record<string, string>
  expires_in: number
}

function isLegacyFallbackEnabled() {
  return import.meta.env.VITE_ENABLE_LEGACY_PRIVATE_MEDIA_FALLBACK === 'true'
}

function putPresignedObject(url: string, file: File, headers: Record<string, string>, onProgress?: (percent: number) => void) {
  return new Promise<void>((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open('PUT', url)
    request.withCredentials = false
    Object.entries(headers).forEach(([name, value]) => request.setRequestHeader(name, value))
    request.upload.onprogress = event => {
      if (event.lengthComputable) onProgress?.(Math.round((event.loaded / event.total) * 100))
    }
    request.onload = () => {
      if (request.status >= 200 && request.status < 300) resolve()
      else reject(new ApiError('Private image upload failed. Request a new upload link and retry.', request.status, 'private_upload_failed'))
    }
    request.onerror = () => reject(new ApiError('Private image upload could not reach storage. Check the R2 bucket CORS policy for this frontend origin and retry.', 0, 'private_upload_network_error'))
    request.onabort = () => reject(new ApiError('Private image upload was cancelled.', 0, 'private_upload_cancelled'))
    request.send(file)
  })
}

async function uploadOne<T>(path: string, kind: string, targetId: string, file: File, onProgress?: (percent: number) => void): Promise<T | null> {
  let ticket: UploadTicket
  try {
    ticket = await apiRequest<UploadTicket>(path, {
      method: 'POST',
      body: { action: 'authorize', kind, target_id: targetId, content_type: file.type, byte_size: file.size },
      headers: { 'Cache-Control': 'no-store' },
    })
  } catch (error) {
    // Legacy multipart storage can write to ephemeral server disks (notably on
    // Render Free). Allow it only for an explicitly opted-in local backend.
    if (isLegacyFallbackEnabled() && error instanceof ApiError && (error.status === 404 || error.status === 503)) return null
    if (error instanceof ApiError && (error.status === 404 || error.status === 503)) {
      throw new ApiError('Private image storage is unavailable on this backend. Do not retry by uploading to legacy server storage.', error.status, 'private_storage_unavailable')
    }
    throw error
  }

  await putPresignedObject(ticket.upload_url, file, ticket.headers, onProgress)
  return apiRequest<T>(path, {
    method: 'POST',
    body: { action: 'complete', upload_token: ticket.upload_token },
    headers: { 'Cache-Control': 'no-store' },
  })
}

export async function uploadPrivateMediaBatch<T>(options: {
  path: string
  kind: string
  targetId: string
  files: File[]
  onProgress?: (fileIndex: number, percent: number) => void
  fallback: () => Promise<T>
}): Promise<T> {
  if (!options.files.length) return options.fallback()
  const first = await uploadOne<T>(options.path, options.kind, options.targetId, options.files[0], percent => options.onProgress?.(0, percent))
  if (first === null) return options.fallback()
  const results: T[] = [first]
  for (const [index, file] of options.files.slice(1).entries()) {
    const result = await uploadOne<T>(options.path, options.kind, options.targetId, file, percent => options.onProgress?.(index + 1, percent))
    if (result === null) throw new ApiError('Storage configuration changed during the upload. Retry the remaining images.', 503, 'private_storage_unavailable')
    results.push(result)
  }
  if (Array.isArray(first)) return results.flat() as T
  return first
}
