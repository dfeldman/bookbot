<template>
  <div id="app">
    <StatusBar />
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAppStore } from './stores/app'
import StatusBar from './components/StatusBar.vue' // Added import

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
