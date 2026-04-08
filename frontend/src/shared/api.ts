import { clearAuth, getAuth, setAuth } from '../auth/auth.svelte'
import { navigate } from '../router.svelte'
import { addToast } from './toastStore.svelte'

export class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(detail)
    this.name = 'ApiError'
  }
}

interface TokenResponse {
  access_token: string
  username: string
}

let refreshPromise: Promise<boolean> | null = null

async function tryRefreshOnce(): Promise<boolean> {
  try {
    const res = await fetch('/api/refresh', {
      method: 'POST',
      credentials: 'include',
    })
    if (!res.ok)
      return false
    const data: TokenResponse = await res.json() as TokenResponse
    setAuth(data.access_token, data.username)
    return true
  }
  catch {
    return false
  }
}

/**
 * Attempt to refresh the session using the httpOnly cookie.
 * Deduplicates concurrent calls — only one refresh request is in flight at a time.
 */
export async function tryRefresh(): Promise<boolean> {
  if (refreshPromise !== null)
    return refreshPromise
  refreshPromise = tryRefreshOnce()
  try {
    return await refreshPromise
  }
  finally {
    refreshPromise = null
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  const token = getAuth().token
  if (token !== null)
    headers.set('Authorization', `Bearer ${token}`)
  if (!headers.has('Content-Type'))
    headers.set('Content-Type', 'application/json')

  let res = await fetch(path, { ...init, headers, credentials: 'include' })

  if (res.status === 401 && token !== null) {
    const refreshed = await tryRefresh()
    if (refreshed) {
      const newToken = getAuth().token
      if (newToken !== null)
        headers.set('Authorization', `Bearer ${newToken}`)
      res = await fetch(path, { ...init, headers, credentials: 'include' })
    }
    else {
      clearAuth()
      navigate('/login')
      throw new ApiError(401, 'Session expired')
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as { detail?: string }
    const detail = body.detail ?? 'Request failed'
    addToast(detail)
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

// --- Auth endpoints ---

export async function login(username: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/api/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export async function register(username: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/api/register', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export async function logout(): Promise<void> {
  try {
    await fetch('/api/logout', { method: 'POST', credentials: 'include' })
  }
  catch {
    // Best-effort — clear local state regardless
  }
  clearAuth()
  navigate('/login')
}

// --- Game endpoints (stubs for phases 9-10) ---

export interface PlayerInfo {
  id: string
  username: string
}

export interface GameResponse {
  id: string
  player1: PlayerInfo
  player2: PlayerInfo | null
  status: string
  winner: PlayerInfo | null
  created_at: string
  updated_at: string
  move_count: number
}

export interface GameDetailResponse extends GameResponse {
  board: number[][]
  current_player: number | null
  moves: MoveResponse[]
}

export interface MoveResponse {
  id: string
  player: PlayerInfo
  column: number
  move_number: number
  created_at: string
}

export interface PaginatedGamesResponse {
  games: GameResponse[]
  next_cursor: string | null
}

export async function createGame(): Promise<GameResponse> {
  return apiFetch<GameResponse>('/api/games', { method: 'POST' })
}

export async function joinGame(gameId: string): Promise<GameResponse> {
  return apiFetch<GameResponse>(`/api/games/${gameId}/join`, { method: 'POST' })
}

export async function getGame(gameId: string): Promise<GameDetailResponse> {
  return apiFetch<GameDetailResponse>(`/api/games/${gameId}`, {})
}

export async function getGames(cursor?: string): Promise<PaginatedGamesResponse> {
  const params = cursor !== undefined ? `?cursor=${encodeURIComponent(cursor)}` : ''
  return apiFetch<PaginatedGamesResponse>(`/api/games${params}`, {})
}

export async function getOpenGames(): Promise<GameResponse[]> {
  return apiFetch<GameResponse[]>('/api/games/open', {})
}

export async function getMoves(gameId: string): Promise<MoveResponse[]> {
  return apiFetch<MoveResponse[]>(`/api/games/${gameId}/moves`, {})
}

export async function playMove(gameId: string, column: number): Promise<MoveResponse> {
  return apiFetch<MoveResponse>(`/api/games/${gameId}/moves`, {
    method: 'POST',
    body: JSON.stringify({ column }),
  })
}
