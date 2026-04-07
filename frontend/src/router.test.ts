import { beforeEach, describe, expect, it, vi } from 'vitest'
import { clearAuth, setAuth } from './auth/auth.svelte'
import { getRoute, navigate, parseRoute, refreshRoute } from './router.svelte'

function setPath(path: string) {
  window.history.replaceState(null, '', path)
}

describe('parseRoute()', () => {
  it('parses /login', () => {
    expect(parseRoute('/login')).toEqual({ page: 'login', params: {} })
  })

  it('parses /register', () => {
    expect(parseRoute('/register')).toEqual({ page: 'register', params: {} })
  })

  it('parses / as lobby', () => {
    expect(parseRoute('/')).toEqual({ page: 'lobby', params: {} })
  })

  it('parses /games/:id', () => {
    expect(parseRoute('/games/abc123')).toEqual({ page: 'game', params: { id: 'abc123' } })
  })

  it('treats unknown paths as not-found', () => {
    expect(parseRoute('/unknown')).toEqual({ page: 'not-found', params: {} })
  })
})

describe('navigate()', () => {
  beforeEach(() => {
    setAuth('tok', 'alice')
    setPath('/')
    navigate('/')
  })

  it('updates current route', () => {
    navigate('/games/xyz')
    expect(getRoute().current).toEqual({ page: 'game', params: { id: 'xyz' } })
  })

  it('pushes to browser history', () => {
    const pushSpy = vi.spyOn(window.history, 'pushState')
    navigate('/games/xyz')
    expect(pushSpy).toHaveBeenCalledWith(null, '', '/games/xyz')
    pushSpy.mockRestore()
  })
})

describe('popstate (back/forward)', () => {
  beforeEach(() => {
    setAuth('tok', 'alice')
    setPath('/')
    navigate('/')
  })

  it('updates route on popstate', () => {
    setPath('/games/g1')
    window.dispatchEvent(new PopStateEvent('popstate'))
    expect(getRoute().current).toEqual({ page: 'game', params: { id: 'g1' } })
  })
})

describe('auth redirect', () => {
  it('redirects unauthenticated user to /login from protected route', () => {
    clearAuth()
    navigate('/')
    expect(getRoute().current).toEqual({ page: 'login', params: {} })
  })

  it('redirects unauthenticated user to /login from /games/:id', () => {
    clearAuth()
    navigate('/games/abc')
    expect(getRoute().current).toEqual({ page: 'login', params: {} })
  })

  it('redirects authenticated user away from /login to lobby', () => {
    setAuth('tok', 'alice')
    navigate('/login')
    expect(getRoute().current).toEqual({ page: 'lobby', params: {} })
  })

  it('redirects authenticated user away from /register to lobby', () => {
    setAuth('tok', 'alice')
    navigate('/register')
    expect(getRoute().current).toEqual({ page: 'lobby', params: {} })
  })

  it('applies auth guard on popstate', () => {
    clearAuth()
    setPath('/games/abc')
    window.dispatchEvent(new PopStateEvent('popstate'))
    expect(getRoute().current).toEqual({ page: 'login', params: {} })
  })
})

describe('refreshRoute', () => {
  it('re-evaluates current URL with auth guard after login', () => {
    clearAuth()
    setPath('/')
    // Simulate: user lands on /, not yet authenticated
    // After tryRefresh succeeds, auth is set and refreshRoute is called
    setAuth('tok', 'alice')
    refreshRoute()
    expect(getRoute().current).toEqual({ page: 'lobby', params: {} })
  })

  it('redirects to /login if still unauthenticated after refresh attempt', () => {
    clearAuth()
    setPath('/')
    refreshRoute()
    expect(getRoute().current).toEqual({ page: 'login', params: {} })
  })
})
