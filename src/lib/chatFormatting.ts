export type ChatMessageSegment =
  | { kind: 'text'; text: string }
  | { kind: 'bold'; text: string }
  | { kind: 'italic'; text: string }
  | { kind: 'break' }

function pushTextSegment(
  segments: ChatMessageSegment[],
  kind: 'text' | 'bold' | 'italic',
  text: string
) {
  if (!text) return
  segments.push({ kind, text })
}

export function parseChatMessageContent(content: string): ChatMessageSegment[] {
  const segments: ChatMessageSegment[] = []
  const normalized = content.replace(/\r\n/g, '\n')

  let index = 0
  let buffer = ''

  const flushText = (kind: 'text' | 'bold' | 'italic' = 'text') => {
    pushTextSegment(segments, kind, buffer)
    buffer = ''
  }

  while (index < normalized.length) {
    const char = normalized[index]

    if (char === '\n') {
      flushText()
      segments.push({ kind: 'break' })
      index += 1
      continue
    }

    if (char === '*' && normalized[index + 1] === '*') {
      const closeIndex = normalized.indexOf('**', index + 2)
      if (closeIndex !== -1) {
        flushText()
        const boldText = normalized.slice(index + 2, closeIndex)
        pushTextSegment(segments, 'bold', boldText)
        index = closeIndex + 2
        continue
      }
    }

    if (char === '*') {
      const closeIndex = normalized.indexOf('*', index + 1)
      const closesSingleItalic =
        closeIndex !== -1 &&
        normalized[closeIndex - 1] !== '*' &&
        normalized[closeIndex + 1] !== '*'

      if (closesSingleItalic) {
        flushText()
        const italicText = normalized.slice(index + 1, closeIndex)
        pushTextSegment(segments, 'italic', italicText)
        index = closeIndex + 1
        continue
      }
    }

    buffer += char
    index += 1
  }

  flushText()

  return segments
}
