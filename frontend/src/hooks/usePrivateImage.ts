import { useEffect, useState } from 'react'
import { binaryRequest } from '../services/apiClient'

type LoadedImage = {
  source: string
  objectUrl: string | null
  error: Error | null
}

export function usePrivateImage(url: string | null | undefined) {
  const [image, setImage] = useState<LoadedImage | null>(null)

  useEffect(() => {
    if (!url) return

    let cancelled = false
    let createdUrl: string | null = null

    binaryRequest(url)
      .then(blob => {
        if (cancelled) return
        createdUrl = URL.createObjectURL(blob)
        setImage({ source: url, objectUrl: createdUrl, error: null })
      })
      .catch(err => {
        if (cancelled) return
        setImage({ source: url, objectUrl: null, error: err instanceof Error ? err : new Error(String(err)) })
      })

    return () => {
      cancelled = true
      if (createdUrl) URL.revokeObjectURL(createdUrl)
    }
  }, [url])

  const matchesCurrentUrl = Boolean(url && image?.source === url)
  return {
    objectUrl: matchesCurrentUrl ? image?.objectUrl ?? null : null,
    isLoading: Boolean(url && (!matchesCurrentUrl || (!image?.objectUrl && !image?.error))),
    error: matchesCurrentUrl ? image?.error ?? null : null,
  }
}
