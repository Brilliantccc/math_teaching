import katex from 'katex'

/**
 * Render a string containing LaTeX (delimited by $...$ inline or $$...$$ display)
 * into an HTML string. Unknown / broken LaTeX is escaped and returned as-is.
 */
export function renderMathText(text: string): string {
  if (!text) return ''

  let result = text

  // Display math: $$...$$
  result = result.replace(/\$\$([\s\S]*?)\$\$/g, (_, tex) => {
    try {
      return katex.renderToString(tex.trim(), { displayMode: true, throwOnError: false })
    } catch {
      return `<code>${tex}</code>`
    }
  })

  // Inline math: $...$  (but not $$ which was already handled)
  result = result.replace(/(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)/g, (_, tex) => {
    try {
      return katex.renderToString(tex.trim(), { displayMode: false, throwOnError: false })
    } catch {
      return `<code>${tex}</code>`
    }
  })

  // Preserve newlines as <br>
  result = result.replace(/\n/g, '<br>')

  return result
}
