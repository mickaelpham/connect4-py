<script lang='ts'>
  interface Props {
    gameId: string
  }
  const { gameId }: Props = $props()
</script>

<h2>Game</h2>
<p>Game {gameId} — board coming in Phase 10.</p>
