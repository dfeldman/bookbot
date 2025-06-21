<template>
  <div class="chunk-content-editor">
    <MarkdownEditor v-if="modelValue.type === 'markdown'" :modelValue="text" @update:modelValue="updateText" />
    <BotEditor v-else-if="modelValue.type === 'bot'" :modelValue="modelValue" @update:modelValue="emit('update:modelValue', $event)" />
    <BotTaskEditor v-else-if="modelValue.type === 'bot_task'" :modelValue="modelValue" @update:modelValue="emit('update:modelValue', $event)" />
    <div v-else class="unsupported-type">
      Unsupported chunk type: {{ modelValue.type }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Chunk } from '@/stores/book';
import MarkdownEditor from '@/components/MarkdownEditor.vue';
import BotEditor from '@/components/BotEditor.vue';
import BotTaskEditor from '@/components/BotTaskEditor.vue';

const props = defineProps<{
  modelValue: Chunk;
}>();

const emit = defineEmits(['update:modelValue']);

const text = computed(() => props.modelValue.text || '');

function updateText(newText: string) {
  emit('update:modelValue', { ...props.modelValue, text: newText });
}

</script>

<style scoped>
.chunk-content-editor {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  padding: 1rem;
}
.unsupported-type {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
  border: 1px dashed #ccc;
  border-radius: 4px;
  margin: 1rem;
}
</style>