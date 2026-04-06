<script lang='ts'>
  import type { GameDetailResponse } from '../shared/api'
  import type { CellCoord } from './winCells'
  import { onMount } from 'svelte'
  import { getAuth } from '../auth/auth.svelte'
  import { getDisplayStatus } from '../lobby/gameStatus'
  import { navigate } from '../router.svelte'
  import { ApiError, getGame, playMove } from '../shared/api'
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

  // Polling: refetch every 2s while game is active
  $effect(() => {
    if (!game) return
    if (game.status !== 'in_progress' && game.status !== 'waiting') return

    const interval = setInterval(async () => {
      try {
        const updated = await getGame(gameId)
        if (pendingColumn !== null && updated.move_count <= game!.move_count) {
          return // server hasn't processed our move yet
        }
        game = updated
        if (pendingColumn !== null) {
          pendingColumn = null
          optimisticBoard = null
        }
      }
      catch {
        // silently ignore polling errors
      }
    }, 2000)

    return () => clearInterval(interval)
  })

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
      const updated = await getGame(gameId)
      game = updated
    }
    catch (e) {
      error = e instanceof ApiError ? e.detail : 'Failed to play move'
    }
    finally {
      optimisticBoard = null
      pendingColumn = null
      setTimeout(() => { lastMoveCell = null }, 300)
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
