<template>
  <div class="unit-toggle">
    <button
      :class="{ active: modelValue === 'kg' }"
      @click="$emit('update:modelValue', 'kg')"
    >
      kgCO2e
    </button>
    <button
      :class="{ active: modelValue === 't' }"
      @click="$emit('update:modelValue', 't')"
    >
      tCO2e
    </button>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    required: true
  }
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.unit-toggle {
  background: #202225;
  border: 3px solid #202225;
  border-radius: 6px;
  display: flex;
  overflow: hidden;
}

.unit-toggle button {
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #888;
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0.5rem 0.75rem;
}

.unit-toggle button.active {
  background: #42464e;
  color: #fff;
}
</style>
