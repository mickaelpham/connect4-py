import { describe, expect, it } from 'vitest'
import { findWinCells } from './winCells'

function emptyBoard(): number[][] {
  return Array.from({ length: 6 }, () => Array.from({ length: 7 }).fill(0))
}

describe('findWinCells', () => {
  it('returns null for an empty board', () => {
    expect(findWinCells(emptyBoard())).toBeNull()
  })

  it('returns null when no four in a row', () => {
    const board = emptyBoard()
    board[5][0] = 1
    board[5][1] = 1
    board[5][2] = 1
    // only 3 in a row
    expect(findWinCells(board)).toBeNull()
  })

  it('finds horizontal win', () => {
    const board = emptyBoard()
    board[5][1] = 1
    board[5][2] = 1
    board[5][3] = 1
    board[5][4] = 1
    expect(findWinCells(board)).toEqual([[5, 1], [5, 2], [5, 3], [5, 4]])
  })

  it('finds vertical win', () => {
    const board = emptyBoard()
    board[2][3] = 2
    board[3][3] = 2
    board[4][3] = 2
    board[5][3] = 2
    expect(findWinCells(board)).toEqual([[2, 3], [3, 3], [4, 3], [5, 3]])
  })

  it('finds diagonal down-right win', () => {
    const board = emptyBoard()
    board[2][0] = 1
    board[3][1] = 1
    board[4][2] = 1
    board[5][3] = 1
    expect(findWinCells(board)).toEqual([[2, 0], [3, 1], [4, 2], [5, 3]])
  })

  it('finds diagonal down-left win', () => {
    const board = emptyBoard()
    board[2][6] = 2
    board[3][5] = 2
    board[4][4] = 2
    board[5][3] = 2
    expect(findWinCells(board)).toEqual([[2, 6], [3, 5], [4, 4], [5, 3]])
  })

  it('returns exactly 4 cells', () => {
    const board = emptyBoard()
    // 5 in a row — should still return the first 4 found
    board[5][0] = 1
    board[5][1] = 1
    board[5][2] = 1
    board[5][3] = 1
    board[5][4] = 1
    const result = findWinCells(board)
    expect(result).toHaveLength(4)
  })

  it('finds win in the middle of the board', () => {
    const board = emptyBoard()
    board[1][2] = 1
    board[2][2] = 1
    board[3][2] = 1
    board[4][2] = 1
    expect(findWinCells(board)).toEqual([[1, 2], [2, 2], [3, 2], [4, 2]])
  })
})
