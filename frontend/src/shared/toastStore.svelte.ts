export type ToastLevel = 'error' | 'warning'

export interface Toast {
  id: number
  message: string
  level: ToastLevel
}

let nextId = 0
let toasts: Toast[] = $state([])

export function addToast(message: string, level: ToastLevel = 'error'): void {
  // Deduplicate identical messages
  if (toasts.some(t => t.message === message && t.level === level))
    return

  const id = nextId++
  toasts.push({ id, message, level })

  if (level === 'warning') {
    setTimeout(dismissToast, 5000, id)
  }
}

export function dismissToast(id: number): void {
  toasts = toasts.filter(t => t.id !== id)
}

export function getToasts() {
  return {
    get list() { return toasts },
  }
}
