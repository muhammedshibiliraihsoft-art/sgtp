import { useEffect, useState } from 'react'
import { binaryRequest } from '../services/apiClient'

type LoadedImage = {
  source: string
  objectUrl: string | null
  error: Error | null
}

export function usePrivateImage(url: string | null | undefined) {
  const [image, setImage] = useState<LoadedImage | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    if (!url) return
    const source = url

    let cancelled = false
    let createdUrl: string | null = null
    const controller = new AbortController()

    void binaryRequest(source, { signal: controller.signal })
      .then(blob => {
        if (cancelled) return
        const mimeType = blob.type.split(';', 1)[0].trim().toLowerCase()
        if (!['image/jpeg', 'image/png', 'image/webp'].includes(mimeType) || !blob.size) {
          throw new Error('The image response was empty or was not an image.')
        }
        createdUrl = URL.createObjectURL(blob)
        setImage({ source, objectUrl: createdUrl, error: null })
      })
      .catch(err => {
        if (cancelled) return
        setImage({ source, objectUrl: null, error: err instanceof Error ? err : new Error(String(err)) })
      })

    return () => {
      cancelled = true
      controller.abort()
      if (createdUrl) URL.revokeObjectURL(createdUrl)
    }
  }, [url, retryCount])

  const matchesCurrentUrl = Boolean(url && image?.source === url)
  return {
    objectUrl: matchesCurrentUrl ? image?.objectUrl ?? null : null,
    isLoading: Boolean(url && (!matchesCurrentUrl || (!image?.objectUrl && !image?.error))),
    error: matchesCurrentUrl ? image?.error ?? null : null,
    retry: () => { setImage(null); setRetryCount(count => count + 1) },
  }
}
