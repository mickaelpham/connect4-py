<script lang='ts'>
  import type { GameResponse } from '../shared/api'
  import { onMount } from 'svelte'
  import { getAuth } from '../auth/auth.svelte'
  import { navigate } from '../router.svelte'
  import { ApiError, createGame, getGames, getOpenGames, joinGame } from '../shared/api'
  import { getDisplayStatus, statusLabel } from './gameStatus'

  const auth = getAuth()

  let myGames: GameResponse[] = $state([])
  let openGames: GameResponse[] = $state([])
  let loading = $state(true)
  let error: string | null = $state(null)
  let creatingGame = $state(false)
  let joiningGameId: string | null = $state(null)

  async function loadGames() {
    try {
      const [myResult, openResult] = await Promise.all([getGames(), getOpenGames()])
      myGames = myResult.games
      openGames = openResult
    }
    catch (e) {
      error = e instanceof ApiError ? e.detail : 'Failed to load games'
    }
    finally {
      loading = false
    }
  }

  onMount(() => {
    loadGames()
  })

  async function handleNewGame() {
    error = null
    creatingGame = true
    try {
      const game = await createGame()
      navigate(`/games/${game.id}`)
    }
    catch (e) {
      error = e instanceof ApiError ? e.detail : 'Failed to create game'
      creatingGame = false
    }
  }

  async function handleJoinGame(gameId: string) {
    error = null
    joiningGameId = gameId
    try {
      await joinGame(gameId)
      navigate(`/games/${gameId}`)
    }
    catch (e) {
      error = e instanceof ApiError ? e.detail : 'Failed to join game'
      joiningGameId = null
    }
  }

  function opponentName(game: GameResponse): string {
    if (!game.player2)
      return '—'
    if (game.player1.username === auth.playerName)
      return game.player2.username
    return game.player1.username
  }

  function relativeTime(iso: string): string {
    const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
    if (seconds < 60)
      return 'just now'
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60)
      return `${minutes}m ago`
    const hours = Math.floor(minutes / 60)
    if (hours < 24)
      return `${hours}h ago`
    const days = Math.floor(hours / 24)
    return `${days}d ago`
  }
</script>

<div class='lobby-page'>
  <div class='lobby-header'>
    <h2>Lobby</h2>
    <button class='btn-primary' onclick={handleNewGame} disabled={creatingGame}>
      {creatingGame ? 'Creating...' : 'New Game'}
    </button>
  </div>

  {#if error}
    <p class='error'>{error}</p>
  {/if}

  {#if loading}
    <p>Loading games...</p>
  {:else}
    <section>
      <h3>Your Games</h3>
      {#if myGames.length === 0}
        <p class='empty'>No games yet. Create one or join an open game!</p>
      {:else}
        <ul class='game-list' role='list'>
          {#each myGames as game (game.id)}
            <li>
              <a
                href='/games/{game.id}'
                onclick={(e: MouseEvent) => {
                  e.preventDefault()
                  navigate(`/games/${game.id}`)
                }}
              >
                <span class='opponent'>{opponentName(game)}</span>
                <span class='status {getDisplayStatus(game, auth.playerName!)}'>{statusLabel(getDisplayStatus(game, auth.playerName!))}</span>
                <span class='time'>{relativeTime(game.updated_at)}</span>
              </a>
            </li>
          {/each}
        </ul>
      {/if}
    </section>

    <section>
      <h3>Open Games</h3>
      {#if openGames.length === 0}
        <p class='empty'>No open games right now.</p>
      {:else}
        <ul class='game-list' role='list'>
          {#each openGames as game (game.id)}
            <li class='open-game-item'>
              <span class='creator'>{game.player1.username}</span>
              <span class='time'>{relativeTime(game.created_at)}</span>
              <button
                class='btn-primary btn-small'
                onclick={() => handleJoinGame(game.id)}
                disabled={joiningGameId !== null}
              >
                {joiningGameId === game.id ? 'Joining...' : 'Join'}
              </button>
            </li>
          {/each}
        </ul>
      {/if}
    </section>
  {/if}
</div>

<style>
  .lobby-page {
    max-width: 640px;
    margin: 0 auto;
  }

  .lobby-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }

  .lobby-header h2 {
    margin: 0;
  }

  .btn-primary {
    padding: 0.5rem 1rem;
    background: #213547;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 0.875rem;
    cursor: pointer;
  }

  .btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-small {
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
  }

  .error {
    color: #dc2626;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 4px;
    padding: 0.5rem;
    font-size: 0.875rem;
    margin-bottom: 1rem;
  }

  .empty {
    color: #6b7280;
    font-size: 0.875rem;
  }

  section {
    margin-bottom: 2rem;
  }

  h3 {
    margin-bottom: 0.75rem;
    font-size: 1rem;
  }

  .game-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .game-list li a {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.625rem 0.75rem;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    text-decoration: none;
    color: inherit;
  }

  .game-list li a:hover {
    background: #f9fafb;
  }

  .open-game-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.625rem 0.75rem;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
  }

  .opponent,
  .creator {
    font-weight: 500;
    flex: 1;
  }

  .status {
    font-size: 0.8rem;
    padding: 0.125rem 0.5rem;
    border-radius: 9999px;
    white-space: nowrap;
  }

  .status.your-turn {
    background: #dcfce7;
    color: #166534;
  }

  .status.their-turn {
    background: #f3f4f6;
    color: #4b5563;
  }

  .status.you-won {
    background: #fef9c3;
    color: #854d0e;
  }

  .status.you-lost {
    background: #fee2e2;
    color: #991b1b;
  }

  .status.draw {
    background: #f3f4f6;
    color: #4b5563;
  }

  .status.waiting {
    background: #dbeafe;
    color: #1e40af;
  }

  .time {
    font-size: 0.8rem;
    color: #9ca3af;
    white-space: nowrap;
  }
</style>
