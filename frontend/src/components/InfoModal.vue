<template>
  <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
    <div
      class="modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="info-modal-title"
    >
      <div class="modal-header">
        <h2 id="info-modal-title">How is carbon calculated?</h2>
        <button class="close-btn" @click="$emit('close')">&times;</button>
      </div>
      <p class="modal-text">
        Emissions are estimated based on logged working time per task and
        geographic carbon factors specific to each production facility.
      </p>
      <div class="formula">
        <span>Work Time</span>
        <span class="operator">x</span>
        <span>People</span>
        <span class="operator">x</span>
        <span class="highlight">Carbon Factor</span>
      </div>
      <div class="factors-section">
        <h3>WHAT'S INCLUDED IN THE CARBON FACTOR:</h3>
        <div class="factor-grid">
          <div class="factor-item">
            <monitor :size="18" />
            <span>Workstation</span>
          </div>
          <div class="factor-item">
            <building2 :size="18" />
            <span>Building Energy</span>
          </div>
          <div class="factor-item">
            <zap :size="18" />
            <span>Electricity Mix</span>
          </div>
          <div class="factor-item">
            <utensils-crossed :size="18" />
            <span>Meals</span>
          </div>
          <div class="factor-item">
            <cloud :size="18" />
            <span>Cloud & Infra</span>
          </div>
          <div class="factor-item">
            <train-front :size="18" />
            <span>Commute</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  Cloud,
  Monitor,
  Building2,
  Zap,
  UtensilsCrossed,
  TrainFront
} from 'lucide-vue-next'

defineProps({
  visible: {
    type: Boolean,
    required: true
  }
})
defineEmits(['close'])
</script>

<style scoped>
.modal-overlay {
  align-items: center;
  background: rgba(0, 0, 0, 0.7);
  bottom: 0;
  display: flex;
  justify-content: center;
  left: 0;
  position: fixed;
  right: 0;
  top: 0;
  z-index: 100;
}

.modal {
  background: #36393f;
  border-radius: 12px;
  max-width: 520px;
  padding: 1.5rem;
  width: 90%;
}

.modal-header {
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.modal-header h2 {
  color: #fff;
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.close-btn {
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 1.5rem;
  line-height: 1;
}

.close-btn:hover {
  color: #fff;
}

.modal-text {
  color: #888;
  font-size: 0.875rem;
  line-height: 1.6;
  margin-bottom: 1.25rem;
}

.formula {
  align-items: center;
  background: #202225;
  border-radius: 8px;
  color: #e0e0e0;
  display: flex;
  font-family: monospace;
  font-size: 1rem;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 1.5rem;
  padding: 1.25rem;
}

.formula .operator {
  color: #666;
  font-size: 0.875rem;
}

.formula .highlight {
  color: #00aa3c;
}

.factors-section h3 {
  color: #888;
  font-size: 0.7rem;
  letter-spacing: 0.05em;
  margin-bottom: 0.75rem;
  text-transform: uppercase;
}

.factor-grid {
  display: grid;
  gap: 0.5rem;
  grid-template-columns: 1fr 1fr;
}

.factor-item {
  align-items: center;
  background: #42464e;
  border-radius: 6px;
  color: #ccc;
  display: flex;
  font-size: 0.875rem;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
}
</style>
