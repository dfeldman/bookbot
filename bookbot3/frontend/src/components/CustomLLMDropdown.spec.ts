import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import CustomLLMDropdown from './CustomLLMDropdown.vue';
import type { LLMInfo } from '../services/api';

const mockLlms: LLMInfo[] = [
  {
    id: 'llm-1',
    name: 'Test LLM 1',
    company: 'TestCo',
    quality_score: 8,
    context_length: 8000,
    input_cost_per_mtok: 0.5,
    output_cost_per_mtok: 1.5,
    description: '',
    router: 'test',
    seconds_per_output_mtok: 0,
    groups: ['writer']
  },
  {
    id: 'llm-2',
    name: 'Test LLM 2',
    company: 'TestCo',
    quality_score: 9,
    context_length: 16000,
    input_cost_per_mtok: 1.0,
    output_cost_per_mtok: 2.0,
    description: '',
    router: 'test',
    seconds_per_output_mtok: 0,
    groups: ['writer', 'editor']
  }
];

describe('CustomLLMDropdown.vue', () => {
  it('renders the default label when no value is selected', () => {
    const wrapper = mount(CustomLLMDropdown, {
      props: {
        llms: mockLlms,
        modelValue: null,
        defaultLabel: '-- Select Model --'
      }
    });
    expect(wrapper.find('.default-label').text()).toBe('-- Select Model --');
  });

  it('displays the selected LLM name when a value is provided', () => {
    const wrapper = mount(CustomLLMDropdown, {
      props: {
        llms: mockLlms,
        modelValue: 'llm-1',
        defaultLabel: '-- Select Model --'
      }
    });
    expect(wrapper.find('.dropdown-toggle').text()).toContain('Test LLM 1 (TestCo)');
  });

  it('opens the dropdown on click', async () => {
    const wrapper = mount(CustomLLMDropdown, { props: { llms: mockLlms, modelValue: null, defaultLabel: 'Test' } });
    expect(wrapper.find('.dropdown-menu').exists()).toBe(false);
    await wrapper.find('.dropdown-toggle').trigger('click');
    expect(wrapper.find('.dropdown-menu').exists()).toBe(true);
  });

  it('emits update:modelValue when an item is selected', async () => {
    const wrapper = mount(CustomLLMDropdown, { props: { llms: mockLlms, modelValue: null, defaultLabel: 'Test' } });
    await wrapper.find('.dropdown-toggle').trigger('click');
    await wrapper.findAll('.dropdown-item')[1].trigger('click'); // Select the first mock LLM

    expect(wrapper.emitted('update:modelValue')).toBeTruthy();
    expect(wrapper.emitted('update:modelValue')![0]).toEqual(['llm-1']);
  });

  it('emits null when the default option is selected', async () => {
    const wrapper = mount(CustomLLMDropdown, { props: { llms: mockLlms, modelValue: 'llm-1', defaultLabel: 'Test' } });
    await wrapper.find('.dropdown-toggle').trigger('click');
    await wrapper.find('.dropdown-item').trigger('click'); // Select the default option

    expect(wrapper.emitted('update:modelValue')).toBeTruthy();
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([null]);
  });

  it('closes the dropdown after selection', async () => {
    const wrapper = mount(CustomLLMDropdown, { props: { llms: mockLlms, modelValue: null, defaultLabel: 'Test' } });
    await wrapper.find('.dropdown-toggle').trigger('click');
    expect(wrapper.find('.dropdown-menu').exists()).toBe(true);

    await wrapper.findAll('.dropdown-item')[1].trigger('click');
    expect(wrapper.find('.dropdown-menu').exists()).toBe(false);
  });
});
