<template>
  <div class="llm-preference-selector">
    <div v-if="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading LLM Catalog...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>Could not load LLM catalog. Please try again later.</p>
    </div>

    <!-- Defaults Mode -->
    <div v-if="!isOverride" class="selector-grid">
      <div v-for="(group, groupName) in groupedLlms" :key="groupName" class="group-container">
        <label class="group-label">{{ formatGroupName(groupName) }}</label>
        <CustomLLMDropdown
          :llms="group"
          :modelValue="selectedLlms[groupName]"
          @update:modelValue="(llmId) => updateSelection(groupName, llmId)"
          defaultLabel="-- Default (Highest Quality) --"
        />
      </div>
    </div>

    <!-- Override Mode -->
    <div v-else class="override-container">
        <label class="group-label">Override Model</label>
        <CustomLLMDropdown
          :llms="allLlmsSorted"
          :modelValue="props.modelValue"
          @update:modelValue="updateOverrideSelection"
          defaultLabel="-- No Override --"
        />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { apiService, LLMInfo } from '../services/api';
import CustomLLMDropdown from './CustomLLMDropdown.vue';

const props = withDefaults(defineProps<{
  modelValue: Record<string, string> | string | null;
  isOverride?: boolean;
}>(), {
  modelValue: null,
  isOverride: false
});
const emit = defineEmits(['update:modelValue']);

const allLlms = ref<LLMInfo[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

const selectedLlms = ref<Record<string, string>>({});

watch(() => props.modelValue, (newValue) => {
  if (!props.isOverride && typeof newValue === 'object' && newValue !== null) {
    selectedLlms.value = { ...newValue };
  }
}, { immediate: true, deep: true });

onMounted(async () => {
  try {
    const response = await apiService.getLlmCatalog();
    allLlms.value = response.llms;
  } catch (e) {
    error.value = 'Failed to fetch LLMs';
    console.error(e);
  } finally {
    isLoading.value = false;
  }
});

const groupedLlms = computed(() => {
  const groups: Record<string, LLMInfo[]> = {};
  for (const llm of allLlms.value) {
    for (const groupName of llm.groups) {
      if (groupName === 'override') continue; // Exclude 'override' from groups
      if (!groups[groupName]) {
        groups[groupName] = [];
      }
      groups[groupName].push(llm);
    }
  }
  // Sort LLMs within each group by quality
  for (const groupName in groups) {
    groups[groupName].sort((a, b) => b.quality_score - a.quality_score);
  }
  return groups;
});

const allLlmsSorted = computed(() => {
  return [...allLlms.value].sort((a, b) => b.quality_score - a.quality_score);
});



function formatGroupName(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function updateSelection(groupName: string, llmId: string | null) {
  const newDefaults = { ...selectedLlms.value };
  if (llmId) {
    newDefaults[groupName] = llmId;
  } else {
    delete newDefaults[groupName];
  }
  selectedLlms.value = newDefaults;
  emit('update:modelValue', newDefaults);
}

function updateOverrideSelection(llmId: string | null) {
  emit('update:modelValue', llmId);
}
</script>

<style scoped>
.llm-preference-selector {
  padding: 1rem;
  background-color: #f9fafb;
  border-radius: 8px;
}

.loading-state, .error-state {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.spinner {
  margin: 0 auto 1rem auto;
  width: 24px;
  height: 24px;
  border: 3px solid #e5e7eb;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.selector-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.override-container {
  max-width: 400px;
}

.group-container, .override-container {
  display: flex;
  flex-direction: column;
}

.group-label {
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}
</style>
