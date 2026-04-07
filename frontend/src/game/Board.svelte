<script lang='ts'>
  import type { CellCoord } from './winCells'

  interface Props {
    board: number[][]
    isMyTurn: boolean
    winningCells: CellCoord[] | null
    currentPlayerColor: number
    lastMoveCell: { row: number, col: number } | null
    onMove: (column: number) => void
  }

  const { board, isMyTurn, winningCells, currentPlayerColor, lastMoveCell, onMove }: Props = $props()

  let hoverColumn: number | null = $state(null)

  const ROWS = 6
  const CELL_SIZE = 64
  const GAP = 4

  const winSet = $derived(() => {
    if (!winningCells)
      return null
    const s = new Set<string>()
    for (const [r, c] of winningCells) s.add(`${r},${c}`)
    return s
  })

  function landingRow(col: number): number {
    for (let r = ROWS - 1; r >= 0; r--) {
      if (board[r][col] === 0)
        return r
    }
    return -1
  }

  function isColumnFull(col: number): boolean {
    return board[0][col] !== 0
  }

  function pieceColor(value: number): string {
    if (value === 1)
      return '#EF4444'
    if (value === 2)
      return '#FACC15'
    return 'transparent'
  }

  function handleColumnClick(col: number) {
    if (isMyTurn && !isColumnFull(col)) {
      onMove(col)
    }
  }
</script>

<div
  class='board'
  role='grid'
  aria-label='Connect 4 board'
  tabindex='0'
  onmouseleave={() => { hoverColumn = null }}
>
  {#each board as row, rowIndex}
    {#each row as cell, colIndex}
      {@const isWinCell = winSet()?.has(`${rowIndex},${colIndex}`) ?? false}
      {@const isDimmed = winSet() !== null && cell !== 0 && !isWinCell}
      {@const isHoverTarget = isMyTurn && cell === 0 && hoverColumn === colIndex && landingRow(colIndex) === rowIndex}
      {@const isDropping = lastMoveCell?.row === rowIndex && lastMoveCell?.col === colIndex}
      <button
        class='cell'
        type='button'
        role='gridcell'
        aria-label='Column {colIndex + 1}'
        disabled={!isMyTurn || isColumnFull(colIndex)}
        onclick={() => handleColumnClick(colIndex)}
        onmouseenter={() => { hoverColumn = colIndex }}
      >
        <span
          class='piece'
          class:win={isWinCell}
          class:dimmed={isDimmed}
          class:dropping={isDropping}
          style:background={isHoverTarget ? pieceColor(currentPlayerColor) : pieceColor(cell)}
          style:opacity={isHoverTarget ? '0.3' : undefined}
          style:--drop-from='{-(rowIndex) * (CELL_SIZE + GAP)}px'
        ></span>
      </button>
    {/each}
  {/each}
</div>

<style>
  .board {
    display: inline-grid;
    grid-template-columns: repeat(7, 64px);
    grid-template-rows: repeat(6, 64px);
    gap: 4px;
    padding: 8px;
    background: #1a2a3a;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
  }

  /* Board face plate: covers the grid with circular holes so dropping
     pieces (z-index 1) fall behind it, while placed pieces (z-index 3)
     sit in front. Hole size matches piece diameter (56px = 28px radius),
     tiled at cell+gap period (68px), offset by board padding (8px). */
  .board::after {
    content: '';
    position: absolute;
    inset: 0;
    background: #213547;
    border-radius: 8px;
    z-index: 2;
    pointer-events: none;
    mask-image: radial-gradient(circle 28px at center, transparent 100%, black 0);
    mask-size: 68px 68px;
    mask-position: 8px 8px;
    -webkit-mask-image: radial-gradient(circle 28px at center, transparent 100%, black 0);
    -webkit-mask-size: 68px 68px;
    -webkit-mask-position: 8px 8px;
  }

  .cell {
    padding: 0;
    border: none;
    background: transparent;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .cell:disabled {
    cursor: default;
  }

  .piece {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    transition: opacity 0.3s;
    position: relative;
    z-index: 3;
  }

  .piece.win {
    box-shadow: 0 0 0 3px white;
  }

  .piece.dimmed {
    opacity: 0.3;
  }

  .piece.dropping {
    animation: drop 0.3s ease-in;
    z-index: 1;
  }

  @keyframes drop {
    from {
      transform: translateY(var(--drop-from));
    }
    to {
      transform: translateY(0);
    }
  }
</style>
