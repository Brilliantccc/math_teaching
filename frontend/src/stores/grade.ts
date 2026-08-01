/** 年级状态管理 */

import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const GRADES = ['初一', '初二', '初三', '高一', '高二', '高三']

export const useGradeStore = defineStore('grade', () => {
  const currentGrade = ref(localStorage.getItem('grade') || '初一')

  function setGrade(grade: string) {
    if (GRADES.includes(grade)) {
      currentGrade.value = grade
      localStorage.setItem('grade', grade)
    }
  }

  // 监听变化
  watch(currentGrade, (newGrade) => {
    localStorage.setItem('grade', newGrade)
  })

  return {
    currentGrade,
    setGrade,
    grades: GRADES
  }
})
