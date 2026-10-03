type ProxyEnvironment = {
  STAGING_API_ORIGIN?: string
  FRONTEND_ORIGIN?: string
}

type PagesRequestContext = {
  request: Request
  env: ProxyEnvironment
}

function jsonError(status: number, detail: string) {
  return Response.json({ detail }, { status, headers: { 'Cache-Control': 'no-store' } })
}

function allowedFrontendOrigin(value: string | undefined, requestOrigin: string): value is string {
  if (!value) return false
  try {
    const configured = new URL(value)
    const isSecurePagesOrigin = configured.protocol === 'https:'
    const isLocalDevOrigin = configured.protocol === 'http:' && ['localhost', '127.0.0.1', '[::1]', '::1'].includes(configured.hostname)
    return configured.origin === value && configured.origin === requestOrigin && (isSecurePagesOrigin || isLocalDevOrigin)
  } catch {
    return false
  }
}

function configuredApiOrigin(value: string | undefined): value is string {
  if (!value) return false
  try {
    const configured = new URL(value)
    return configured.protocol === 'https:'
      && configured.origin === value
      && configured.pathname === '/'
      && !configured.search
      && !configured.hash
      && !configured.username
      && !configured.password
  } catch {
    return false
  }
}

function setCookieHeaders(headers: Headers, cookies: string[]) {
  headers.delete('set-cookie')
  for (const cookie of cookies) {
    // Upstream host-only cookies should belong to the Pages hostname in the browser.
    // Removing Domain narrows scope to that hostname; all other flags stay intact.
    headers.append('set-cookie', cookie.replace(/;\s*domain=[^;]*/i, ''))
  }
}

export async function onRequest({ request, env }: PagesRequestContext): Promise<Response> {
  const incomingUrl = new URL(request.url)
  if (!incomingUrl.pathname.startsWith('/api/')) return jsonError(404, 'Not found.')
  if (!configuredApiOrigin(env.STAGING_API_ORIGIN)) return jsonError(503, 'The staging API proxy is not configured.')
  if (!allowedFrontendOrigin(env.FRONTEND_ORIGIN, incomingUrl.origin)) return jsonError(503, 'The frontend origin is not configured.')

  const method = request.method.toUpperCase()
  if (!['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'].includes(method)) {
    return jsonError(405, 'Method not allowed.')
  }

  const origin = request.headers.get('Origin')
  if (origin && origin !== env.FRONTEND_ORIGIN) return jsonError(403, 'Request origin is not allowed.')
  if (!origin && !['GET', 'HEAD', 'OPTIONS'].includes(method)) return jsonError(403, 'Request origin is required.')

  const upstreamUrl = new URL(`${incomingUrl.pathname}${incomingUrl.search}`, env.STAGING_API_ORIGIN)
  const headers = new Headers(request.headers)
  for (const header of ['host', 'connection', 'content-length', 'transfer-encoding', 'x-forwarded-host', 'x-forwarded-proto']) {
    headers.delete(header)
  }
  // Validate browser Origin at the edge, then provide the approved API origin for
  // Django's CSRF Origin check. Cookies and X-CSRFToken remain unchanged.
  if (origin) headers.set('Origin', env.STAGING_API_ORIGIN)

  let upstream: Response
  try {
    const upstreamRequest = new Request(upstreamUrl, {
      method,
      headers,
      body: ['GET', 'HEAD'].includes(method) ? undefined : request.body,
      redirect: 'manual',
      cache: 'no-store',
      ...(request.body && !['GET', 'HEAD'].includes(method) ? { duplex: 'half' as const } : {}),
    } as RequestInit & { duplex?: 'half' })
    upstream = await fetch(upstreamRequest)
  } catch {
    return jsonError(502, 'The staging API could not be reached.')
  }

  const responseHeaders = new Headers(upstream.headers)
  responseHeaders.set('Cache-Control', 'private, no-store')
  const cookies = upstream.headers.getSetCookie()
  setCookieHeaders(responseHeaders, cookies)
  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  })
}
