import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'
import { server } from '../../test/server'
import { clearAuth, isAuthenticated } from './auth.svelte'
import LoginPage from './LoginPage.svelte'

beforeEach(() => {
  clearAuth()
})

describe('loginPage', () => {
  it('renders login form', () => {
    render(LoginPage)
    expect(screen.getByRole('heading', { name: 'Login' })).toBeInTheDocument()
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument()
  })

  it('shows link to register page', () => {
    render(LoginPage)
    expect(screen.getByText('Register')).toBeInTheDocument()
  })

  it('shows validation error when username is empty', async () => {
    const user = userEvent.setup()
    render(LoginPage)
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Login' }))
    expect(screen.getByText('Username is required')).toBeInTheDocument()
  })

  it('shows validation error when password is empty', async () => {
    const user = userEvent.setup()
    render(LoginPage)
    await user.type(screen.getByLabelText('Username'), 'alice')
    await user.click(screen.getByRole('button', { name: 'Login' }))
    expect(screen.getByText('Password is required')).toBeInTheDocument()
  })

  it('calls login API and sets auth on success', async () => {
    server.use(
      http.post('/api/login', () => {
        return HttpResponse.json({
          access_token: 'test-token',
          token_type: 'bearer',
          username: 'alice',
        })
      }),
    )

    const user = userEvent.setup()
    render(LoginPage)
    await user.type(screen.getByLabelText('Username'), 'alice')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Login' }))

    expect(isAuthenticated()).toBe(true)
  })

  it('shows server error on login failure', async () => {
    server.use(
      http.post('/api/login', () => {
        return HttpResponse.json(
          { detail: 'Invalid username or password' },
          { status: 401 },
        )
      }),
    )

    const user = userEvent.setup()
    render(LoginPage)
    await user.type(screen.getByLabelText('Username'), 'alice')
    await user.type(screen.getByLabelText('Password'), 'wrongpassword')
    await user.click(screen.getByRole('button', { name: 'Login' }))

    expect(await screen.findByText('Invalid username or password')).toBeInTheDocument()
  })

  it('disables button while submitting', async () => {
    let resolveLogin: (() => void) | undefined
    server.use(
      http.post('/api/login', async () => {
        return new Promise((resolve) => {
          resolveLogin = () => resolve(HttpResponse.json({
            access_token: 'tok',
            token_type: 'bearer',
            username: 'alice',
          }))
        })
      }),
    )

    const user = userEvent.setup()
    render(LoginPage)
    await user.type(screen.getByLabelText('Username'), 'alice')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Login' }))

    expect(screen.getByRole('button', { name: 'Logging in…' })).toBeDisabled()
    resolveLogin!()
  })
})
