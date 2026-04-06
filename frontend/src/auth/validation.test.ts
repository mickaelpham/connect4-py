import { describe, expect, it } from 'vitest'
import { hasErrors, validateLogin, validateRegister } from './validation'

describe('validateLogin', () => {
  it('returns no errors for valid input', () => {
    expect(hasErrors(validateLogin('alice', 'password'))).toBe(false)
  })

  it('requires username', () => {
    const errors = validateLogin('', 'password')
    expect(errors.username).toBeDefined()
  })

  it('requires password', () => {
    const errors = validateLogin('alice', '')
    expect(errors.password).toBeDefined()
  })

  it('rejects password over 72 chars', () => {
    const errors = validateLogin('alice', 'a'.repeat(73))
    expect(errors.password).toBeDefined()
  })
})

describe('validateRegister', () => {
  it('returns no errors for valid input', () => {
    expect(hasErrors(validateRegister('alice', 'password123'))).toBe(false)
  })

  it('requires username', () => {
    const errors = validateRegister('', 'password123')
    expect(errors.username).toBeDefined()
  })

  it('rejects username shorter than 3 chars', () => {
    const errors = validateRegister('ab', 'password123')
    expect(errors.username).toContain('at least 3')
  })

  it('rejects username longer than 20 chars', () => {
    const errors = validateRegister('a'.repeat(21), 'password123')
    expect(errors.username).toContain('at most 20')
  })

  it('rejects username with special chars', () => {
    const errors = validateRegister('bad user!', 'password123')
    expect(errors.username).toContain('letters, numbers')
  })

  it('allows underscores in username', () => {
    expect(hasErrors(validateRegister('good_user', 'password123'))).toBe(false)
  })

  it('requires password', () => {
    const errors = validateRegister('alice', '')
    expect(errors.password).toBeDefined()
  })

  it('rejects password shorter than 8 chars', () => {
    const errors = validateRegister('alice', 'short')
    expect(errors.password).toContain('at least 8')
  })

  it('rejects password longer than 72 chars', () => {
    const errors = validateRegister('alice', 'a'.repeat(73))
    expect(errors.password).toContain('at most 72')
  })
})
