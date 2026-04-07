import { vi } from 'vitest'

type EventHandler = (e: MessageEvent) => void

export class MockEventSource {
  static instances: MockEventSource[] = []

  url: string
  readyState = 0 // CONNECTING
  onerror: ((e: Event) => void) | null = null

  private listeners: Record<string, EventHandler[]> = {}

  constructor(url: string) {
    this.url = url
    MockEventSource.instances.push(this)
    // Simulate async open
    queueMicrotask(() => {
      this.readyState = 1 // OPEN
    })
  }

  addEventListener(type: string, handler: EventHandler): void {
    const list = this.listeners[type]
    if (list === undefined)
      this.listeners[type] = []
    this.listeners[type].push(handler)
  }

  removeEventListener(type: string, handler: EventHandler): void {
    const list = this.listeners[type]
    if (list !== undefined)
      this.listeners[type] = list.filter(h => h !== handler)
  }

  close(): void {
    this.readyState = 2 // CLOSED
  }

  // --- Test helpers ---

  /** Simulate a server-sent event */
  _emit(type: string, data: unknown): void {
    const json = typeof data === 'string' ? data : JSON.stringify(data)
    const event = new MessageEvent(type, { data: json })
    for (const handler of this.listeners[type] ?? [])
      handler(event)
  }

  /** Simulate an error (connection lost) */
  _emitError(): void {
    this.readyState = 2
    this.onerror?.(new Event('error'))
  }

  static latest(): MockEventSource | undefined {
    return MockEventSource.instances.at(-1)
  }

  static reset(): void {
    MockEventSource.instances = []
  }

  static install(): void {
    MockEventSource.reset()
    vi.stubGlobal('EventSource', MockEventSource)
  }

  static uninstall(): void {
    MockEventSource.reset()
    vi.unstubAllGlobals()
  }
}
