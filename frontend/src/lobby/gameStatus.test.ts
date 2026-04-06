import type { GameResponse } from '../shared/api'
import { describe, expect, it } from 'vitest'
import { getDisplayStatus, statusLabel } from './gameStatus'

function makeGame(overrides: Partial<GameResponse> = {}): GameResponse {
  return {
    id: 'game1',
    player1: { id: 'p1', username: 'alice' },
    player2: { id: 'p2', username: 'bob' },
    status: 'in_progress',
    winner: null,
    created_at: '2025-01-01T00:00:00',
    updated_at: '2025-01-01T00:00:00',
    move_count: 0,
    ...overrides,
  }
}

describe('getDisplayStatus', () => {
  it('returns waiting for waiting games', () => {
    const game = makeGame({ status: 'waiting', player2: null })
    expect(getDisplayStatus(game, 'alice')).toBe('waiting')
  })

  it('returns draw for draw games', () => {
    const game = makeGame({ status: 'draw', move_count: 42 })
    expect(getDisplayStatus(game, 'alice')).toBe('draw')
  })

  it('returns you-won when current user is winner', () => {
    const game = makeGame({
      status: 'won',
      winner: { id: 'p1', username: 'alice' },
    })
    expect(getDisplayStatus(game, 'alice')).toBe('you-won')
  })

  it('returns you-lost when current user is not winner', () => {
    const game = makeGame({
      status: 'won',
      winner: { id: 'p2', username: 'bob' },
    })
    expect(getDisplayStatus(game, 'alice')).toBe('you-lost')
  })

  it('returns your-turn for player1 when move_count is even', () => {
    const game = makeGame({ move_count: 0 })
    expect(getDisplayStatus(game, 'alice')).toBe('your-turn')
  })

  it('returns their-turn for player1 when move_count is odd', () => {
    const game = makeGame({ move_count: 1 })
    expect(getDisplayStatus(game, 'alice')).toBe('their-turn')
  })

  it('returns your-turn for player2 when move_count is odd', () => {
    const game = makeGame({ move_count: 1 })
    expect(getDisplayStatus(game, 'bob')).toBe('your-turn')
  })

  it('returns their-turn for player2 when move_count is even', () => {
    const game = makeGame({ move_count: 2 })
    expect(getDisplayStatus(game, 'bob')).toBe('their-turn')
  })
})

describe('statusLabel', () => {
  it('returns human-readable labels', () => {
    expect(statusLabel('your-turn')).toBe('Your turn')
    expect(statusLabel('their-turn')).toBe('Their turn')
    expect(statusLabel('you-won')).toBe('You won')
    expect(statusLabel('you-lost')).toBe('You lost')
    expect(statusLabel('draw')).toBe('Draw')
    expect(statusLabel('waiting')).toBe('Waiting for opponent')
  })
})
