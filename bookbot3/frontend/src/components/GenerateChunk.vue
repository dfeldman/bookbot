<template>
  <div class="generate-chunk-panel" :class="{ 'is-locked': chunk.is_locked }">
    <h5>Generate Scene</h5>
        <div v-if="chunk.is_locked" class="generating-overlay">
      <div class="spinner"></div>
      <p>Generating content...</p>
    </div>
    <div v-if="chunk && chunk.type === 'scene'" :class="{ 'content-locked': chunk.is_locked }">
      <p>Use AI to generate content for this scene.</p>

      <div class="form-group">
        <label for="bot-select">Bot</label>
        <select id="bot-select" v-model="selectedBot" class="form-control" :disabled="chunk.is_locked">
          <option disabled value="">Select a bot</option>
          <option v-for="bot in bots" :key="bot.chunk_id" :value="bot.chunk_id">{{ bot.props?.name || bot.chunk_id }}</option>
        </select>
      </div>

      <div class="form-group">
        <label for="task-select">Task</label>
        <select id="task-select" v-model="selectedTask" class="form-control" :disabled="chunk.is_locked || !selectedBot">
          <option disabled value="">Select a task</option>
          <option v-for="task in availableTasks" :key="task.chunk_id" :value="task.chunk_id">{{ task.props?.name || task.chunk_id }}</option>
        </select>
      </div>

      <div class="form-group">
        <label for="llm-select">LLM</label>
        <select id="llm-select" v-model="selectedLlm" class="form-control" :disabled="chunk.is_locked">
          <option :value="null">Default</option>
          <option v-for="llm in llms" :key="llm.id" :value="llm">{{ llm.name }}</option>
        </select>
      </div>

      <div class="cost-estimate">
        <p>Estimated Cost: <strong>${{ costEstimate }}</strong></p>
      </div>

      <button @click="generate" class="btn btn-primary" :disabled="chunk.is_locked || !selectedBot || !selectedTask">
        Generate
      </button>

    </div>
    <div v-else>
      <p class="text-muted">Generation is only available for 'scene' chunks.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useBookStore } from '@/stores/book';
import { storeToRefs } from 'pinia';
import type { Chunk, LLMInfo } from '@/stores/types';

const props = defineProps<{
  chunk: Chunk;
}>();

const bookStore = useBookStore();
const { bots, tasks, llms, currentBook, llmDefaults } = storeToRefs(bookStore);

const selectedBot = ref('');
const selectedTask = ref('');
const selectedLlm = ref<LLMInfo | null>(null);

const costEstimate = computed(() => {
  if (!selectedLlm.value || !props.chunk.props?.target_word_count) {
    return '0.00';
  }
  const targetWordCount = props.chunk.props.target_word_count || 300;
  const cost = (targetWordCount / 2) * (selectedLlm.value.output_cost_per_mtok / 1000000);
  return cost.toFixed(4);
});

const availableTasks = computed(() => {
  if (!selectedBot.value) return [];
  return tasks.value.filter(t => t.props?.bot_id === selectedBot.value);
});

watch(selectedBot, () => {
  selectedTask.value = '';
});

async function generate() {
  if (!selectedBot.value || !selectedTask.value) {
    alert('Please select a Bot and a Task.');
    return;
  }

  try {
    const options: { llm_id?: string; target_word_count?: number } = {};
    if (selectedLlm.value) {
      options.llm_id = selectedLlm.value.id;
    }
    if (props.chunk.props?.target_word_count) {
      options.target_word_count = props.chunk.props.target_word_count;
    }

    await bookStore.startSceneGeneration(props.chunk.chunk_id, selectedBot.value, selectedTask.value, options);
  } catch (error) {
    console.error('Failed to start generation job:', error);
    alert('Failed to start generation. Please check the console for details.');
  }
}

onMounted(async () => {
  if (currentBook.value) {
    await Promise.all([
      bookStore.loadBots(currentBook.value.book_id),
      bookStore.loadTasks(currentBook.value.book_id),
      bookStore.loadLlmDefaults(currentBook.value.book_id)
    ]);
  }
  await bookStore.loadLlmCatalog();

  if (llmDefaults.value?.default_llm_id && llms.value.length > 0) {
    const defaultLlm = llms.value.find(llm => llm.id === llmDefaults.value.default_llm_id);
    if (defaultLlm) {
      selectedLlm.value = defaultLlm;
    }
  }
});
</script>

<style scoped>
.generate-chunk-panel {
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}
.form-group {
  margin-bottom: 1rem;
}
.cost-estimate {
  margin-top: 1rem;
  font-style: italic;
}

.generating-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10;
  border-radius: 4px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.content-locked {
  opacity: 0.5;
  pointer-events: none;
}
</style>
