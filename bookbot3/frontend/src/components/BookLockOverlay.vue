<template>
  <div class="book-lock-overlay">
    <div class="overlay-content">
      <div class="spinner"></div>
      <h2>{{ title }}</h2>
      <p>{{ message }}</p>
      <p v-if="jobStatus">Job Status: {{ jobStatus }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">


defineProps({
  title: {
    type: String,
    default: 'Processing Book'
  },
  message: {
    type: String,
    default: 'Please wait while we prepare your book...'
  },
  jobStatus: {
    type: String,
    default: ''
  }
});
</script>

<style scoped>
.book-lock-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.75);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000; /* Ensure it's on top */
  color: white;
  text-align: center;
}

.overlay-content {
  padding: 20px;
  background-color: rgba(50, 50, 50, 0.9);
  border-radius: 8px;
}

.spinner {
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top: 4px solid #fff;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
