<template>
  <div class="tabs">
    <button
      :class="{ active: modelValue === 'matrix' }"
      @click="$emit('update:modelValue', 'matrix')"
    >
      Matrix view
    </button>
    <button
      :class="{ active: modelValue === 'breakdown' }"
      @click="$emit('update:modelValue', 'breakdown')"
    >
      {{ breakdownLabel }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    required: true
  },
  breakdownLabel: {
    type: String,
    required: true
  }
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.tabs {
  border-bottom: 1px solid #202225;
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.tabs button {
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 0.875rem;
  padding: 0.75rem 0;
  position: relative;
}

.tabs button.active {
  color: #fff;
}

.tabs button.active::after {
  background: #00aa3c;
  bottom: -1px;
  content: '';
  height: 2px;
  left: 0;
  position: absolute;
  right: 0;
}
</style>
