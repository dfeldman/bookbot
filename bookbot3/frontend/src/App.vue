<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAppStore } from './stores/app'

const appStore = useAppStore()

onMounted(() => {
  appStore.initialize()
})
</script>

<style>
#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
