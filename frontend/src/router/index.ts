/** Vue Router 配置 */

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

    // 主页面
    {
      path: '/',
      name: 'Home',
      component: () => import('@/views/Home.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/browse',
      name: 'Browse',
      component: () => import('@/views/Browse.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/practice',
      name: 'Practice',
      component: () => import('@/views/Practice.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/practice/stats',
      name: 'PracticeStats',
      component: () => import('@/views/PracticeStats.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/wrong-questions',
      name: 'WrongQuestions',
      component: () => import('@/views/WrongQuestions.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/test',
      name: 'Test',
      component: () => import('@/views/Test.vue'),
      meta: { requiresAuth: true }
    },

    // 教师功能
    {
      path: '/manage',
      name: 'Manage',
      component: () => import('@/views/Manage.vue'),
      meta: { requiresAuth: true, requiresTeacher: true }
    },
    {
      path: '/upload',
      name: 'Upload',
      component: () => import('@/views/Upload.vue'),
      meta: { requiresAuth: true, requiresTeacher: true }
    },
    {
      path: '/question/edit/:id',
      name: 'QuestionEdit',
      component: () => import('@/views/QuestionEdit.vue'),
      meta: { requiresAuth: true, requiresTeacher: true }
    },
    {
      path: '/paper-manage',
      name: 'PaperManage',
      component: () => import('@/views/PaperManage.vue'),
      meta: { requiresAuth: true, requiresTeacher: true }
    },
    {
      path: '/student-data',
      name: 'StudentData',
      component: () => import('@/views/StudentData.vue'),
      meta: { requiresAuth: true, requiresTeacher: true }
    },

    // 其他
    {
      path: '/change-password',
      name: 'ChangePassword',
      component: () => import('@/views/ChangePassword.vue'),
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

  // 初始化认证状态
  if (!authStore.isAuthenticated && authStore.token) {
    await authStore.init()
  }

  // 检查是否需要认证
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
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
