import type { GameDetailResponse } from './api'
import { getAuth } from '../auth/auth.svelte'
import { tryRefresh } from './api'

export interface GameEvent {
  type: 'game_state' | 'player_joined' | 'move' | 'game_over'
  data: GameDetailResponse
}

export interface GameStream {
  close: () => void
}

const EVENT_TYPES = ['game_state', 'player_joined', 'move', 'game_over'] as const
const MAX_RECONNECT_ATTEMPTS = 5
const BASE_DELAY_MS = 1000
const MAX_DELAY_MS = 30_000

export function createGameStream(
  gameId: string,
  onEvent: (event: GameEvent) => void,
  onError?: () => void,
): GameStream {
  let eventSource: EventSource | null = null
  let closed = false
  let reconnectAttempts = 0
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function connect() {
    if (closed)
      return

    const token = getAuth().token
    if (token === null)
      return

    eventSource = new EventSource(
      `/api/games/${gameId}/stream?token=${encodeURIComponent(token)}`,
    )

    for (const type of EVENT_TYPES) {
      eventSource.addEventListener(type, (e: MessageEvent) => {
        reconnectAttempts = 0
        const data: GameDetailResponse = JSON.parse(e.data as string) as GameDetailResponse
        onEvent({ type, data })
        if (type === 'game_over') {
          close()
        }
      })
    }

    eventSource.onerror = () => {
      eventSource?.close()
      eventSource = null

      if (closed)
        return

      reconnectAttempts++
      if (reconnectAttempts > MAX_RECONNECT_ATTEMPTS) {
        onError?.()
        return
      }

      const delay = Math.min(BASE_DELAY_MS * 2 ** (reconnectAttempts - 1), MAX_DELAY_MS)

      reconnectTimer = setTimeout(async () => {
        reconnectTimer = null
        if (closed)
          return
        await tryRefresh()
        connect()
      }, delay)
    }
  }

  function close() {
    closed = true
    if (reconnectTimer !== null) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    eventSource?.close()
    eventSource = null
  }

  connect()
  return { close }
}
