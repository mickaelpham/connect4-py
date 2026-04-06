import { render, screen, waitFor } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { server } from '../../test/server'
import { clearAuth, setAuth } from '../auth/auth.svelte'
import * as router from '../router.svelte'
import GamePage from './GamePage.svelte'

function emptyBoard(): number[][] {
  return Array.from({ length: 6 }, () => Array.from({ length: 7 }, () => 0))
}

const baseGame = {
  id: 'game1',
  player1: { id: 'p1', username: 'alice' },
  player2: { id: 'p2', username: 'bob' },
  status: 'in_progress',
  winner: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  move_count: 0,
  board: emptyBoard(),
  current_player: 1,
}

const waitingGame = {
  ...baseGame,
  player2: null,
  status: 'waiting',
  current_player: null,
}

function mockGameApi(game: unknown) {
  server.use(
    http.get('/api/games/:gameId', () => {
      return HttpResponse.json(game)
    }),
  )
}

beforeEach(() => {
  clearAuth()
  setAuth('test-token', 'alice')
  vi.useFakeTimers({ shouldAdvanceTime: true })
})

afterEach(() => {
  vi.useRealTimers()
})

describe('gamePage', () => {
  it('shows loading state initially', () => {
    // Never resolve the API call
    server.use(
      http.get('/api/games/:gameId', () => {
        return new Promise(() => {})
      }),
    )
    render(GamePage, { props: { gameId: 'game1' } })
    expect(screen.getByText('Loading game...')).toBeInTheDocument()
  })

  it('shows error when game not found', async () => {
    server.use(
      http.get('/api/games/:gameId', () => {
        return HttpResponse.json({ detail: 'Game not found' }, { status: 404 })
      }),
    )
    render(GamePage, { props: { gameId: 'nonexistent' } })
    expect(await screen.findByText('Game not found')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Back to Lobby' })).toBeInTheDocument()
  })

  it('shows waiting view with share link when creator is waiting', async () => {
    mockGameApi(waitingGame)
    render(GamePage, { props: { gameId: 'game1' } })
    expect(await screen.findByText('Waiting for opponent')).toBeInTheDocument()
    expect(screen.getByDisplayValue(/\/games\/game1/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Copy' })).toBeInTheDocument()
  })

  it('shows board when game is in progress', async () => {
    mockGameApi(baseGame)
    render(GamePage, { props: { gameId: 'game1' } })
    expect(await screen.findByRole('grid', { name: 'Connect 4 board' })).toBeInTheDocument()
  })

  it('shows player names in info panel', async () => {
    mockGameApi(baseGame)
    render(GamePage, { props: { gameId: 'game1' } })
    expect(await screen.findByText('alice')).toBeInTheDocument()
    expect(screen.getByText('bob')).toBeInTheDocument()
    expect(screen.getByText('(you)')).toBeInTheDocument()
  })

  it('shows correct status label', async () => {
    mockGameApi(baseGame) // move_count=0, alice is player1 → your turn
    render(GamePage, { props: { gameId: 'game1' } })
    expect(await screen.findByText('Your turn')).toBeInTheDocument()
  })

  it('shows their turn when opponent should play', async () => {
    mockGameApi({ ...baseGame, move_count: 1, current_player: 2 })
    render(GamePage, { props: { gameId: 'game1' } })
    expect(await screen.findByText('Their turn')).toBeInTheDocument()
  })

  it('plays a move on column click', async () => {
    mockGameApi(baseGame)
    let moveRequested = false
    server.use(
      http.post('/api/games/:gameId/moves', async ({ request }) => {
        const body = await request.json() as { column: number }
        moveRequested = true
        expect(body.column).toBe(0)
        const updatedBoard = emptyBoard()
        updatedBoard[5][0] = 1
        return HttpResponse.json({
          id: 'move1',
          player: { id: 'p1', username: 'alice' },
          column: 0,
          move_number: 1,
          created_at: new Date().toISOString(),
        })
      }),
      // After move, getGame returns updated state
      http.get('/api/games/:gameId', ({ request }) => {
        const updatedBoard = emptyBoard()
        if (moveRequested) {
          updatedBoard[5][0] = 1
        }
        return HttpResponse.json({
          ...baseGame,
          board: updatedBoard,
          move_count: moveRequested ? 1 : 0,
          current_player: moveRequested ? 2 : 1,
        })
      }),
    )

    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(GamePage, { props: { gameId: 'game1' } })

    await screen.findByRole('grid', { name: 'Connect 4 board' })

    // Click the first column (first cell, top-left)
    const cells = screen.getAllByRole('gridcell')
    await user.click(cells[0]) // column 0

    expect(moveRequested).toBe(true)
  })

  it('shows error on failed move', async () => {
    mockGameApi(baseGame)
    server.use(
      http.post('/api/games/:gameId/moves', () => {
        return HttpResponse.json({ detail: 'Column is full' }, { status: 422 })
      }),
    )

    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(GamePage, { props: { gameId: 'game1' } })

    await screen.findByRole('grid', { name: 'Connect 4 board' })
    const cells = screen.getAllByRole('gridcell')
    await user.click(cells[0])

    expect(await screen.findByText('Column is full')).toBeInTheDocument()
  })

  it('highlights winning cells and dims others', async () => {
    const wonBoard = emptyBoard()
    // Player 1 wins horizontally on bottom row
    wonBoard[5][0] = 1
    wonBoard[5][1] = 1
    wonBoard[5][2] = 1
    wonBoard[5][3] = 1
    // Some other pieces
    wonBoard[4][0] = 2
    wonBoard[4][1] = 2
    wonBoard[4][2] = 2

    mockGameApi({
      ...baseGame,
      status: 'won',
      winner: { id: 'p1', username: 'alice' },
      board: wonBoard,
      current_player: null,
      move_count: 7,
    })

    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByRole('grid', { name: 'Connect 4 board' })

    // Check that win cells have the 'win' class and others have 'dimmed'
    const pieces = document.querySelectorAll('.piece')
    const winPieces = document.querySelectorAll('.piece.win')
    const dimmedPieces = document.querySelectorAll('.piece.dimmed')

    expect(winPieces.length).toBe(4)
    expect(dimmedPieces.length).toBe(3) // the 3 player-2 pieces
  })

  it('polls for updates every 2s', async () => {
    let fetchCount = 0
    server.use(
      http.get('/api/games/:gameId', () => {
        fetchCount++
        // After second fetch, opponent has played
        if (fetchCount >= 3) {
          const updatedBoard = emptyBoard()
          updatedBoard[5][0] = 1
          updatedBoard[5][1] = 2
          return HttpResponse.json({
            ...baseGame,
            board: updatedBoard,
            move_count: 2,
            current_player: 1,
          })
        }
        const board = emptyBoard()
        board[5][0] = 1
        return HttpResponse.json({
          ...baseGame,
          board,
          move_count: 1,
          current_player: 2,
        })
      }),
    )

    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByRole('grid', { name: 'Connect 4 board' })

    // Initial fetch = 1
    expect(fetchCount).toBe(1)

    // Advance 2s → poll fires
    await vi.advanceTimersByTimeAsync(2000)
    await waitFor(() => expect(fetchCount).toBe(2))

    // Advance another 2s → another poll
    await vi.advanceTimersByTimeAsync(2000)
    await waitFor(() => expect(fetchCount).toBe(3))
  })

  it('stops polling when game ends', async () => {
    let fetchCount = 0
    server.use(
      http.get('/api/games/:gameId', () => {
        fetchCount++
        return HttpResponse.json({
          ...baseGame,
          status: 'won',
          winner: { id: 'p1', username: 'alice' },
          current_player: null,
          move_count: 7,
        })
      }),
    )

    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByText('You won')

    const countAfterLoad = fetchCount

    // Advance several polling intervals
    await vi.advanceTimersByTimeAsync(6000)

    // No additional fetches should have happened
    expect(fetchCount).toBe(countAfterLoad)
  })

  it('navigates back to lobby from not-found', async () => {
    server.use(
      http.get('/api/games/:gameId', () => {
        return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
      }),
    )

    const navigateSpy = vi.spyOn(router, 'navigate').mockImplementation(() => {})
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(GamePage, { props: { gameId: 'bad' } })

    await screen.findByText('Not found')
    await user.click(screen.getByRole('button', { name: 'Back to Lobby' }))

    expect(navigateSpy).toHaveBeenCalledWith('/')
    navigateSpy.mockRestore()
  })

  it('shows board for player2 who joined a waiting game', async () => {
    // Player2 (alice) views a game where someone else created it
    mockGameApi({
      ...baseGame,
      player1: { id: 'p3', username: 'charlie' },
      player2: { id: 'p1', username: 'alice' },
    })
    render(GamePage, { props: { gameId: 'game1' } })
    // Should show board, not waiting view
    expect(await screen.findByRole('grid', { name: 'Connect 4 board' })).toBeInTheDocument()
    expect(screen.getByText('charlie')).toBeInTheDocument()
  })
})
