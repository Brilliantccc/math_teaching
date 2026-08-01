<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores'
import AppLayout from '@/components/layout/AppLayout.vue'

const authStore = useAuthStore()

onMounted(async () => {
  await authStore.init()
})
</script>

<template>
  <AppLayout>
    <router-view />
  </AppLayout>
</template>

<style>
#app {
  min-height: 100vh;
}
</style>
