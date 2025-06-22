import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { ref } from 'vue';
import GenerateChunk from './GenerateChunk.vue';
import type { Chunk, LLMInfo } from '@/stores/types';

// Create a reusable mock store instance with proper types
const mockBookStore = {
  bots: ref<Chunk[]>([]),
  tasks: ref<Chunk[]>([]),
  llms: ref<LLMInfo[]>([]),
  llmDefaults: ref<{ default_llm_id: string } | null>(null),
  currentBook: ref({ book_id: 'book1' }),
  loadBots: vi.fn(),
  loadTasks: vi.fn(),
  loadLlmCatalog: vi.fn(),
  loadLlmDefaults: vi.fn(),
  startSceneGeneration: vi.fn(),
};

// Mock the store to return the same instance every time
vi.mock('@/stores/book', () => ({
  useBookStore: vi.fn(() => mockBookStore),
}));

describe('GenerateChunk.vue', () => {
  beforeEach(() => {
    // Reset state and mocks before each test
    vi.clearAllMocks();
    mockBookStore.bots.value = [];
    mockBookStore.tasks.value = [];
    mockBookStore.llms.value = [];
    mockBookStore.llmDefaults.value = null;
    mockBookStore.currentBook.value = { book_id: 'book1' };
    setActivePinia(createPinia());
  });

  const mockChunk: Chunk = {
    chunk_id: 'scene1',
    book_id: 'book1',
    type: 'scene',
    title: 'Test Scene',
    text: '',
    props: { target_word_count: 500 },
    is_locked: false,
    is_deleted: false,
    is_latest: true,
    version: 1,
    word_count: 0,
    created_at: '',
    updated_at: '',
  };

  const mockBots: Chunk[] = [
    { chunk_id: 'bot1', book_id: 'book1', type: 'bot', title: 'Bot 1', text: '', props: { name: 'Writer Bot' }, is_deleted: false, is_latest: true, version: 1, word_count: 0, created_at: '', updated_at: '' },
  ];

  const mockTasks: Chunk[] = [
    { chunk_id: 'task1', book_id: 'book1', type: 'bot_task', title: 'Task 1', text: '', props: { name: 'Write Scene', bot_id: 'bot1' }, is_deleted: false, is_latest: true, version: 1, word_count: 0, created_at: '', updated_at: '' },
  ];

  const mockLlms: LLMInfo[] = [
    { id: 'llm1', name: 'LLM One', output_cost_per_mtok: 10, input_cost_per_mtok: 5, context_length: 8000, company: 'AI Co', description: '', router: '', seconds_per_output_mtok: 1, groups: [], quality_score: 5 },
    { id: 'llm2', name: 'LLM Two', output_cost_per_mtok: 20, input_cost_per_mtok: 10, context_length: 8000, company: 'AI Co', description: '', router: '', seconds_per_output_mtok: 1, groups: [], quality_score: 5 },
  ];

  it('renders the component for a scene chunk', () => {
    const wrapper = mount(GenerateChunk, { props: { chunk: mockChunk } });
    expect(wrapper.find('h5').text()).toBe('Generate Scene');
    expect(wrapper.find('#bot-select').exists()).toBe(true);
  });

  it('loads data on mount', async () => {
    mount(GenerateChunk, { props: { chunk: mockChunk } });
    await flushPromises();
    expect(mockBookStore.loadBots).toHaveBeenCalledWith('book1');
    expect(mockBookStore.loadTasks).toHaveBeenCalledWith('book1');
    expect(mockBookStore.loadLlmCatalog).toHaveBeenCalled();
    expect(mockBookStore.loadLlmDefaults).toHaveBeenCalledWith('book1');
  });

  it('selects the default LLM on mount', async () => {
    mockBookStore.llms.value = mockLlms;
    mockBookStore.llmDefaults.value = { default_llm_id: 'llm2' };

    const wrapper = mount(GenerateChunk, { props: { chunk: mockChunk } });
    await flushPromises();

    const select = wrapper.find('#llm-select').element as HTMLSelectElement;
    // Options: 0: Default, 1: LLM One, 2: LLM Two
    expect(select.selectedIndex).toBe(2);
  });

  it('calculates cost estimate correctly', async () => {
    mockBookStore.llms.value = mockLlms;
    const wrapper = mount(GenerateChunk, { props: { chunk: mockChunk } });
    await flushPromises();

    // Select the first LLM ('LLM One') by manipulating the DOM and triggering a change event
    const llmSelect = wrapper.find('#llm-select');
    (llmSelect.findAll('option')[1].element as HTMLOptionElement).selected = true;
    await llmSelect.trigger('change');

    const cost = (500 / 2) * (10 / 1000000);
    expect(wrapper.find('.cost-estimate strong').text()).toBe(`$${cost.toFixed(4)}`);
  });

  it('calls startSceneGeneration with correct payload', async () => {
    mockBookStore.bots.value = mockBots;
    mockBookStore.tasks.value = mockTasks;
    mockBookStore.llms.value = mockLlms;

    const wrapper = mount(GenerateChunk, { props: { chunk: mockChunk } });
    await flushPromises();

    await wrapper.find('#bot-select').setValue('bot1');
    await wrapper.find('#task-select').setValue('task1');
    
    // Select the first LLM ('LLM One')
    const llmSelect = wrapper.find('#llm-select');
    (llmSelect.findAll('option')[1].element as HTMLOptionElement).selected = true;
    await llmSelect.trigger('change');
    
    await wrapper.find('button.btn-primary').trigger('click');

    expect(mockBookStore.startSceneGeneration).toHaveBeenCalledWith('scene1', 'bot1', 'task1', {
      llm_id: 'llm1',
      target_word_count: 500,
    });
  });

  it('disables UI and shows overlay when chunk is locked', async () => {
    const lockedChunk = { ...mockChunk, is_locked: true };
    const wrapper = mount(GenerateChunk, { props: { chunk: lockedChunk } });
    await flushPromises();

    expect(wrapper.find('.generating-overlay').exists()).toBe(true);
    const button = wrapper.find('button.btn-primary').element as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });
});
