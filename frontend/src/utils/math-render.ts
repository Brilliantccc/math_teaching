/**
 * 数学公式渲染工具
 * 使用 KaTeX 支持 \text{中文} 和公式混合内容
 */

import katex from 'katex'

/**
 * 渲染文本中的 LaTeX 公式
 * 支持格式：
 * - $\text{中文}a=2$ → 中文和公式混合
 * - $a^2+b^2=c^2$ → 纯公式
 * - $$\frac{1}{2}$$ → 块级公式
 */
export function renderMathText(text: string): string {
  if (!text) return ''

  let result = text

  // 修复数据库存储的双反斜杠（如 \\text → \text）
  result = result.replace(/\\\\([a-zA-Z]+)/g, '\\$1')

  // 第一步：处理 $$...$$ 块级公式
  const blockPlaceholders: string[] = []
  result = result.replace(/\$\$([\s\S]*?)\$\$/g, (_, tex) => {
    const index = blockPlaceholders.length
    try {
      blockPlaceholders.push(
        katex.renderToString(tex.trim(), { displayMode: true, throwOnError: false })
      )
    } catch (e) {
      console.warn('KaTeX block render error:', e)
      blockPlaceholders.push(`<i>${tex}</i>`)
    }
    return `\x00B${index}\x00`
  })

  // 第二步：处理 $...$ 行内公式
  const inlinePlaceholders: string[] = []
  result = result.replace(/\$([^\$\n]+?)\$/g, (_, tex) => {
    const index = inlinePlaceholders.length
    try {
      inlinePlaceholders.push(
        katex.renderToString(tex.trim(), { displayMode: false, throwOnError: false })
      )
    } catch (e) {
      console.warn('KaTeX inline render error:', e)
      inlinePlaceholders.push(`<i>${tex}</i>`)
    }
    return `\x00I${index}\x00`
  })

  // 第三步：还原占位符（KaTeX 输出的是安全的 HTML）
  blockPlaceholders.forEach((html, i) => {
    result = result.replace(`\x00B${i}\x00`, html)
  })
  inlinePlaceholders.forEach((html, i) => {
    result = result.replace(`\x00I${i}\x00`, html)
  })

  // 将换行符转换为<br>标签
  result = result.replace(/\n/g, '<br>')

  return result
}

/**
 * 触发页面重新渲染（KaTeX 是即时渲染，此函数为空）
 */
export async function typesetMath(): Promise<void> {
  // KaTeX 是即时渲染，无需额外操作
}

/**
 * 渲染指定元素内的数学公式（KaTeX 是即时渲染，此函数为空）
 */
export async function typesetElement(_element: HTMLElement): Promise<void> {
  // KaTeX 是即时渲染，无需额外操作
}
