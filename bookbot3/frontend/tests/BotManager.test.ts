import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia, type Pinia } from 'pinia';
import BotManager from '@/components/BotManager.vue';
import { useBookStore } from '@/stores/book';
import type { Chunk } from '@/stores/types';
import { apiService } from '@/services/api';

// Mock dependencies
vi.mock('@/services/api');
vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { bookId: 'book-1' } }),
}));

// Mock child components
const BotEditor = { template: '<div class="bot-editor-stub"></div>', props: ['modelValue'] };
const BotTaskEditor = { template: '<div class="bot-task-editor-stub"></div>', props: ['modelValue'] };

const createMockChunk = (id: string, name: string, type: 'bot' | 'bot_task'): Chunk => ({
  chunk_id: id,
  book_id: 'book-1',
  type,
  title: name,
  text: `Text for ${name}`,
  props: { name, llm_group: 'Writer', temperature: 0.7 },
  is_deleted: false,
  is_latest: true,
  version: 1,
  word_count: 5,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
});

const mockBots = [createMockChunk('bot-1', 'Creative Bot', 'bot')];
const mockBotTasks = [createMockChunk('task-1', 'Drafting Task', 'bot_task')];

describe('BotManager.vue', () => {
  let pinia: Pinia;
  let bookStore: ReturnType<typeof useBookStore>;

  const mountComponent = () => mount(BotManager, {
    global: {
      plugins: [pinia], // Use the shared pinia instance
      stubs: { BotEditor, BotTaskEditor },
    },
  });

  beforeEach(() => {
    vi.useFakeTimers();
    pinia = createPinia();
    setActivePinia(pinia);
    bookStore = useBookStore();
    bookStore.chunks = []; // Start with an empty store
    bookStore.updateChunkInStore = vi.fn();

    // Mock the API calls that the component and its store actions use
    vi.mocked(apiService.getChunks).mockResolvedValue({ chunks: [...mockBots, ...mockBotTasks] });
    vi.mocked(apiService.updateChunk).mockImplementation(async (id, data) => {
      const chunk = [...mockBots, ...mockBotTasks].find(c => c.chunk_id === id);
      // Return a new object to properly simulate an API response
      return { ...chunk, ...data, props: { ...chunk?.props, ...data.props } } as Chunk;
    });
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('loads and renders the list of bots and tasks on mount', async () => {
    const wrapper = mountComponent();
    expect(apiService.getChunks).toHaveBeenCalledWith('book-1');
    await flushPromises();
    expect(wrapper.text()).toContain('Creative Bot');
    expect(wrapper.text()).toContain('Drafting Task');
  });

  it('shows the BotEditor when a bot is selected', async () => {
    const wrapper = mountComponent();
    await flushPromises(); // Wait for chunks to load

    await wrapper.find('.item-list li').trigger('click'); // Clicks the first item (a bot)
    await flushPromises();

    const editor = wrapper.findComponent(BotEditor);
    expect(editor.exists()).toBe(true);
    expect(editor.props('modelValue')).toEqual(mockBots[0]);
  });

  it('creates a new bot and shows it in the editor', async () => {
    const createdBot = createMockChunk('new-bot-id', 'New Bot', 'bot');
    vi.mocked(apiService.createChunk).mockResolvedValue(createdBot);
    vi.mocked(apiService.getChunks).mockResolvedValueOnce({ chunks: [...mockBots, ...mockBotTasks] })
      .mockResolvedValueOnce({ chunks: [...mockBots, ...mockBotTasks, createdBot] });

    const wrapper = mountComponent();
    await flushPromises(); // Initial load

    await wrapper.findAll('button.create-button')[0].trigger('click'); // Clicks 'New Bot'
    await flushPromises();

    expect(apiService.createChunk).toHaveBeenCalledWith('book-1', expect.any(Object));
    expect(apiService.getChunks).toHaveBeenCalledTimes(2); // Initial load + reload after create

    const editor = wrapper.findComponent(BotEditor);
    expect(editor.exists()).toBe(true);
    const newBot = editor.props('modelValue') as Chunk;
    expect(newBot.chunk_id).toBe('new-bot-id');
  });

  it('auto-saves when the editor emits an update', async () => {
    const wrapper = mountComponent();
    await flushPromises(); // Initial load

    await wrapper.find('.item-list li').trigger('click'); // Select the bot
    await flushPromises();

    const editor = wrapper.findComponent(BotEditor);
    expect(editor.exists()).toBe(true);

    const updatedBot = { ...mockBots[0], text: 'Updated prompt' };
    await editor.vm.$emit('update:modelValue', updatedBot);

    await vi.runAllTimersAsync();
    await flushPromises();

    expect(apiService.updateChunk).toHaveBeenCalledWith(updatedBot.chunk_id, expect.any(Object));
    expect(bookStore.updateChunkInStore).toHaveBeenCalledWith(expect.objectContaining({ text: 'Updated prompt' }));
  });
});
