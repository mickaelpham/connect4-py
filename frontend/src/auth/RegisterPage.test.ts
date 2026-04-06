import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'
import { server } from '../../test/server'
import { clearAuth, isAuthenticated } from './auth.svelte'
import RegisterPage from './RegisterPage.svelte'

beforeEach(() => {
  clearAuth()
})

describe('registerPage', () => {
  it('renders register form', () => {
    render(RegisterPage)
    expect(screen.getByRole('heading', { name: 'Register' })).toBeInTheDocument()
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Register' })).toBeInTheDocument()
  })

  it('shows link to login page', () => {
    render(RegisterPage)
    expect(screen.getByText('Login')).toBeInTheDocument()
  })

  it('shows validation error for short username', async () => {
    const user = userEvent.setup()
    render(RegisterPage)
    await user.type(screen.getByLabelText('Username'), 'ab')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Register' }))
    expect(screen.getByText(/at least 3/)).toBeInTheDocument()
  })

  it('shows validation error for invalid username chars', async () => {
    const user = userEvent.setup()
    render(RegisterPage)
    await user.type(screen.getByLabelText('Username'), 'bad user!')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Register' }))
    expect(screen.getByText(/letters, numbers/)).toBeInTheDocument()
  })

  it('shows validation error for short password', async () => {
    const user = userEvent.setup()
    render(RegisterPage)
    await user.type(screen.getByLabelText('Username'), 'alice')
    await user.type(screen.getByLabelText('Password'), 'short')
    await user.click(screen.getByRole('button', { name: 'Register' }))
    expect(screen.getByText(/at least 8/)).toBeInTheDocument()
  })

  it('calls register API and sets auth on success', async () => {
    server.use(
      http.post('/api/register', () => {
        return HttpResponse.json({
          access_token: 'test-token',
          token_type: 'bearer',
          username: 'newuser',
        })
      }),
    )

    const user = userEvent.setup()
    render(RegisterPage)
    await user.type(screen.getByLabelText('Username'), 'newuser')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Register' }))

    expect(isAuthenticated()).toBe(true)
  })

  it('shows server error on duplicate username', async () => {
    server.use(
      http.post('/api/register', () => {
        return HttpResponse.json(
          { detail: 'Username already taken' },
          { status: 409 },
        )
      }),
    )

    const user = userEvent.setup()
    render(RegisterPage)
    await user.type(screen.getByLabelText('Username'), 'taken')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Register' }))

    expect(await screen.findByText('Username already taken')).toBeInTheDocument()
  })
})
