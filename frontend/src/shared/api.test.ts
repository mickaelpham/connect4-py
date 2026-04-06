import { http, HttpResponse } from 'msw'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { server } from '../../test/server'
import { clearAuth, getAuth, isAuthenticated, setAuth } from '../auth/auth.svelte'
import { ApiError, login, tryRefresh } from './api'

beforeEach(() => {
  clearAuth()
})

afterEach(() => {
  clearAuth()
})

describe('login()', () => {
  it('returns token response on success', async () => {
    server.use(
      http.post('/api/login', () => {
        return HttpResponse.json({
          access_token: 'tok123',
          token_type: 'bearer',
          username: 'alice',
        })
      }),
    )

    const res = await login('alice', 'password123')
    expect(res.access_token).toBe('tok123')
    expect(res.username).toBe('alice')
  })

  it('throws ApiError on failure', async () => {
    server.use(
      http.post('/api/login', () => {
        return HttpResponse.json(
          { detail: 'Invalid username or password' },
          { status: 401 },
        )
      }),
    )

    await expect(login('alice', 'wrong')).rejects.toThrow(ApiError)
    await expect(login('alice', 'wrong')).rejects.toThrow('Invalid username or password')
  })
})

describe('tryRefresh()', () => {
  it('sets auth on successful refresh', async () => {
    server.use(
      http.post('/api/refresh', () => {
        return HttpResponse.json({
          access_token: 'refreshed-tok',
          token_type: 'bearer',
          username: 'alice',
        })
      }),
    )

    const result = await tryRefresh()
    expect(result).toBe(true)
    expect(isAuthenticated()).toBe(true)
    expect(getAuth().token).toBe('refreshed-tok')
    expect(getAuth().playerName).toBe('alice')
  })

  it('returns false on failed refresh', async () => {
    server.use(
      http.post('/api/refresh', () => {
        return HttpResponse.json(
          { detail: 'Invalid or expired refresh token' },
          { status: 401 },
        )
      }),
    )

    const result = await tryRefresh()
    expect(result).toBe(false)
    expect(isAuthenticated()).toBe(false)
  })
})

describe('apiFetch 401 intercept', () => {
  it('retries request after successful token refresh', async () => {
    setAuth('expired-tok', 'alice')
    let callCount = 0

    server.use(
      http.get('/api/games', ({ request }) => {
        callCount++
        const authHeader = request.headers.get('Authorization')
        if (authHeader === 'Bearer expired-tok') {
          return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })
        }
        return HttpResponse.json({ games: [], next_cursor: null })
      }),
      http.post('/api/refresh', () => {
        return HttpResponse.json({
          access_token: 'fresh-tok',
          token_type: 'bearer',
          username: 'alice',
        })
      }),
    )

    const { getGames } = await import('./api')
    const result = await getGames()

    expect(callCount).toBe(2)
    expect(result.games).toEqual([])
    expect(getAuth().token).toBe('fresh-tok')
  })

  it('clears auth and throws when refresh fails', async () => {
    setAuth('expired-tok', 'alice')

    server.use(
      http.get('/api/games', () => {
        return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })
      }),
      http.post('/api/refresh', () => {
        return HttpResponse.json(
          { detail: 'Invalid or expired refresh token' },
          { status: 401 },
        )
      }),
    )

    const { getGames } = await import('./api')
    await expect(getGames()).rejects.toThrow('Session expired')
    expect(isAuthenticated()).toBe(false)
  })
})
