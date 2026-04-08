import { test, expect } from '../fixtures.ts';

test.describe('Lobby', () => {
  test('empty lobby shows no-games messages', async ({ player1 }) => {
    await expect(player1.page.locator('text=No games yet')).toBeVisible();
    await expect(player1.page.locator('text=No open games right now')).toBeVisible();
  });

  test('create game navigates to waiting view', async ({ player1 }) => {
    await player1.page.locator('button:has-text("New Game")').click();

    await expect(player1.page).toHaveURL(/\/games\/.+/);
    await expect(player1.page.locator('.waiting-view')).toBeVisible();
    await expect(player1.page.locator('text=Waiting for opponent')).toBeVisible();
  });

  test('open game visible to other player', async ({ player1, player2 }) => {
    // Player1 creates a game
    await player1.page.locator('button:has-text("New Game")').click();
    await expect(player1.page).toHaveURL(/\/games\/.+/);

    // Player2 refreshes lobby and sees the open game
    await player2.page.reload();
    const openGame = player2.page.locator('.open-game-item').first();
    await expect(openGame).toBeVisible();
    await expect(openGame).toContainText(player1.username);
  });

  test('join game from lobby navigates to game page', async ({ player1, player2 }) => {
    // Player1 creates a game
    await player1.page.locator('button:has-text("New Game")').click();
    await expect(player1.page).toHaveURL(/\/games\/.+/);

    // Player2 refreshes and joins
    await player2.page.reload();
    const joinButton = player2.page.locator('.open-game-item').first().locator('button:has-text("Join")');
    await joinButton.click();

    await expect(player2.page).toHaveURL(/\/games\/.+/);
    // Board should be visible after joining
    await expect(player2.page.locator('[role="grid"]')).toBeVisible();
  });
});
