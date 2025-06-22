import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import BotEditor from './BotEditor.vue';
import type { Chunk } from '../stores/types';

// Mock MarkdownEditor to isolate BotEditor logic and avoid its complexity.
const MockMarkdownEditor = {
  template: '<textarea :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)"></textarea>',
  props: ['modelValue']
};

const createMockChunk = (overrides = {}): Chunk => ({
  chunk_id: 'bot-123',
  book_id: 'book-abc',
  type: 'bot',
  title: 'Test Bot Title',
  text: 'You are a helpful assistant.',
  props: {
    name: 'Test Bot',
    llm_group: 'Writer',
    temperature: 0.7,
  },
  is_deleted: false,
  is_latest: true,
  version: 1,
  word_count: 5,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

describe('BotEditor.vue', () => {
  const mountOptions = {
    props: {
      modelValue: createMockChunk(),
    },
    global: {
      stubs: {
        MarkdownEditor: MockMarkdownEditor,
      },
    },
  };

  it('renders bot properties correctly from modelValue', () => {
    const wrapper = mount(BotEditor, mountOptions);

    const nameInput = wrapper.find('#bot-name').element as HTMLInputElement;
    expect(nameInput.value).toBe('Test Bot');

    const markdownEditor = wrapper.findComponent(MockMarkdownEditor);
    expect(markdownEditor.props('modelValue')).toBe('You are a helpful assistant.');

    const llmGroupSelect = wrapper.find('#llm-group').element as HTMLSelectElement;
    expect(llmGroupSelect.value).toBe('Writer');

    const tempInput = wrapper.find('#temperature').element as HTMLInputElement;
    expect(tempInput.value).toBe('0.7');
  });

  it('emits update:modelValue when the name is changed', async () => {
    const wrapper = mount(BotEditor, mountOptions);
    await wrapper.find('#bot-name').setValue('Updated Bot Name');

    const emittedEvents = wrapper.emitted('update:modelValue');
    expect(emittedEvents).toBeDefined();
    expect(emittedEvents).toHaveLength(1);
    const emittedChunk = emittedEvents![0][0] as Chunk;
    expect(emittedChunk.props).toBeDefined();
    expect(emittedChunk.props!.name).toBe('Updated Bot Name');
    expect(emittedChunk.text).toBe('You are a helpful assistant.'); // Ensure other fields are preserved
  });

  it('emits update:modelValue when the system prompt is changed', async () => {
    const wrapper = mount(BotEditor, mountOptions);
    const markdownEditor = wrapper.findComponent(MockMarkdownEditor);
    await markdownEditor.vm.$emit('update:modelValue', 'A new system prompt.');

    const emittedEvents = wrapper.emitted('update:modelValue');
    expect(emittedEvents).toBeDefined();
    expect(emittedEvents).toHaveLength(1);
    const emittedChunk = emittedEvents![0][0] as Chunk;
    expect(emittedChunk.text).toBe('A new system prompt.');
    expect(emittedChunk.props).toBeDefined();
    expect(emittedChunk.props!.name).toBe('Test Bot'); // Ensure other fields are preserved
  });

  it('emits update:modelValue when the LLM group is changed', async () => {
    const wrapper = mount(BotEditor, mountOptions);
    await wrapper.find('#llm-group').setValue('Editor');

    const emittedEvents = wrapper.emitted('update:modelValue');
    expect(emittedEvents).toBeDefined();
    expect(emittedEvents).toHaveLength(1);
    const emittedChunk = emittedEvents![0][0] as Chunk;
    expect(emittedChunk.props).toBeDefined();
    expect(emittedChunk.props!.llm_group).toBe('Editor');
  });

  it('emits update:modelValue when the temperature is changed', async () => {
    const wrapper = mount(BotEditor, mountOptions);
    await wrapper.find('#temperature').setValue('1.2');

    const emittedEvents = wrapper.emitted('update:modelValue');
    expect(emittedEvents).toBeDefined();
    expect(emittedEvents).toHaveLength(1);
    const emittedChunk = emittedEvents![0][0] as Chunk;
    expect(emittedChunk.props).toBeDefined();
    expect(emittedChunk.props!.temperature).toBe(1.2);
  });
  
  it('updates local state when modelValue prop changes externally', async () => {
    const wrapper = mount(BotEditor, mountOptions);

    // Verify initial state
    let nameInput = wrapper.find('#bot-name').element as HTMLInputElement;
    expect(nameInput.value).toBe('Test Bot');

    // Simulate parent updating the prop
    const updatedChunk = createMockChunk({
      text: 'Updated externally',
      props: { name: 'External Update Bot', llm_group: 'Thinker', temperature: 1.5 }
    });
    await wrapper.setProps({ modelValue: updatedChunk });

    // Verify component reflects new prop values
    nameInput = wrapper.find('#bot-name').element as HTMLInputElement;
    expect(nameInput.value).toBe('External Update Bot');
    const markdownEditor = wrapper.findComponent(MockMarkdownEditor);
    expect(markdownEditor.props('modelValue')).toBe('Updated externally');
    const llmGroupSelect = wrapper.find('#llm-group').element as HTMLSelectElement;
    expect(llmGroupSelect.value).toBe('Thinker');
    const tempInput = wrapper.find('#temperature').element as HTMLInputElement;
    expect(tempInput.value).toBe('1.5');
  });
});
