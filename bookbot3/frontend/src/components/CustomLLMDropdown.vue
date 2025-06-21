<template>
  <div class="custom-llm-dropdown" ref="dropdownRef">
    <button @click="toggleDropdown" class="dropdown-toggle">
      <span v-if="selectedLlm">{{ selectedLlm.name }} ({{ selectedLlm.company }})</span>
      <span v-else class="default-label">{{ defaultLabel }}</span>
      <span class="toggle-arrow" :class="{ 'is-open': isOpen }"></span>
    </button>
    <transition name="fade">
      <div v-if="isOpen" class="dropdown-menu">
        <div class="dropdown-item" @click="selectLlm(null)">
          {{ defaultLabel }}
        </div>
        <div v-for="llm in llms" :key="llm.id" class="dropdown-item" @click="selectLlm(llm.id)">
          <div class="item-header">
            <strong class="item-name">{{ llm.name }}</strong>
            <span class="item-company">{{ llm.company }}</span>
          </div>
          <div class="item-details">
            <span>Q: {{ llm.quality_score }}/10</span>
            <span>{{ (llm.context_length / 1000).toFixed(0) }}k ctx</span>
            <span>${{ llm.input_cost_per_mtok.toFixed(2) }}/M tok</span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import type { LLMInfo } from '../services/api';

const props = withDefaults(defineProps<{
  llms: LLMInfo[];
  modelValue: string | null;
  defaultLabel?: string;
}>(), {
  modelValue: null
});

const emit = defineEmits(['update:modelValue']);

const isOpen = ref(false);
const dropdownRef = ref<HTMLElement | null>(null);

const selectedLlm = computed(() => {
  return props.llms.find(llm => llm.id === props.modelValue);
});

function toggleDropdown() {
  isOpen.value = !isOpen.value;
}

function selectLlm(llmId: string | null) {
  emit('update:modelValue', llmId);
  isOpen.value = false;
}

function handleClickOutside(event: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isOpen.value = false;
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
.custom-llm-dropdown {
  position: relative;
  width: 100%;
}

.dropdown-toggle {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background-color: white;
  font-size: 0.875rem;
  text-align: left;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.default-label {
  color: #6b7280;
}

.toggle-arrow {
  border: solid #6b7280;
  border-width: 0 2px 2px 0;
  display: inline-block;
  padding: 3px;
  transform: rotate(45deg);
  transition: transform 0.2s ease;
}

.toggle-arrow.is-open {
  transform: rotate(-135deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background-color: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  margin-top: 0.25rem;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.dropdown-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background-color: #f9fafb;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.item-name {
  font-weight: 600;
  color: #1f2937;
}

.item-company {
  font-size: 0.8rem;
  color: #6b7280;
}

.item-details {
  display: flex;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: #4b5563;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
