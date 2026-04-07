<script lang='ts'>
  import { navigate } from '../router.svelte'
</script>

<div class='not-found'>
  <h2>Page not found</h2>
  <p>The page you're looking for doesn't exist.</p>
  <button class='btn-secondary' onclick={() => navigate('/')}>Back to Lobby</button>
</div>

<style>
  .not-found {
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: center;
    margin-top: 4rem;
  }

  .not-found p {
    color: #6b7280;
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
