import type { Page } from '@playwright/test';

export async function playMove(page: Page, column: number): Promise<void> {
  await page.locator(`[aria-label="Column ${column}"]`).first().click();
}

/**
 * Play a sequence of moves alternating between two players.
 * Columns are 1-indexed (matching aria-labels).
 * Waits for SSE propagation after each move by checking move history entries.
 */
export async function playMoves(
  player1Page: Page,
  player2Page: Page,
  moves: number[],
): Promise<void> {
  for (let i = 0; i < moves.length; i++) {
    const currentPage = i % 2 === 0 ? player1Page : player2Page;
    const otherPage = i % 2 === 0 ? player2Page : player1Page;

    await playMove(currentPage, moves[i]);

    // Wait for the other player to see the update via SSE
    await otherPage.locator('.move-entry').nth(i).waitFor({ timeout: 5_000 });
  }
}
