<script lang='ts'>
  import type { ValidationErrors } from './validation'
  import { navigate } from '../router.svelte'
  import { ApiError, login } from '../shared/api'
  import { setAuth } from './auth.svelte'
  import { hasErrors, validateLogin } from './validation'

  let username = $state('')
  let password = $state('')
  let errors: ValidationErrors = $state({})
  let serverError: string | null = $state(null)
  let submitting = $state(false)

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault()
    errors = validateLogin(username, password)
    if (hasErrors(errors))
      return

    serverError = null
    submitting = true
    try {
      const res = await login(username, password)
      setAuth(res.access_token, res.username)
      navigate('/')
    }
    catch (err) {
      if (err instanceof ApiError)
        serverError = err.detail
      else
        serverError = 'An unexpected error occurred'
    }
    finally {
      submitting = false
    }
  }
</script>

<div class='auth-page'>
  <h2>Login</h2>

  <form onsubmit={handleSubmit} novalidate>
    {#if serverError}
      <p class='server-error'>{serverError}</p>
    {/if}

    <label>
      <span>Username</span>
      <input
        type='text'
        bind:value={username}
        autocomplete='username'
        disabled={submitting}
      />
      {#if errors.username}
        <p class='field-error'>{errors.username}</p>
      {/if}
    </label>

    <label>
      <span>Password</span>
      <input
        type='password'
        bind:value={password}
        autocomplete='current-password'
        disabled={submitting}
      />
      {#if errors.password}
        <p class='field-error'>{errors.password}</p>
      {/if}
    </label>

    <button type='submit' disabled={submitting}>
      {submitting ? 'Logging in…' : 'Login'}
    </button>
  </form>

  <p class='switch-link'>
    Don't have an account?
    <a href='/register' onclick={(e: MouseEvent) => {
      e.preventDefault()
      navigate('/register')
    }}>Register</a>
  </p>
</div>

<style>
  .auth-page {
    max-width: 360px;
    margin: 0 auto;
  }

  h2 {
    margin-bottom: 1.5rem;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  label span {
    font-weight: 500;
    font-size: 0.875rem;
  }

  input {
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 1rem;
  }

  input:disabled {
    opacity: 0.6;
  }

  button {
    padding: 0.625rem;
    background: #213547;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
  }

  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .server-error {
    color: #dc2626;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 4px;
    padding: 0.5rem;
    font-size: 0.875rem;
  }

  .field-error {
    color: #dc2626;
    font-size: 0.8rem;
    margin: 0;
  }

  .switch-link {
    margin-top: 1rem;
    text-align: center;
    font-size: 0.875rem;
  }
</style>
