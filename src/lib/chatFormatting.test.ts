import { describe, expect, it } from 'vitest'
import { parseChatMessageContent } from './chatFormatting'

describe('parseChatMessageContent', () => {
  it('keeps plain text, line breaks, bold, and italic as structured segments', () => {
    expect(parseChatMessageContent('Hello **world**\n*safe* <script>alert(1)</script>')).toEqual([
      { kind: 'text', text: 'Hello ' },
      { kind: 'bold', text: 'world' },
      { kind: 'break' },
      { kind: 'italic', text: 'safe' },
      { kind: 'text', text: ' <script>alert(1)</script>' },
    ])
  })

  it('leaves unmatched markers as plain text', () => {
    expect(parseChatMessageContent('Use *literal stars and **double stars')).toEqual([
      { kind: 'text', text: 'Use *literal stars and **double stars' },
    ])
  })
})
