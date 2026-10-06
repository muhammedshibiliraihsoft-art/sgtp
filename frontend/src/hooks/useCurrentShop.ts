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
type ShopState = Omit<CurrentShop, 'shopId'> & { userId: string | null }

const CurrentShopContext = createContext<CurrentShop | null>(null)

export function CurrentShopProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const userId = user?.id ?? null
  const isMainSupplier = Boolean(user?.is_main_supplier_admin)
  const [state, setState] = useState<ShopState>({
    userId: null,
    shop: null,
    role: null,
    workFunctions: [],
    isLoading: true,
  })

  useEffect(() => {
    if (!userId || isMainSupplier) return

    let isMounted = true
    shopsService.list()
      .then(async page => {
        if (!isMounted) return
        if (page.results.length > 0) {
          const current = page.results[0]
          const context = await shopsService.context(current.id)
          if (!isMounted) return
          setState({ userId, shop: current, role: context.role, workFunctions: context.work_functions ?? [], isLoading: false })
        } else {
          setState({ userId, shop: null, role: null, workFunctions: [], isLoading: false })
        }
      })
      .catch(() => {
        if (isMounted) setState({ userId, shop: null, role: null, workFunctions: [], isLoading: false })
      })

    return () => { isMounted = false }
  }, [userId, isMainSupplier])

  const currentShop = !userId || isMainSupplier
    ? { shop: null, shopId: undefined, role: null, workFunctions: [], isLoading: false }
    : state.userId !== userId
      ? { shop: null, shopId: undefined, role: null, workFunctions: [], isLoading: true }
      : { ...state, shopId: state.shop?.id }

  return createElement(CurrentShopContext.Provider, {
    value: currentShop,
  }, children)
}

export function useCurrentShop() {
  const context = useContext(CurrentShopContext)
  if (!context) throw new Error('useCurrentShop must be used inside CurrentShopProvider')
  return context
}
