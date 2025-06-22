<template>
  <div class="metadata-editor">
    <div class="form-group">
      <label for="chunk-name">Name</label>
      <input
        id="chunk-name"
        type="text"
        :value="displayName"
        @input="updateName(($event.target as HTMLInputElement).value)"
        :readonly="!isNameEditable"
        class="chunk-name-input"
        placeholder="[No name]"
      />
    </div>
    <div class="form-row">
      <div class="form-group">
        <label for="chunk-type">Type</label>
        <select id="chunk-type" :value="modelValue.type" @change="update('type', ($event.target as HTMLSelectElement).value)">
          <option value="scene">Scene</option>
          <option value="bot">Bot</option>
          <option value="bot_task">Bot Task</option>
        </select>
      </div>
      <div class="form-group">
        <label for="chunk-chapter">Chapter</label>
        <input id="chunk-chapter" type="number" :value="modelValue.chapter" @input="update('chapter', parseInt(($event.target as HTMLInputElement).value) || 0)" />
      </div>
      <div class="form-group">
        <label for="chunk-order">Order</label>
        <input id="chunk-order" type="number" :value="modelValue.order" @input="update('order', parseInt(($event.target as HTMLInputElement).value) || 0)" />
      </div>
    </div>

    <div class="form-group properties-editor">
      <label>Properties</label>
      <div v-for="(prop, index) in localProperties" :key="index" class="property-row">
        <input type="text" v-model="prop.key" placeholder="Key" @change="updateProperties" />
        <textarea v-model="prop.value" placeholder="Value (JSON)" @change="updateProperties" rows="1"></textarea>
        <button @click="removeProperty(index)" class="remove-btn">-</button>
      </div>
      <button @click="addProperty" class="add-btn">Add Property</button>
    </div>

    <div class="form-group">
      <label for="chunk-tags">Tags</label>
      <input id="chunk-tags" type="text" :value="tagsString" @input="updateTags(($event.target as HTMLInputElement).value)" placeholder="comma, separated, tags" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import type { Chunk } from '@/stores/book';

const props = defineProps<{
  modelValue: Chunk;
}>();

const emit = defineEmits(['update:modelValue']);

const localProperties = ref<{ key: string; value: string }[]>([]);
const tagsString = ref('');

const SINGLETON_CHUNK_TYPES = ['outline', 'brief', 'characters', 'settings', 'style'];

const isNameEditable = computed(() => {
  const type = props.modelValue.type;
  return !SINGLETON_CHUNK_TYPES.includes(type);
});

const displayName = computed(() => {
  const chunk = props.modelValue;
  if (SINGLETON_CHUNK_TYPES.includes(chunk.type)) {
    return chunk.type.charAt(0).toUpperCase() + chunk.type.slice(1);
  }
  if (chunk.type === 'scene') {
    return chunk.props?.scene_title || '';
  }
  return chunk.props?.name || '';
});

watch(() => props.modelValue.id, () => {
  if (props.modelValue && props.modelValue.props) {
    tagsString.value = (props.modelValue.props.tags || []).join(', ');
    const propsToEdit = { ...props.modelValue.props };
    // Exclude properties that have dedicated UI elements in other editors
    delete propsToEdit.tags;
    delete propsToEdit.name;
    delete propsToEdit.llm_group;
    delete propsToEdit.temperature;
    delete propsToEdit.applicable_jobs;
    if (props.modelValue.type === 'scene') {
      delete propsToEdit.scene_title;
    }
    localProperties.value = Object.entries(propsToEdit).map(([key, value]) => ({
      key,
      value: typeof value === 'string' ? value : JSON.stringify(value, null, 2),
    }));
  } else {
    tagsString.value = '';
    localProperties.value = [];
  }
}, { immediate: true });

function update<K extends keyof Chunk>(key: K, value: Chunk[K]) {
  emit('update:modelValue', { ...props.modelValue, [key]: value });
}

function updateProperties() {
  const newProps: { [key: string]: any } = {};

  const newTags = tagsString.value.split(',').map(tag => tag.trim()).filter(Boolean);
  if (newTags.length > 0) {
    newProps.tags = newTags;
  }

  localProperties.value.forEach(prop => {
    if (prop.key) {
      try {
        newProps[prop.key] = JSON.parse(prop.value);
      } catch (e) {
        newProps[prop.key] = prop.value;
      }
    }
  });
  update('props', newProps);
}

function addProperty() {
  localProperties.value.push({ key: '', value: '' });
}

function removeProperty(index: number) {
  localProperties.value.splice(index, 1);
  updateProperties();
}

function updateName(value: string) {
  if (!isNameEditable.value) return;

  const chunk = props.modelValue;
  let propToUpdate = 'name';
  if (chunk.type === 'scene') {
    propToUpdate = 'scene_title';
  }

  const newProps = { ...chunk.props, [propToUpdate]: value };
  update('props', newProps);
}

function updateTags(value: string) {
  tagsString.value = value;
  updateProperties();
}
</script>

<style scoped>
.chunk-name-input {
  font-size: 1.25rem;
  font-weight: 600;
  border: none;
  padding: 0.5rem;
  background-color: #f0f0f0;
  border-radius: 4px;
}

.metadata-editor {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
  background-color: #fdfdfd;
}
.form-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}
.form-group {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  margin-bottom: 1rem;
}
.form-group label {
  margin-bottom: 0.5rem;
  font-weight: bold;
  font-size: 0.875rem;
}
.form-group input, .form-group select, .form-group textarea {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.properties-editor .property-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5rem;
}
.property-row input {
  flex: 1;
}
.property-row textarea {
  flex: 2;
  font-family: monospace;
  resize: vertical;
}
.remove-btn, .add-btn {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
}
.remove-btn {
  background-color: #f44336;
  color: white;
  border: none;
}
.add-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  align-self: flex-start;
}
</style>