<script lang='ts'>
  import { onMount } from 'svelte'
  import { getAuth, isAuthenticated, markInitialized } from './auth/auth.svelte'
  import LoginPage from './auth/LoginPage.svelte'
  import RegisterPage from './auth/RegisterPage.svelte'
  import GamePage from './game/GamePage.svelte'
  import LobbyPage from './lobby/LobbyPage.svelte'
  import { getRoute, navigate, refreshRoute } from './router.svelte'
  import { logout, tryRefresh } from './shared/api'

  const route = getRoute()
  const auth = getAuth()

  onMount(async () => {
    await tryRefresh()
    markInitialized()
    refreshRoute()
  })

  function handleLogout() {
    logout()
  }

  function handleLogoClick(e: MouseEvent) {
    e.preventDefault()
    navigate('/')
  }
</script>

<nav class='navbar'>
  <a class='logo' href='/' onclick={handleLogoClick}>
    Connect 4
  </a>

  {#if isAuthenticated()}
    <div class='nav-right'>
      <span class='player-name'>{auth.playerName}</span>
      <button class='logout-btn' onclick={handleLogout}>Logout</button>
    </div>
  {/if}
</nav>

<main>
  {#if !auth.initialized}
    <p>Loading...</p>
  {:else if route.current.page === 'login'}
    <LoginPage />
  {:else if route.current.page === 'register'}
    <RegisterPage />
  {:else if route.current.page === 'lobby'}
    <LobbyPage />
  {:else if route.current.page === 'game'}
    <GamePage gameId={route.current.params.id} />
  {/if}
</main>

<style>
  .navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1.5rem;
    border-bottom: 1px solid #e0e0e0;
  }

  .logo {
    font-weight: 700;
    font-size: 1.25rem;
    color: #213547;
    text-decoration: none;
  }

  .nav-right {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .player-name {
    font-weight: 500;
  }

  .logout-btn {
    padding: 0.25rem 0.75rem;
    border: 1px solid #213547;
    border-radius: 4px;
    background: none;
    cursor: pointer;
  }

  main {
    max-width: 960px;
    margin: 2rem auto;
    padding: 0 1rem;
  }
</style>
