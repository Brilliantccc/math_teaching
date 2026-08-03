/** 年级状态管理 */

import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { GRADES as BASE_GRADES } from '@/constants'

// 在基础年级列表前添加"全部"选项
export const GRADES = ['全部', ...BASE_GRADES]

export const useGradeStore = defineStore('grade', () => {
  const currentGrade = ref(localStorage.getItem('grade') || '初一')

  function setGrade(grade: string) {
    if (GRADES.includes(grade)) {
      currentGrade.value = grade
      localStorage.setItem('grade', grade)
    }
  }

  // 获取用于API的年级参数（全部返回空字符串）
  function getGradeParam() {
    return currentGrade.value === '全部' ? '' : currentGrade.value
  }

  // 监听变化
  watch(currentGrade, (newGrade) => {
    localStorage.setItem('grade', newGrade)
  })

  return {
    currentGrade,
    setGrade,
    getGradeParam,
    grades: GRADES
  }
})
