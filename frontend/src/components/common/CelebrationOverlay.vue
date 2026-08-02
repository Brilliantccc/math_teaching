<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  show: boolean
  type?: 'success' | 'encouragement' | 'milestone'
}>()

const emit = defineEmits<{
  (e: 'done'): void
}>()

const particles = ref<Array<{ id: number; x: number; y: number; delay: number; color: string }>>([])

const successMessages = [
  '太棒了！继续保持！',
  '答对了！你真厉害！',
  '完美！就是这个答案！',
  '做对了！越来越棒！',
  '正确！继续加油！'
]

const encouragementMessages = [
  '没关系，错误是学习的一部分',
  '再想想，你可以的！',
  '别灰心，下次一定能答对！',
  '加油，错误让你更强大！',
  '继续努力，你正在进步！'
]

const milestoneMessages = [
  '连续答对 5 题！',
  '练习时间超过 30 分钟！',
  '今天完成了所有目标！',
  '你已经掌握了这个知识点！'
]

function getMessage(type: string) {
  switch (type) {
    case 'success':
      return successMessages[Math.floor(Math.random() * successMessages.length)]
    case 'encouragement':
      return encouragementMessages[Math.floor(Math.random() * encouragementMessages.length)]
    case 'milestone':
      return milestoneMessages[Math.floor(Math.random() * milestoneMessages.length)]
    default:
      return successMessages[0]
  }
}

function createParticles() {
  const colors = ['#2563eb', '#16a34a', '#f59e0b', '#dc2626', '#8b5cf6']
  particles.value = Array.from({ length: 20 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    delay: Math.random() * 0.5,
    color: colors[Math.floor(Math.random() * colors.length)]
  }))
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    createParticles()
    setTimeout(() => {
      emit('done')
    }, 2000)
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="celebration">
      <div v-if="show" class="celebration-overlay" @click="emit('done')">
        <div class="celebration-content">
          <div class="celebration-icon">
            <template v-if="type === 'success'">
              <svg viewBox="0 0 24 24" class="check-icon">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" fill="currentColor"/>
              </svg>
            </template>
            <template v-else-if="type === 'encouragement'">
              <span class="encourage-emoji">💪</span>
            </template>
            <template v-else>
              <span class="milestone-emoji">🎉</span>
            </template>
          </div>
          <div class="celebration-message">
            {{ getMessage(type || 'success') }}
          </div>
        </div>

        <!-- 粒子效果 -->
        <div class="particles">
          <div
            v-for="particle in particles"
            :key="particle.id"
            class="particle"
            :style="{
              left: `${particle.x}%`,
              top: `${particle.y}%`,
              backgroundColor: particle.color,
              animationDelay: `${particle.delay}s`
            }"
          ></div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.celebration-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  z-index: 1000;
  cursor: pointer;
}

.celebration-content {
  background: var(--color-bg-card);
  padding: 48px;
  border-radius: var(--radius-xl);
  text-align: center;
  box-shadow: var(--shadow-modal);
  transform: scale(0.8);
  animation: bounce-in 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.celebration-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-success-bg);
  border-radius: 50%;
}

.check-icon {
  width: 48px;
  height: 48px;
  color: var(--color-success);
  animation: draw-check 0.5s ease-out 0.2s both;
}

.encourage-emoji,
.milestone-emoji {
  font-size: 48px;
  animation: pop-in 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s both;
}

.celebration-message {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.particles {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.particle {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: particle-fall 1.5s ease-out forwards;
}

@keyframes bounce-in {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes draw-check {
  0% {
    stroke-dasharray: 100;
    stroke-dashoffset: 100;
  }
  100% {
    stroke-dasharray: 100;
    stroke-dashoffset: 0;
  }
}

@keyframes pop-in {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes particle-fall {
  0% {
    transform: translateY(0) rotate(0deg);
    opacity: 1;
  }
  100% {
    transform: translateY(100vh) rotate(720deg);
    opacity: 0;
  }
}

.celebration-enter-active,
.celebration-leave-active {
  transition: opacity 0.3s ease;
}

.celebration-enter-from,
.celebration-leave-to {
  opacity: 0;
}
</style>
