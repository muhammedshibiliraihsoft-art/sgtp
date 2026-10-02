import { useState, useEffect } from 'react'
import { binaryRequest } from '../services/apiClient'

export function usePrivateImage(url: string | null | undefined) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!url) {
      setObjectUrl(null)
      setIsLoading(false)
      setError(null)
      return
    }

    let isMounted = true
    setIsLoading(true)
    setError(null)

    binaryRequest(url)
      .then(blob => {
        if (!isMounted) return
        const createdUrl = URL.createObjectURL(blob)
        setObjectUrl(createdUrl)
        setIsLoading(false)
      })
      .catch(err => {
        if (!isMounted) return
        setError(err instanceof Error ? err : new Error(String(err)))
        setIsLoading(false)
      })

    return () => {
      isMounted = false
      if (objectUrl) {
         // this closure has stale objectUrl if we don't handle carefully, 
         // but wait, we need to revoke the CURRENT object url when url changes
      }
    }
  }, [url])

  // Better cleanup logic
  useEffect(() => {
    return () => {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl)
      }
    }
  }, [objectUrl])

  return { objectUrl, isLoading, error }
}
