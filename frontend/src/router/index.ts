/** Vue Router 路由配置 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 认证页面
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/auth/Register.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/forgot-password',
      name: 'ForgotPassword',
      component: () => import('@/views/auth/ForgotPassword.vue'),
      meta: { requiresAuth: false }
    },

    // 主页
    {
      path: '/',
      name: 'Home',
      component: () => import('@/views/Home.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/browse',
      name: 'Browse',
      component: () => import('@/views/browse/Browse.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/practice',
      name: 'Practice',
      component: () => import('@/views/practice/Practice.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/practice/stats',
      name: 'PracticeStats',
      component: () => import('@/views/practice/PracticeStats.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/wrong-questions',
      name: 'WrongQuestions',
      component: () => import('@/views/practice/WrongQuestions.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/test',
      name: 'Test',
      component: () => import('@/views/test/Test.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/test-manage',
      name: 'TestManage',
      component: () => import('@/views/test/TestManage.vue'),
      meta: { requiresAuth: true, requiresTeacher: true }
    },

    // 教师功能
    {
      path: '/manage',
      name: 'Manage',
      component: () => import('@/views/manage/Manage.vue'),
      meta: { requiresAuth: true, requiresTeacher: true }
    },
    {
      path: '/upload',
      name: 'Upload',
      component: () => import('@/views/upload/Upload.vue'),
      meta: { requiresAuth: true, requiresTeacher: true }
    },
    {
      path: '/question/edit/:id',
      name: 'QuestionEdit',
      component: () => import('@/views/manage/QuestionEdit.vue'),
      meta: { requiresAuth: true, requiresTeacher: true }
    },
    {
      path: '/paper-manage',
      name: 'PaperManage',
      component: () => import('@/views/manage/PaperManage.vue'),
      meta: { requiresAuth: true, requiresTeacher: true }
    },
    {
      path: '/student-data',
      name: 'StudentData',
      component: () => import('@/views/student/StudentData.vue'),
      meta: { requiresAuth: true, requiresTeacher: true }
    },

    // 其他
    {
      path: '/change-password',
      name: 'ChangePassword',
      component: () => import('@/views/auth/ChangePassword.vue'),
      meta: { requiresAuth: true }
    },

    // 404
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 初始化认证状态（只在首次导航时调用）
  // 添加超时保护，防止网络请求阻塞导航
  if (authStore.token && !authStore.userFetched) {
    try {
      // 使用 Promise.race 添加5秒超时
      await Promise.race([
        authStore.init(),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Auth init timeout')), 5000))
      ])
    } catch (error) {
      console.warn('[Router] Auth init failed or timeout:', error)
      // 即使初始化失败，也允许继续导航
    }
  }

  // 检查是否需要认证
  // 如果有 token 但用户信息还没获取到，允许继续（等待异步完成）
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated && !authStore.token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // 检查是否需要教师权限
  if (to.meta.requiresTeacher && !authStore.isTeacher) {
    next({ name: 'Home' })
    return
  }

  // 如果已登录访问登录页，重定向到首页
  if (to.name === 'Login' && authStore.isAuthenticated) {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router