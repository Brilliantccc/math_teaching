/** 年级状态管理 */

import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { GRADES, MIDDLE_SCHOOL_GRADES, HIGH_SCHOOL_GRADES } from '@/constants'

// 重新导出 GRADES 供其他组件使用
export { GRADES }

export const useGradeStore = defineStore('grade', () => {
  const currentGrade = ref(localStorage.getItem('grade') || '初一上')

  function setGrade(grade: string) {
    currentGrade.value = grade
    localStorage.setItem('grade', grade)
  }

  // 获取用于API的年级参数（全部返回空字符串，初中全部/高中全部返回对应年级数组）
  function getGradeParam() {
    if (currentGrade.value === '全部') return ''
    if (currentGrade.value === '初中全部') return MIDDLE_SCHOOL_GRADES.join(',')
    if (currentGrade.value === '高中全部') return HIGH_SCHOOL_GRADES.join(',')
    return currentGrade.value
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
