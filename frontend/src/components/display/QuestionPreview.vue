<script setup lang="ts">
import { computed, ref } from 'vue'
import LatexText from './LatexText.vue'

const props = withDefaults(defineProps<{
  content: string
  images?: string[]
  showImages?: boolean
  compact?: boolean
}>(), {
  showImages: false,
  compact: false
})

const parsedImages = computed(() => {
  if (!props.images) return []
  try {
    return Array.isArray(props.images) ? props.images : JSON.parse(props.images)
  } catch {
    return []
  }
})

// 是否显示右侧图片区域
const shouldShowSidebar = computed(() => {
  return props.showImages && parsedImages.value.length > 0
})

// 图片加载状态管理
const imageErrors = ref<Record<string, boolean>>({})

function handleImageError(index: string | number) {
  imageErrors.value[String(index)] = true
}

function isImageError(index: string | number): boolean {
  return imageErrors.value[String(index)] === true
}

// 获取图片URL，处理相对路径
function getImageSrc(img: string): string {
  if (!img) return ''
  if (img.startsWith('http')) return img
  // 直接返回相对路径，由浏览器处理
  return img
}
</script>

<template>
  <div class="question-preview" :class="{ compact, 'has-images': shouldShowSidebar }">
    <!-- 主内容区域 -->
    <div class="question-main">
      <!-- 题干文字 -->
      <div class="question-content" :class="{ compact }">
        <LatexText :content="content" :images="images" />
      </div>
    </div>

    <!-- 右侧图片展示区域 -->
    <div v-if="shouldShowSidebar" class="question-sidebar" :class="{ compact }">
      <div class="image-list">
        <div
          v-for="(img, index) in parsedImages"
          :key="index"
          class="image-item"
          :class="{ 'image-error': isImageError(index) }"
        >
          <template v-if="!isImageError(index)">
            <img
              :src="getImageSrc(img)"
              :alt="`配图${Number(index) + 1}`"
              class="question-image"
              @error="handleImageError(index)"
              loading="lazy"
            />
          </template>
          <template v-else>
            <div class="image-fallback">
              <span class="fallback-icon">🖼️</span>
              <span class="fallback-text">图片加载失败</span>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.question-preview {
  display: flex;
  gap: 16px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  overflow: hidden;
  background: var(--color-bg-card);
  transition: box-shadow 0.2s;
}

.question-preview:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.question-preview.compact {
  border: none;
  border-radius: 0;
  background: transparent;
  gap: 8px;
}

.question-preview.compact:hover {
  box-shadow: none;
}

/* 主内容区域 */
.question-preview.has-images .question-main {
  flex: 1;
  min-width: 0;
}

.question-content {
  padding: 16px 20px;
  line-height: 1.8;
  font-size: 14px;
  color: var(--color-text-body);
}

.question-content.compact {
  padding: 10px 12px;
  line-height: 1.6;
  font-size: 13px;
}

/* 右侧图片区域 */
.question-sidebar {
  width: 160px;
  flex-shrink: 0;
  padding: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.question-sidebar.compact {
  width: 120px;
  padding: 8px;
}

.image-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.image-list.compact {
  gap: 4px;
}

.image-item {
  position: relative;
  border-radius: 6px;
  overflow: hidden;
  background: #f8f9fa;
  border: 1px solid #e8e8e8;
  transition: all 0.2s ease;
}

.image-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.question-image {
  width: 100%;
  height: auto;
  max-height: 120px;
  object-fit: contain;
  display: block;
}

.compact .question-image {
  max-height: 80px;
}

/* 图片加载失败时的回退样式 */
.image-fallback {
  width: 100%;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #8c8c8c;
  gap: 4px;
}

.compact .image-fallback {
  height: 60px;
}

.fallback-icon {
  font-size: 18px;
  opacity: 0.5;
}

.compact .fallback-icon {
  font-size: 14px;
}

.fallback-text {
  font-size: 10px;
  text-align: center;
}

.compact .fallback-text {
  font-size: 9px;
}

.image-item.image-error {
  border-style: dashed;
  border-color: #d9d9d9;
}

/* 无图片时的样式 */
.question-preview:not(.has-images) {
  display: block;
}
</style>
