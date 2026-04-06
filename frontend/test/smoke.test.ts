import { describe, expect, it } from 'vitest'

describe('test setup', () => {
  it('vitest runs', () => {
    expect(1 + 1).toBe(2)
  })

  it('jsdom is available', () => {
    const div = document.createElement('div')
    div.textContent = 'hello'
    document.body.appendChild(div)
    expect(document.body.textContent).toContain('hello')
  })

  it('testing-library matchers work', () => {
    const div = document.createElement('div')
    div.textContent = 'visible'
    document.body.appendChild(div)
    expect(div).toBeVisible()
  })
})
