import { render, screen, waitFor } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MockEventSource } from '../../test/mockEventSource'
import { server } from '../../test/server'
import { clearAuth, setAuth } from '../auth/auth.svelte'
import * as router from '../router.svelte'
import GamePage from './GamePage.svelte'

function emptyBoard(): number[][] {
  return Array.from({ length: 6 }, () => Array.from<number>({ length: 7 }).fill(0))
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
  moves: [],
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
  MockEventSource.install()
})

afterEach(() => {
  MockEventSource.uninstall()
  vi.useRealTimers()
})

describe('gamePage', () => {
  it('shows loading state initially', () => {
    // Never resolve the API call
    server.use(
      http.get('/api/games/:gameId', async () => {
        return new Promise(() => {})
      }),
    )
    render(GamePage, { props: { gameId: 'game1' } })
    expect(document.querySelectorAll('.skeleton').length).toBeGreaterThan(0)
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
        return HttpResponse.json({
          id: 'move1',
          player: { id: 'p1', username: 'alice' },
          column: 0,
          move_number: 1,
          created_at: new Date().toISOString(),
        })
      }),
      http.get('/api/games/:gameId', () => {
        return HttpResponse.json(baseGame)
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

  it('shows error on failed move and rolls back optimistic board', async () => {
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
    const winPieces = document.querySelectorAll('.piece.win')
    const dimmedPieces = document.querySelectorAll('.piece.dimmed')

    expect(winPieces.length).toBe(4)
    expect(dimmedPieces.length).toBe(3) // the 3 player-2 pieces
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

  it('shows join view when visiting someone else\'s waiting game', async () => {
    mockGameApi({
      ...waitingGame,
      player1: { id: 'p3', username: 'charlie' },
    })
    render(GamePage, { props: { gameId: 'game1' } })
    expect(await screen.findByText('charlie is waiting for an opponent')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Join Game' })).toBeInTheDocument()
    // Should NOT show the board or waiting view
    expect(screen.queryByRole('grid')).not.toBeInTheDocument()
    expect(screen.queryByText('Waiting for opponent')).not.toBeInTheDocument()
  })

  it('joins game and shows board after clicking join', async () => {
    const waitingForJoin = {
      ...waitingGame,
      player1: { id: 'p3', username: 'charlie' },
    }
    let joined = false
    server.use(
      http.get('/api/games/:gameId', () => {
        if (joined) {
          return HttpResponse.json({
            ...baseGame,
            player1: { id: 'p3', username: 'charlie' },
            player2: { id: 'p1', username: 'alice' },
          })
        }
        return HttpResponse.json(waitingForJoin)
      }),
      http.post('/api/games/:gameId/join', () => {
        joined = true
        return HttpResponse.json({
          ...waitingForJoin,
          player2: { id: 'p1', username: 'alice' },
          status: 'in_progress',
        })
      }),
    )

    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(GamePage, { props: { gameId: 'game1' } })

    await screen.findByText('charlie is waiting for an opponent')
    await user.click(screen.getByRole('button', { name: 'Join Game' }))

    expect(await screen.findByRole('grid', { name: 'Connect 4 board' })).toBeInTheDocument()
  })
})

describe('gamePage SSE', () => {
  it('connects SSE when game is in progress', async () => {
    mockGameApi(baseGame)
    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByRole('grid', { name: 'Connect 4 board' })

    const es = MockEventSource.latest()
    expect(es).toBeDefined()
    expect(es!.url).toContain('/api/games/game1/stream')
    expect(es!.url).toContain('token=test-token')
  })

  it('connects SSE when creator is waiting', async () => {
    mockGameApi(waitingGame)
    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByText('Waiting for opponent')

    const es = MockEventSource.latest()
    expect(es).toBeDefined()
    expect(es!.url).toContain('/api/games/game1/stream')
  })

  it('does not connect SSE for finished games', async () => {
    mockGameApi({
      ...baseGame,
      status: 'won',
      winner: { id: 'p1', username: 'alice' },
      current_player: null,
      move_count: 7,
    })
    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByText('You won')

    expect(MockEventSource.instances.length).toBe(0)
  })

  it('does not connect SSE when viewing someone else\'s waiting game', async () => {
    mockGameApi({
      ...waitingGame,
      player1: { id: 'p3', username: 'charlie' },
    })
    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByText('charlie is waiting for an opponent')

    expect(MockEventSource.instances.length).toBe(0)
  })

  it('updates game state from SSE move event', async () => {
    mockGameApi(baseGame)
    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByRole('grid', { name: 'Connect 4 board' })

    // Simulate SSE move event — opponent played in column 0
    const updatedBoard = emptyBoard()
    updatedBoard[5][0] = 1
    updatedBoard[5][1] = 2

    const es = MockEventSource.latest()!
    es._emit('move', {
      ...baseGame,
      board: updatedBoard,
      move_count: 2,
      current_player: 1,
    })

    // Board should update — check that pieces are rendered
    await waitFor(() => {
      const pieces = document.querySelectorAll('.piece')
      expect(pieces.length).toBeGreaterThanOrEqual(2)
    })
  })

  it('animates opponent piece drop on SSE move event', async () => {
    // Start with one piece already on board (alice played col 0)
    const initialBoard = emptyBoard()
    initialBoard[5][0] = 1
    mockGameApi({ ...baseGame, board: initialBoard, move_count: 1, current_player: 2 })
    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByRole('grid', { name: 'Connect 4 board' })

    // No piece should be animating yet
    expect(document.querySelector('.piece.dropping')).toBeNull()

    // Opponent (player 2) plays in column 1 via SSE
    const updatedBoard = emptyBoard()
    updatedBoard[5][0] = 1
    updatedBoard[5][1] = 2

    const es = MockEventSource.latest()!
    es._emit('move', {
      ...baseGame,
      board: updatedBoard,
      move_count: 2,
      current_player: 1,
    })

    // The new piece at row 5, col 1 should have the dropping class
    await waitFor(() => {
      const dropping = document.querySelector('.piece.dropping')
      expect(dropping).not.toBeNull()
    })

    // After 300ms the animation class should be cleared
    await vi.advanceTimersByTimeAsync(300)
    await waitFor(() => {
      expect(document.querySelector('.piece.dropping')).toBeNull()
    })
  })

  it('transitions from waiting to board on player_joined event', async () => {
    mockGameApi(waitingGame)
    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByText('Waiting for opponent')

    const es = MockEventSource.latest()!
    es._emit('player_joined', {
      ...baseGame,
      status: 'in_progress',
      player2: { id: 'p2', username: 'bob' },
    })

    expect(await screen.findByRole('grid', { name: 'Connect 4 board' })).toBeInTheDocument()
  })

  it('shows winner on game_over event', async () => {
    mockGameApi(baseGame)
    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByRole('grid', { name: 'Connect 4 board' })

    const wonBoard = emptyBoard()
    wonBoard[5][0] = 1
    wonBoard[5][1] = 1
    wonBoard[5][2] = 1
    wonBoard[5][3] = 1

    const es = MockEventSource.latest()!
    es._emit('game_over', {
      ...baseGame,
      status: 'won',
      winner: { id: 'p1', username: 'alice' },
      board: wonBoard,
      current_player: null,
      move_count: 7,
    })

    expect(await screen.findByText('You won')).toBeInTheDocument()
  })

  it('clears optimistic state when SSE confirms move', async () => {
    mockGameApi(baseGame)
    server.use(
      http.post('/api/games/:gameId/moves', () => {
        return HttpResponse.json({
          id: 'move1',
          player: { id: 'p1', username: 'alice' },
          column: 0,
          move_number: 1,
          created_at: new Date().toISOString(),
        })
      }),
    )

    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByRole('grid', { name: 'Connect 4 board' })

    // Play optimistic move
    const cells = screen.getAllByRole('gridcell')
    await user.click(cells[0])

    // SSE confirms with server state
    const confirmedBoard = emptyBoard()
    confirmedBoard[5][0] = 1

    const es = MockEventSource.latest()!
    es._emit('move', {
      ...baseGame,
      board: confirmedBoard,
      move_count: 1,
      current_player: 2,
    })

    // Status should show their turn now
    expect(await screen.findByText('Their turn')).toBeInTheDocument()
  })

  it('does not reconnect SSE when game state updates from events', async () => {
    mockGameApi(baseGame)
    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByRole('grid', { name: 'Connect 4 board' })

    const countAfterConnect = MockEventSource.instances.length

    // Fire several move events — none should cause a new EventSource
    const es = MockEventSource.latest()!
    for (let move = 1; move <= 5; move++) {
      const board = emptyBoard()
      board[5][0] = 1
      es._emit('move', {
        ...baseGame,
        board,
        move_count: move,
        current_player: move % 2 === 0 ? 1 : 2,
      })
      // Let Svelte flush effects
      await vi.advanceTimersByTimeAsync(0)
    }

    expect(MockEventSource.instances.length).toBe(countAfterConnect)
    // The original connection should still be open
    expect(es.readyState).not.toBe(2)
  })

  it('closes SSE on component unmount', async () => {
    mockGameApi(baseGame)
    const { unmount } = render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByRole('grid', { name: 'Connect 4 board' })

    const es = MockEventSource.latest()!
    expect(es.readyState).not.toBe(2)

    unmount()

    // EventSource should be closed
    expect(es.readyState).toBe(2)
  })

  it('shows error on permanent SSE connection failure', async () => {
    mockGameApi(baseGame)
    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByRole('grid', { name: 'Connect 4 board' })

    // Mock tryRefresh to fail
    server.use(
      http.post('/api/refresh', () => {
        return HttpResponse.json({ detail: 'Invalid' }, { status: 401 })
      }),
    )

    // Simulate multiple SSE errors to exhaust reconnect attempts
    for (let i = 0; i < 6; i++) {
      const es = MockEventSource.latest()!
      es._emitError()
      // Advance past reconnect delay
      await vi.advanceTimersByTimeAsync(60_000)
    }

    expect(await screen.findByText('Connection lost. Please refresh the page.')).toBeInTheDocument()
  })

  it('reconnects SSE on error', async () => {
    mockGameApi(baseGame)
    render(GamePage, { props: { gameId: 'game1' } })
    await screen.findByRole('grid', { name: 'Connect 4 board' })

    server.use(
      http.post('/api/refresh', () => {
        return HttpResponse.json({ detail: 'Invalid' }, { status: 401 })
      }),
    )

    const initialCount = MockEventSource.instances.length

    // Simulate SSE error
    MockEventSource.latest()!._emitError()

    // Advance past first reconnect delay (1s)
    await vi.advanceTimersByTimeAsync(1500)

    // A new EventSource should have been created
    expect(MockEventSource.instances.length).toBeGreaterThan(initialCount)
  })
})
