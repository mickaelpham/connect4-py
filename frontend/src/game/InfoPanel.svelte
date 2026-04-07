<script lang='ts'>
  import type { GameDetailResponse } from '../shared/api'
  import type { DisplayStatus } from '../lobby/gameStatus'
  import { navigate } from '../router.svelte'
  import { statusLabel } from '../lobby/gameStatus'

  interface Props {
    game: GameDetailResponse
    status: DisplayStatus | null
    error: string | null
    username: string
  }

  const { game, status, error, username }: Props = $props()

  let moveListEl: HTMLDivElement | undefined = $state()

  $effect(() => {
    if (game.moves.length && moveListEl) {
      moveListEl.scrollTop = moveListEl.scrollHeight
    }
  })
</script>

<div class='info-panel'>
  {#if status}
    <div class='status-section'>
      <span class='status-badge {status}'>{statusLabel(status)}</span>
    </div>
  {/if}

  <div class='players'>
    <div class='player'>
      <span class='piece-dot red'></span>
      <span class='player-name'>{game.player1.username}</span>
      {#if game.player1.username === username}
        <span class='you-tag'>(you)</span>
      {/if}
    </div>
    <div class='player'>
      <span class='piece-dot yellow'></span>
      <span class='player-name'>{game.player2?.username ?? '—'}</span>
      {#if game.player2?.username === username}
        <span class='you-tag'>(you)</span>
      {/if}
    </div>
  </div>

  {#if error}
    <p class='error'>{error}</p>
  {/if}

  <div class='move-history'>
    <h4>Move History</h4>
    {#if game.moves.length === 0}
      <p class='empty-text'>No moves yet</p>
    {:else}
      <div class='move-list' bind:this={moveListEl}>
        {#each game.moves as move (move.move_number)}
          <div class='move-entry'>
            <span class='move-num'>{move.move_number}.</span>
            <span class='piece-dot {move.player.id === game.player1.id ? 'red' : 'yellow'}'></span>
            <span>{move.player.username}</span>
            <span class='move-col'>Col {move.column + 1}</span>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <button class='btn-secondary' onclick={() => navigate('/')}>Back to Lobby</button>
</div>

<style>
  .info-panel {
    width: 240px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .status-section {
    text-align: center;
  }

  .status-badge {
    font-size: 0.875rem;
    font-weight: 500;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    white-space: nowrap;
  }

  .status-badge.your-turn {
    background: #dcfce7;
    color: #166534;
  }

  .status-badge.their-turn {
    background: #f3f4f6;
    color: #4b5563;
  }

  .status-badge.you-won {
    background: #fef9c3;
    color: #854d0e;
  }

  .status-badge.you-lost {
    background: #fee2e2;
    color: #991b1b;
  }

  .status-badge.draw {
    background: #f3f4f6;
    color: #4b5563;
  }

  .status-badge.waiting {
    background: #dbeafe;
    color: #1e40af;
  }

  .players {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .player {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .piece-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .piece-dot.red {
    background: #EF4444;
  }

  .piece-dot.yellow {
    background: #FACC15;
  }

  .player-name {
    font-weight: 500;
  }

  .you-tag {
    color: #6b7280;
    font-size: 0.8rem;
  }

  .error {
    color: #dc2626;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 4px;
    padding: 0.5rem;
    font-size: 0.875rem;
  }

  .move-history {
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 0.75rem;
  }

  .move-history h4 {
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
  }

  .move-list {
    max-height: 200px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .move-entry {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.8rem;
  }

  .move-num {
    color: #6b7280;
    min-width: 1.5rem;
    text-align: right;
  }

  .move-col {
    color: #6b7280;
    margin-left: auto;
  }

  .empty-text {
    color: #9ca3af;
    font-size: 0.8rem;
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
