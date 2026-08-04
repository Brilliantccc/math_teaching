/** 应用入口 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import 'katex/dist/katex.min.css'

import App from './App.vue'
import router from './router'
import './styles/tokens.css'
import './styles/global.css'

// 全局错误处理 - 防止未捕获的错误导致应用崩溃
window.addEventListener('error', (event) => {
  console.error('[Global] Uncaught error:', event.error)
  // 阻止默认行为（控制台报错）
  event.preventDefault()
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('[Global] Unhandled promise rejection:', event.reason)
  // 阻止默认行为（控制台报错）
  event.preventDefault()
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Antd)

app.mount('#app')
