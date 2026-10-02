import { useState, useEffect } from 'react'
import { shopsService, type ShopSummary } from '../services/shops'
import { useAuth } from '../services/useAuth'

export function useCurrentShop() {
  const { user } = useAuth()
  const [shop, setShop] = useState<ShopSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!user || user.is_main_supplier_admin) {
      setIsLoading(false)
      return
    }

    let isMounted = true
    shopsService.list()
      .then(page => {
        if (!isMounted) return
        if (page.results.length > 0) {
          setShop(page.results[0])
        }
        setIsLoading(false)
      })
      .catch(() => {
        if (isMounted) setIsLoading(false)
      })

    return () => { isMounted = false }
  }, [user])

  return { shop, shopId: shop?.id, isLoading }
}
