<template>
  <div class="chunk-content-editor">
    <MarkdownEditor v-if="isMarkdownChunk" :modelValue="text" @update:modelValue="updateText" />
    <BotEditor
      v-else-if="modelValue.type === 'bot'"
      :modelValue="modelValue"
      :is-saving="isSaving"
      :save-status="saveStatus"
      @update:modelValue="emit('update:modelValue', $event)"
      @save="emit('save')"
    />
    <BotTaskEditor
      v-else-if="modelValue.type === 'bot_task'"
      :modelValue="modelValue"
      :is-saving="isSaving"
      :save-status="saveStatus"
      @update:modelValue="emit('update:modelValue', $event)"
      @save="emit('save')"
    />
    <div v-else class="unsupported-type">
      Unsupported chunk type: {{ modelValue.type }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Chunk } from '@/stores/types';
import MarkdownEditor from '@/components/SceneEditor.vue';
import BotEditor from '@/components/BotEditor.vue';
import BotTaskEditor from '@/components/BotTaskEditor.vue';

const props = defineProps<{
  modelValue: Chunk;
  isSaving: boolean;
  saveStatus: string;
}>();

const emit = defineEmits(['update:modelValue', 'save']);

const isMarkdownChunk = computed(() => {
  const markdownTypes = ['scene', 'brief', 'outline', 'settings', 'characters'];
  return markdownTypes.includes(props.modelValue.type);
});

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