<template>
  <div v-if="isLoading" class="loading-pane">Loading...</div>
  <div v-else-if="chunkData" class="chunk-editor-layout">
    <ChunkEditorHeader
      :book-id="chunkData.book_id"
      :save-status="saveStatus"
      :is-saving="isSaving"
      :is-bot-task="isBotTask"
      @save="saveChunk"
      @delete="showDeleteModal = true"
      @show-versions="showVersionHistory = true"
      @start-job="showStartJobModal = true"
    />
    <main class="editor-main">
      <div class="editor-container">
        <ChunkMetadataEditor v-model="chunkData" />
        <ChunkContentEditor v-model="chunkData" />
      </div>
      <aside class="sidebar">
        <ContextPanel :chunkId="chunkId" />
        <GenerateChunkPanel :chunkId="chunkId" />
      </aside>
    </main>

    <!-- Modals -->
    <DeleteConfirmationModal
      v-if="showDeleteModal"
      title="Delete Chunk"
      message="Are you sure you want to delete this chunk? This action cannot be undone."
      confirm-text="Delete"
      @close="showDeleteModal = false"
      @confirm="deleteChunk"
    />
    <VersionHistoryModal
      v-if="showVersionHistory"
      :chunkId="chunkId"
      @close="showVersionHistory = false"
    />
    <StartJobModal 
      v-if="showStartJobModal && chunkData"
      :chunk="chunkData"
      @close="showStartJobModal = false"
      @start-job="handleStartJob"
    />
  </div>
  <div v-else class="error-pane">Could not load chunk data.</div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useBookStore } from '../stores/book';
import { apiService } from '../services/api';
import type { Chunk } from '@/stores/book';

// Import new sub-components
import ChunkEditorHeader from '@/components/chunk-editor/ChunkEditorHeader.vue';
import ChunkMetadataEditor from '@/components/chunk-editor/ChunkMetadataEditor.vue';
import ChunkContentEditor from '@/components/chunk-editor/ChunkContentEditor.vue';
import DeleteConfirmationModal from '@/components/modals/DeleteConfirmationModal.vue';

// Import existing components
import ContextPanel from '@/components/ContextPanel.vue';
import GenerateChunkPanel from '@/components/GenerateChunkPanel.vue';
import VersionHistoryModal from '@/components/VersionHistoryModal.vue';
import StartJobModal from '@/components/StartJobModal.vue';

const route = useRoute();
const router = useRouter();
const bookStore = useBookStore();

const chunkId = route.params.chunkId as string;
const chunkData = ref<Chunk | null>(null);
const isLoading = ref(true);
const isSaving = ref(false);
const saveStatus = ref('Saved');

// Modal states
const showDeleteModal = ref(false);
const showVersionHistory = ref(false);
const showStartJobModal = ref(false);

let autoSaveTimer: number | undefined;

// Computed properties
const isBotTask = computed(() => chunkData.value?.type === 'bot_task');

// Load initial chunk data
onMounted(async () => {
  try {
    const data = await bookStore.loadChunk(chunkId);
    // Deep clone and set defaults to ensure all reactive properties exist
    chunkData.value = JSON.parse(JSON.stringify(data));
  } catch (error) {
    console.error('Failed to load chunk:', error);
  } finally {
    isLoading.value = false;
  }
});

// Autosave functionality
watch(chunkData, (newVal, oldVal) => {
  if (oldVal && newVal) { // only trigger on changes after initial load
    saveStatus.value = 'Unsaved changes';
    clearTimeout(autoSaveTimer);
    autoSaveTimer = window.setTimeout(() => {
      saveChunk();
    }, 3000);
  }
}, { deep: true });

// Cleanup timer on unmount
onBeforeUnmount(() => {
  clearTimeout(autoSaveTimer);
});

// --- Actions ---
async function saveChunk() {
  if (!chunkData.value) return;
  isSaving.value = true;
  saveStatus.value = 'Saving...';
  clearTimeout(autoSaveTimer);
  try {
    const payload = {
      text: chunkData.value.text,
      props: chunkData.value.props,
      type: chunkData.value.type,
    };
    const updated = await apiService.updateChunk(chunkData.value.chunk_id, payload);
    bookStore.updateChunkInStore(updated); // Update the store with the canonical version
    saveStatus.value = 'Saved';
  } catch (error) {
    console.error('Failed to save chunk:', error);
    saveStatus.value = 'Error saving!';
  } finally {
    isSaving.value = false;
  }
}

async function deleteChunk() {
  if (!chunkData.value) return;
  try {
    await apiService.deleteChunk(chunkData.value.chunk_id);
    router.push(`/books/${chunkData.value.book_id}`);
  } catch (error) {
    console.error('Failed to delete chunk:', error);
    // Optionally show an error message to the user
  }
}

async function handleStartJob(placeholderValues: Record<string, string>) {
  if (!chunkData.value) return;
  try {
    await bookStore.startGenerateChunkJob(chunkData.value.chunk_id, placeholderValues);
    console.log('Job started successfully');
    // Optionally, show a success notification to the user
  } catch (error) {
    console.error('Failed to start job:', error);
    // Optionally, show an error notification to the user
  }
  showStartJobModal.value = false;
}
</script>

<style scoped>
.chunk-editor-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.editor-main {
  display: flex;
  flex-grow: 1;
  overflow: hidden;
}

.editor-container {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto; /* Allows metadata and content to scroll */
}

.sidebar {
  width: 350px;
  flex-shrink: 0;
  border-left: 1px solid #e0e0e0;
  background-color: #f7f7f7;
  overflow-y: auto;
  padding: 1rem;
}

.loading-pane, .error-pane {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  font-size: 1.2rem;
  color: #6c757d;
}
</style>
