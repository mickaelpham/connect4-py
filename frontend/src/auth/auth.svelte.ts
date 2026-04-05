let token: string | null = $state(null)
let playerName: string | null = $state(null)

export function getAuth() {
  return {
    get token() { return token },
    get playerName() { return playerName },
  }
}

export function setAuth(newToken: string, name: string) {
  token = newToken
  playerName = name
}

export function clearAuth() {
  token = null
  playerName = null
}

export function isAuthenticated(): boolean {
  return token !== null
}
