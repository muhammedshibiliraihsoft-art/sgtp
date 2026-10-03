import { useState, useEffect } from 'react'
import { shopsService, type ShopSummary } from '../services/shops'
import { useAuth } from '../services/useAuth'

export function useCurrentShop() {
  const { user } = useAuth()
  const [shop, setShop] = useState<ShopSummary | null>(null)
  const [role, setRole] = useState<'ADMIN' | 'STAFF' | 'VIEWER' | null>(null)
  const [workFunctions, setWorkFunctions] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!user || user.is_main_supplier_admin) {
      setShop(null)
      setRole(null)
      setWorkFunctions([])
      setIsLoading(false)
      return
    }

    let isMounted = true
    shopsService.list()
      .then(async page => {
        if (!isMounted) return
        if (page.results.length > 0) {
          const current = page.results[0]
          const context = await shopsService.context(current.id)
          if (!isMounted) return
          setShop(current)
          setRole(context.role)
          setWorkFunctions(context.work_functions ?? [])
        }
        setIsLoading(false)
      })
      .catch(() => {
        if (isMounted) setIsLoading(false)
      })

    return () => { isMounted = false }
  }, [user])

  return { shop, shopId: shop?.id, role, workFunctions, isLoading }
}
