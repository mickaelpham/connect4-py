import { isAuthenticated } from './auth/auth.svelte'

export interface Route {
  page: 'login' | 'register' | 'lobby' | 'game'
  params: Record<string, string>
}

const GAMES_RE = /^\/games\/([^/]+)$/

const PUBLIC_PAGES = new Set<Route['page']>(['login', 'register'])

export function parseRoute(path: string): Route {
  if (path === '/login')
    return { page: 'login', params: {} }
  if (path === '/register')
    return { page: 'register', params: {} }
  const match = GAMES_RE.exec(path)
  if (match)
    return { page: 'game', params: { id: match[1] } }
  return { page: 'lobby', params: {} }
}

function applyAuthGuard(route: Route): Route {
  if (!PUBLIC_PAGES.has(route.page) && !isAuthenticated()) {
    window.history.replaceState(null, '', '/login')
    return { page: 'login', params: {} }
  }
  if (PUBLIC_PAGES.has(route.page) && isAuthenticated()) {
    window.history.replaceState(null, '', '/')
    return { page: 'lobby', params: {} }
  }
  return route
}

// No auth guard on initial load — App.svelte calls refreshRoute() after tryRefresh()
let currentRoute: Route = $state(parseRoute(window.location.pathname))

export function navigate(path: string) {
  window.history.pushState(null, '', path)
  currentRoute = applyAuthGuard(parseRoute(path))
}

window.addEventListener('popstate', () => {
  currentRoute = applyAuthGuard(parseRoute(window.location.pathname))
})

export function refreshRoute() {
  currentRoute = applyAuthGuard(parseRoute(window.location.pathname))
}

export function getRoute() {
  return {
    get current() { return currentRoute },
  }
}
