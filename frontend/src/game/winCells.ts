export type CellCoord = [row: number, col: number]

const ROWS = 6
const COLS = 7
const WIN_LENGTH = 4

const DIRECTIONS: [number, number][] = [
  [0, 1], // horizontal (right)
  [1, 0], // vertical (down)
  [1, 1], // diagonal down-right
  [1, -1], // diagonal down-left
]

/**
 * Find the 4 winning cells on a row-major board (row 0 = top).
 * Returns null if no winner found.
 */
export function findWinCells(board: number[][]): CellCoord[] | null {
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const player = board[r][c]
      if (player === 0)
        continue

      for (const [dr, dc] of DIRECTIONS) {
        const cells: CellCoord[] = [[r, c]]
        for (let i = 1; i < WIN_LENGTH; i++) {
          const nr = r + dr * i
          const nc = c + dc * i
          if (nr < 0 || nr >= ROWS || nc < 0 || nc >= COLS || board[nr][nc] !== player)
            break
          cells.push([nr, nc])
        }
        if (cells.length === WIN_LENGTH)
          return cells
      }
    }
  }
  return null
}
