/**
 * 数学公式渲染工具
 * 使用 KaTeX 支持 \text{中文} 和公式混合内容
 */

import katex from 'katex'

// 内联图片样式
const inlineImageStyle = `
  <style>
    .inline-image {
      display: inline-block;
      max-height: 200px;
      max-width: 100%;
      vertical-align: middle;
      margin: 0 6px;
      border-radius: 4px;
      border: 1px solid #e8e8e8;
      background: #fafafa;
      object-fit: contain;
    }
    .inline-image:hover {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      transform: scale(1.02);
      transition: all 0.2s ease;
    }
    .image-reference {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 3px 10px;
      border-radius: 14px;
      font-size: 11px;
      font-weight: 500;
      margin: 0 6px;
      vertical-align: middle;
      cursor: default;
      transition: transform 0.2s, box-shadow 0.2s;
      box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
    }
    .image-reference:hover {
      transform: scale(1.05);
      box-shadow: 0 3px 8px rgba(102, 126, 234, 0.4);
    }
    .image-reference::before {
      content: "📷";
      font-size: 12px;
    }
  </style>
`

/**
 * 渲染文本中的 LaTeX 公式
 * 支持格式：
 * - $\text{中文}a=2$ → 中文和公式混合
 * - $a^2+b^2=c^2$ → 纯公式
 * - $$\frac{1}{2}$$ → 块级公式
 * - {{img:0}} → 图片引用
 */
export function renderMathText(text: string, images?: string[]): string {
  if (!text) return ''

  let result = text

  // 修复数据库存储的双反斜杠（如 \\text → \text，\\\\text → \text）
  // 多层转义：先处理四重，再处理双重
  // 注意：数据库中存储的是 \text{答案}$，不需要修复
  // 只有当出现 \\text（双反斜杠）时才需要修复
  result = result.replace(/\\\\text/g, '\\text')
  result = result.replace(/\\\\triangle/g, '\\triangle')
  result = result.replace(/\\\\angle/g, '\\angle')
  result = result.replace(/\\\\parallel/g, '\\parallel')
  result = result.replace(/\\\\frac/g, '\\frac')
  result = result.replace(/\\\\sqrt/g, '\\sqrt')
  result = result.replace(/\\\\times/g, '\\times')
  result = result.replace(/\\\\div/g, '\\div')
  result = result.replace(/\\\\pm/g, '\\pm')
  result = result.replace(/\\\\leq/g, '\\leq')
  result = result.replace(/\\\\geq/g, '\\geq')
  result = result.replace(/\\\\neq/g, '\\neq')

  // 清理 HTML 标签，避免干扰 KaTeX 渲染
  // 将 <br> 和 <br/> 替换为换行符占位符
  result = result.replace(/<br\s*\/?>/gi, '\x00BR\x00')

  // 移除其他 HTML 标签，但要保护数学公式中的 < 符号
  // 只匹配已知的 HTML 标签，避免误伤数学公式
  result = result.replace(/<(\/?)(?:p|div|span|b|i|u|strong|em|font|img|a|ul|ol|li|h[1-6]|table|tr|td|th|thead|tbody)[^>]*>/gi, '')

  // 第零步：处理图片引用 {{img:N}}
  // 将图片引用替换为实际的 <img> 标签
  result = result.replace(/\{\{img:(\d+)\}\}/g, (_, index) => {
    const imgIndex = parseInt(index)
    if (images && images[imgIndex]) {
      // 获取图片URL，处理相对路径
      let imgSrc = images[imgIndex]
      if (!imgSrc.startsWith('http') && !imgSrc.startsWith('data:')) {
        // 相对路径，直接使用（浏览器会相对于当前页面解析）
        imgSrc = imgSrc
      }
      // 返回内联图片，支持hover效果
      return `<img src="${imgSrc}" class="inline-image" alt="配图${imgIndex + 1}" loading="lazy" onerror="this.style.display='none'"/>`
    }
    // 如果没有图片，显示指引文字
    return `<span class="image-reference">[图${imgIndex + 1}]</span>`
  })

  // 预处理：将包含中文的数学公式转换为 \text{} 包裹（允许公式内有换行符）
  // 这样 KaTeX 不会产生 Unicode 警告
  result = result.replace(/\$([\s\S]+?)\$/g, (match, tex) => {
    // 如果公式中包含中文字符，且没有使用 \text{} 包裹
    if (/[一-龥]/.test(tex) && !/\\text\s*\{/.test(tex)) {
      // 将中文字符用 \text{} 包裹
      const wrapped = tex.replace(/([一-龥，。、；：？！（）]+)/g, '\\text{$1}')
      return `$${wrapped}$`
    }
    return match
  })

  // 第一步：处理 $$...$$ 块级公式
  const blockPlaceholders: string[] = []
  result = result.replace(/\$\$([\s\S]*?)\$\$/g, (_, tex) => {
    const index = blockPlaceholders.length
    try {
      blockPlaceholders.push(
        katex.renderToString(tex.trim(), { displayMode: true, throwOnError: false, strict: false })
      )
    } catch (e) {
      console.warn('KaTeX block render error:', e)
      blockPlaceholders.push(`<i>${tex}</i>`)
    }
    return `\x00B${index}\x00`
  })

  // 第二步：处理 $...$ 行内公式（允许公式内有换行符）
  const inlinePlaceholders: string[] = []
  result = result.replace(/\$([\s\S]+?)\$/g, (_, tex) => {
    const index = inlinePlaceholders.length
    try {
      const html = katex.renderToString(tex.trim(), { displayMode: false, throwOnError: false, strict: false })
      inlinePlaceholders.push(html)
    } catch (e) {
      console.warn('KaTeX inline render error:', e)
      inlinePlaceholders.push(`<i>${tex}</i>`)
    }
    return `\x00I${index}\x00`
  })

  // 第三步：还原图片占位符（现在图片占位符已经直接转换为指引文字，不需要还原）

  // 第四步：还原公式占位符（KaTeX 输出的是安全的 HTML）
  blockPlaceholders.forEach((html, i) => {
    result = result.replace(`\x00B${i}\x00`, html)
  })
  inlinePlaceholders.forEach((html, i) => {
    result = result.replace(`\x00I${i}\x00`, html)
  })

  // 将换行符占位符转换为<br>标签
  result = result.replace(/\x00BR\x00/g, '<br>')

  // 处理普通换行符，但不能破坏 HTML 标签内的内容（如 KaTeX SVG 路径）
  // 策略：只在 HTML 标签之间的文本部分替换换行
  result = result.replace(/(<[^>]+>)|(\n)/g, (match, tag, newline) => {
    if (tag) return tag // HTML 标签原样返回
    return '<br>'       // 换行符替换为 <br>
  })

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
