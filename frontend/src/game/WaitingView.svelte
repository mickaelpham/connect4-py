<script lang='ts'>
  interface Props {
    gameId: string
  }

  const { gameId }: Props = $props()

  const gameUrl = $derived(`${window.location.origin}/games/${gameId}`)
  let copied = $state(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(gameUrl)
    copied = true
    setTimeout(() => { copied = false }, 2000)
  }
</script>

<div class='waiting-view'>
  <h2>Waiting for opponent</h2>
  <p>Share this link with a friend to start playing:</p>

  <div class='share-link'>
    <input type='text' readonly value={gameUrl} />
    <button class='btn-primary' onclick={handleCopy}>
      {copied ? 'Copied!' : 'Copy'}
    </button>
  </div>

  <p class='hint'>The game will start automatically when they join.</p>
</div>

<style>
  .waiting-view {
    max-width: 480px;
    margin: 0 auto;
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .share-link {
    display: flex;
    gap: 0.5rem;
  }

  .share-link input {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.875rem;
    color: #213547;
    background: #f9fafb;
  }

  .btn-primary {
    padding: 0.5rem 1rem;
    background: #213547;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 0.875rem;
    cursor: pointer;
    white-space: nowrap;
  }

  .hint {
    color: #6b7280;
    font-size: 0.875rem;
  }
</style>
