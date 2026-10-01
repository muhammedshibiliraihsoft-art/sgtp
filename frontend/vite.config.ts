import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'

const APPROVED_STAGING_API_ORIGIN = 'https://birky-staging-api.onrender.com'

function validateProxyTarget(value: string | undefined) {
  if (!value) return undefined
  let url: URL
  try {
    url = new URL(value)
  } catch {
    throw new Error('AUTH_API_PROXY_TARGET must be the approved staging API origin.')
  }
  if (url.origin !== APPROVED_STAGING_API_ORIGIN || url.pathname !== '/' || url.search || url.hash || url.username || url.password) {
    throw new Error('AUTH_API_PROXY_TARGET must be the approved staging API origin.')
  }
  return url.origin
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = validateProxyTarget(env.AUTH_API_PROXY_TARGET)

  return {
    plugins: [react(), tailwindcss()],
    server: proxyTarget ? {
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          secure: true,
          configure(proxy) {
            proxy.on('proxyReq', (proxyRequest, request, response) => {
              const method = request.method?.toUpperCase() ?? 'GET'
              const origin = request.headers.origin
              const host = request.headers.host
              const localOrigin = origin && host && (() => {
                try {
                  const parsed = new URL(origin)
                  return parsed.protocol === 'http:'
                    && parsed.origin === `http://${host}`
                    && ['localhost', '127.0.0.1', '[::1]'].includes(parsed.hostname === '::1' ? '[::1]' : parsed.hostname)
                } catch {
                  return false
                }
              })()

              if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && !localOrigin) {
                response.writeHead(403, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' })
                response.end(JSON.stringify({ detail: 'Request origin is not allowed.' }))
                proxyRequest.destroy()
                return
              }

              // The local proxy checks the browser Origin above; Django then sees
              // the proxy's approved upstream origin for its CSRF Origin check.
              proxyRequest.setHeader('origin', proxyTarget)
            })
          },
        },
      },
    } : undefined,
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      clearMocks: true,
    },
  }
})
