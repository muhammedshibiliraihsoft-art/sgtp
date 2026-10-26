import { createContext, createElement, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import { shopsService, type ShopSummary } from '../services/shops'
import { useAuth } from '../services/useAuth'

type CurrentShop = {
  shop: ShopSummary | null
  shopId: string | undefined
  role: 'ADMIN' | 'STAFF' | 'VIEWER' | null
  workFunctions: string[]
  isLoading: boolean
}

const CurrentShopContext = createContext<CurrentShop | null>(null)

export function CurrentShopProvider({ children }: { children: ReactNode }) {
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
          const canManageBilling = context.role === 'ADMIN'
            || (context.role === 'STAFF' && context.work_functions?.includes('CASHIER'))
          setShop({ ...current, default_currency: canManageBilling ? context.billing_currency ?? null : null })
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

  return createElement(CurrentShopContext.Provider, {
    value: { shop, shopId: shop?.id, role, workFunctions, isLoading },
  }, children)
}

export function useCurrentShop() {
  const context = useContext(CurrentShopContext)
  if (!context) throw new Error('useCurrentShop must be used inside CurrentShopProvider')
  return context
}
