<script lang='ts'>
  import type { GameDetailResponse } from '../shared/api'
  import type { CellCoord } from './winCells'
  import { onMount } from 'svelte'
  import { getAuth } from '../auth/auth.svelte'
  import { getDisplayStatus } from '../lobby/gameStatus'
  import { navigate } from '../router.svelte'
  import { ApiError, getGame, joinGame, playMove } from '../shared/api'
  import { createGameStream } from '../shared/gameStream'
  import Board from './Board.svelte'
  import InfoPanel from './InfoPanel.svelte'
  import WaitingView from './WaitingView.svelte'
  import { findWinCells } from './winCells'

  interface Props {
    gameId: string
  }

  const { gameId }: Props = $props()
  const auth = getAuth()

  let game: GameDetailResponse | null = $state(null)
  let loading = $state(true)
  let error: string | null = $state(null)
  let optimisticBoard: number[][] | null = $state(null)
  let pendingColumn: number | null = $state(null)
  let lastMoveCell: { row: number, col: number } | null = $state(null)

  const displayBoard = $derived(optimisticBoard ?? game?.board ?? [])
  const status = $derived(game ? getDisplayStatus(game, auth.playerName!) : null)
  const isMyTurn = $derived(status === 'your-turn' && pendingColumn === null)
  const myPlayerNumber = $derived(
    game ? (game.player1.username === auth.playerName ? 1 : 2) : 1,
  )
  const winningCells: CellCoord[] | null = $derived(
    game?.status === 'won' ? findWinCells(game.board) : null,
  )
  const isCreatorWaiting = $derived(
    game?.status === 'waiting' && game.player1.username === auth.playerName,
  )
  const shouldStream = $derived(
    game !== null && (isCreatorWaiting || game.status === 'in_progress'),
  )
  const canJoin = $derived(
    game?.status === 'waiting' && game.player1.username !== auth.playerName && game.player2 === null,
  )
  let joining = $state(false)

  onMount(() => {
    loadGame()
  })

  async function loadGame() {
    try {
      game = await getGame(gameId)
    }
    catch (e) {
      error = e instanceof ApiError ? e.detail : 'Failed to load game'
    }
    finally {
      loading = false
    }
  }

  // SSE: stream game events while game is active
  // shouldStream is a $derived boolean — the effect only re-runs on status
  // transitions (null→waiting, waiting→in_progress, in_progress→won/draw),
  // NOT on every game state update from SSE events.
  $effect(() => {
    if (!shouldStream) return

    const stream = createGameStream(
      gameId,
      (event) => {
        const prevBoard = game?.board
        game = event.data
        if (pendingColumn !== null) {
          pendingColumn = null
          optimisticBoard = null
          setTimeout(() => {
            lastMoveCell = null
          }, 300)
        }
        else if ((event.type === 'move' || event.type === 'game_over') && prevBoard) {
          const newBoard = event.data.board
          for (let r = 0; r < newBoard.length; r++) {
            for (let c = 0; c < newBoard[r].length; c++) {
              if (prevBoard[r][c] === 0 && newBoard[r][c] !== 0) {
                lastMoveCell = { row: r, col: c }
                setTimeout(() => {
                  lastMoveCell = null
                }, 300)
                return
              }
            }
          }
        }
      },
      () => {
        error = 'Connection lost. Please refresh the page.'
      },
    )

    return () => stream.close()
  })

  async function handleJoin() {
    if (!game) return
    error = null
    joining = true
    try {
      await joinGame(gameId)
      game = await getGame(gameId)
    }
    catch (e) {
      error = e instanceof ApiError ? e.detail : 'Failed to join game'
    }
    finally {
      joining = false
    }
  }

  async function handleMove(column: number) {
    if (!game || pendingColumn !== null) return

    // Compute optimistic board
    const newBoard = game.board.map(row => [...row])
    let targetRow = -1
    for (let r = newBoard.length - 1; r >= 0; r--) {
      if (newBoard[r][column] === 0) {
        targetRow = r
        break
      }
    }
    if (targetRow === -1) return

    newBoard[targetRow][column] = myPlayerNumber
    optimisticBoard = newBoard
    pendingColumn = column
    lastMoveCell = { row: targetRow, col: column }
    error = null

    try {
      await playMove(gameId, column)
      // No re-fetch — SSE event will update game state and clear optimistic board
    }
    catch (e) {
      optimisticBoard = null
      pendingColumn = null
      error = e instanceof ApiError ? e.detail : 'Failed to play move'
      setTimeout(() => {
        lastMoveCell = null
      }, 300)
    }
  }
</script>

{#if loading}
  <p>Loading game...</p>
{:else if !game}
  <div class='not-found'>
    <p class='error'>{error ?? 'Game not found'}</p>
    <button class='btn-secondary' onclick={() => navigate('/')}>Back to Lobby</button>
  </div>
{:else if isCreatorWaiting}
  <WaitingView {gameId} />
{:else if canJoin}
  <div class='join-view'>
    <h2>{game.player1.username} is waiting for an opponent</h2>
    {#if error}
      <p class='error'>{error}</p>
    {/if}
    <button class='btn-primary' onclick={handleJoin} disabled={joining}>
      {joining ? 'Joining...' : 'Join Game'}
    </button>
  </div>
{:else}
  <div class='game-layout'>
    <Board
      board={displayBoard}
      {isMyTurn}
      {winningCells}
      currentPlayerColor={myPlayerNumber}
      {lastMoveCell}
      onMove={handleMove}
    />
    <InfoPanel
      {game}
      {status}
      {error}
      username={auth.playerName!}
    />
  </div>
{/if}

<style>
  .game-layout {
    display: flex;
    gap: 2rem;
    align-items: flex-start;
    justify-content: center;
  }

  .not-found {
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: center;
  }

  .error {
    color: #dc2626;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 4px;
    padding: 0.5rem;
    font-size: 0.875rem;
  }

  .join-view {
    max-width: 480px;
    margin: 0 auto;
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: center;
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

  .btn-secondary {
    padding: 0.5rem 1rem;
    border: 1px solid #213547;
    border-radius: 4px;
    background: none;
    font-size: 0.875rem;
    cursor: pointer;
    color: #213547;
  }
</style>
