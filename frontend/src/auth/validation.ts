// Keep in sync with: src/connect4/api/schemas.py
export const USERNAME_MIN = 3
export const USERNAME_MAX = 20
export const USERNAME_PATTERN = /^\w+$/
export const PASSWORD_MIN = 8
export const PASSWORD_MAX = 72

export interface ValidationErrors {
  username?: string
  password?: string
}

export function validateLogin(username: string, password: string): ValidationErrors {
  const errors: ValidationErrors = {}
  if (!username)
    errors.username = 'Username is required'
  if (!password)
    errors.password = 'Password is required'
  else if (password.length > PASSWORD_MAX)
    errors.password = `Password must be at most ${PASSWORD_MAX} characters`
  return errors
}

export function validateRegister(username: string, password: string): ValidationErrors {
  const errors: ValidationErrors = {}

  if (!username)
    errors.username = 'Username is required'
  else if (username.length < USERNAME_MIN)
    errors.username = `Username must be at least ${USERNAME_MIN} characters`
  else if (username.length > USERNAME_MAX)
    errors.username = `Username must be at most ${USERNAME_MAX} characters`
  else if (!USERNAME_PATTERN.test(username))
    errors.username = 'Username can only contain letters, numbers, and underscores'

  if (!password)
    errors.password = 'Password is required'
  else if (password.length < PASSWORD_MIN)
    errors.password = `Password must be at least ${PASSWORD_MIN} characters`
  else if (password.length > PASSWORD_MAX)
    errors.password = `Password must be at most ${PASSWORD_MAX} characters`

  return errors
}

export function hasErrors(errors: ValidationErrors): boolean {
  return Object.keys(errors).length > 0
}
