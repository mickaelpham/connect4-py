import type { GameResponse } from '../shared/api'

export type DisplayStatus
  = | 'your-turn'
    | 'their-turn'
    | 'you-won'
    | 'you-lost'
    | 'draw'
    | 'waiting'

export function getDisplayStatus(game: GameResponse, currentUsername: string): DisplayStatus {
  if (game.status === 'waiting')
    return 'waiting'
  if (game.status === 'draw')
    return 'draw'
  if (game.status === 'won') {
    return game.winner?.username === currentUsername ? 'you-won' : 'you-lost'
  }
  // in_progress: player1 moves on even move_count, player2 on odd
  const isPlayer1 = game.player1.username === currentUsername
  const isPlayer1Turn = game.move_count % 2 === 0
  return (isPlayer1 === isPlayer1Turn) ? 'your-turn' : 'their-turn'
}

const labels: Record<DisplayStatus, string> = {
  'your-turn': 'Your turn',
  'their-turn': 'Their turn',
  'you-won': 'You won',
  'you-lost': 'You lost',
  'draw': 'Draw',
  'waiting': 'Waiting for opponent',
}

export function statusLabel(status: DisplayStatus): string {
  return labels[status]
}
