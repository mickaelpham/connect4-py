import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { server } from '../../test/server'
import { clearAuth, setAuth } from '../auth/auth.svelte'
import * as router from '../router.svelte'
import LobbyPage from './LobbyPage.svelte'

function mockGamesApi(myGames: unknown[] = [], openGames: unknown[] = []) {
  server.use(
    http.get('/api/games', () => {
      return HttpResponse.json({ games: myGames, next_cursor: null })
    }),
    http.get('/api/games/open', () => {
      return HttpResponse.json(openGames)
    }),
  )
}

const myGame = {
  id: 'game1',
  player1: { id: 'p1', username: 'alice' },
  player2: { id: 'p2', username: 'bob' },
  status: 'in_progress',
  winner: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  move_count: 0,
}

const waitingGame = {
  id: 'game2',
  player1: { id: 'p1', username: 'alice' },
  player2: null,
  status: 'waiting',
  winner: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  move_count: 0,
}

const openGame = {
  id: 'game3',
  player1: { id: 'p3', username: 'charlie' },
  player2: null,
  status: 'waiting',
  winner: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  move_count: 0,
}

beforeEach(() => {
  clearAuth()
  setAuth('test-token', 'alice')
})

describe('lobbyPage', () => {
  it('renders heading and new game button', async () => {
    mockGamesApi()
    render(LobbyPage)
    expect(screen.getByRole('heading', { name: 'Lobby' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'New Game' })).toBeInTheDocument()
  })

  it('shows loading state initially', () => {
    mockGamesApi()
    render(LobbyPage)
    expect(screen.getByText('Loading games...')).toBeInTheDocument()
  })

  it('displays your games section', async () => {
    mockGamesApi([myGame])
    render(LobbyPage)
    expect(await screen.findByText('bob')).toBeInTheDocument()
    expect(screen.getByText('Your turn')).toBeInTheDocument()
  })

  it('displays open games with join button', async () => {
    mockGamesApi([], [openGame])
    render(LobbyPage)
    expect(await screen.findByText('charlie')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Join' })).toBeInTheDocument()
  })

  it('shows empty state when no games', async () => {
    mockGamesApi()
    render(LobbyPage)
    expect(await screen.findByText('No games yet. Create one or join an open game!')).toBeInTheDocument()
    expect(screen.getByText('No open games right now.')).toBeInTheDocument()
  })

  it('shows waiting status for own waiting game', async () => {
    mockGamesApi([waitingGame])
    render(LobbyPage)
    expect(await screen.findByText('Waiting for opponent')).toBeInTheDocument()
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('creates a new game and navigates', async () => {
    mockGamesApi()
    server.use(
      http.post('/api/games', () => {
        return HttpResponse.json({
          id: 'new-game-id',
          player1: { id: 'p1', username: 'alice' },
          player2: null,
          status: 'waiting',
          winner: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          move_count: 0,
        })
      }),
    )

    const navigateSpy = vi.spyOn(router, 'navigate').mockImplementation(() => {})
    const user = userEvent.setup()
    render(LobbyPage)

    await screen.findByText('No games yet. Create one or join an open game!')
    await user.click(screen.getByRole('button', { name: 'New Game' }))

    expect(navigateSpy).toHaveBeenCalledWith('/games/new-game-id')
    navigateSpy.mockRestore()
  })

  it('joins an open game and navigates', async () => {
    mockGamesApi([], [openGame])
    server.use(
      http.post('/api/games/game3/join', () => {
        return HttpResponse.json({
          ...openGame,
          player2: { id: 'p1', username: 'alice' },
          status: 'in_progress',
        })
      }),
    )

    const navigateSpy = vi.spyOn(router, 'navigate').mockImplementation(() => {})
    const user = userEvent.setup()
    render(LobbyPage)

    await screen.findByText('charlie')
    await user.click(screen.getByRole('button', { name: 'Join' }))

    expect(navigateSpy).toHaveBeenCalledWith('/games/game3')
    navigateSpy.mockRestore()
  })

  it('shows error when loading fails', async () => {
    server.use(
      http.get('/api/games', () => {
        return HttpResponse.json({ detail: 'Server error' }, { status: 500 })
      }),
      http.get('/api/games/open', () => {
        return HttpResponse.json([], { status: 200 })
      }),
    )

    render(LobbyPage)
    expect(await screen.findByText('Server error')).toBeInTheDocument()
  })

  it('shows correct status labels for different game states', async () => {
    const wonGame = {
      ...myGame,
      id: 'game-won',
      status: 'won',
      winner: { id: 'p1', username: 'alice' },
      move_count: 7,
    }
    const lostGame = {
      ...myGame,
      id: 'game-lost',
      status: 'won',
      winner: { id: 'p2', username: 'bob' },
      move_count: 8,
    }
    mockGamesApi([wonGame, lostGame])
    render(LobbyPage)
    expect(await screen.findByText('You won')).toBeInTheDocument()
    expect(screen.getByText('You lost')).toBeInTheDocument()
  })

  it('disables new game button while creating', async () => {
    mockGamesApi()
    let resolveCreate: (value: Response) => void
    server.use(
      http.post('/api/games', async () => {
        return new Promise((resolve) => {
          resolveCreate = resolve
        })
      }),
    )

    const navigateSpy = vi.spyOn(router, 'navigate').mockImplementation(() => {})
    const user = userEvent.setup()
    render(LobbyPage)

    await screen.findByText('No games yet. Create one or join an open game!')
    await user.click(screen.getByRole('button', { name: 'New Game' }))

    expect(screen.getByRole('button', { name: 'Creating...' })).toBeDisabled()

    resolveCreate!(HttpResponse.json({
      id: 'x',
      player1: { id: 'p1', username: 'alice' },
      player2: null,
      status: 'waiting',
      winner: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      move_count: 0,
    }))

    navigateSpy.mockRestore()
  })
})
