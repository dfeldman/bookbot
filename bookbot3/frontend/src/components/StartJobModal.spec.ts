import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import StartJobModal from './StartJobModal.vue';
import { createPinia, setActivePinia } from 'pinia';

// Mock the store
vi.mock('@/stores/book', () => ({
  useBookStore: () => ({})
}));


describe('StartJobModal.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  const chunk = {
    chunk_id: '1',
    book_id: '1',
    type: 'bot_task',
    text: 'Generate a story about a {{creature}} who finds a {{item}}.',
    props: {},
    chapter: 1,
    order: 1,
    word_count: 10,
    version: 1,
    is_locked: false,
    is_deleted: false,
    is_latest: true,
    created_at: '',
    updated_at: ''
  };

  it('renders correctly and identifies placeholders', async () => {
    const wrapper = mount(StartJobModal, {
      props: { chunk }
    });
    await flushPromises();

    expect(wrapper.find('h3').text()).toBe('Start Job: Untitled Task');
    const labels = wrapper.findAll('label');
    expect(labels.length).toBe(2);
    expect(labels[0].text()).toBe('creature');
    expect(labels[1].text()).toBe('item');
  });

  it('emits a close event when the close button is clicked', async () => {
    const wrapper = mount(StartJobModal, {
      props: { chunk }
    });
    await flushPromises();

    await wrapper.find('button.cancel-button').trigger('click');
    expect(wrapper.emitted().close).toBeTruthy();
  });

  it('emits a start-job event with placeholder values on form submission', async () => {
    const wrapper = mount(StartJobModal, {
      props: { chunk }
    });
    await flushPromises();

    const inputs = wrapper.findAll('input[type="text"]');
    expect(inputs.length).toBe(2);
    await inputs[0].setValue('dragon');
    await inputs[1].setValue('magical sword');

    await wrapper.find('button.start-button').trigger('click');

    expect(wrapper.emitted()['start-job']).toBeTruthy();
    expect(wrapper.emitted()['start-job'][0]).toEqual([{
      creature: 'dragon',
      item: 'magical sword'
    }]);
  });
});

