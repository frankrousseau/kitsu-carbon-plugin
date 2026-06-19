<template>
  <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
    <div
      class="modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="info-modal-title"
    >
      <div class="modal-header">
        <h2 id="info-modal-title">{{ $t('carbon.info.title') }}</h2>
        <button class="close-btn" @click="$emit('close')">&times;</button>
      </div>
      <div class="modal-body">
        <p class="modal-text">{{ $t('carbon.info.description') }}</p>
        <div class="formula">
          <span>{{ $t('carbon.info.work_time') }}</span>
          <span class="operator">x</span>
          <span>{{ $t('carbon.info.people') }}</span>
          <span class="operator">x</span>
          <span class="highlight">{{ $t('carbon.info.carbon_factor') }}</span>
        </div>
        <div class="factors-section">
          <h3>{{ $t('carbon.info.factors_title') }}</h3>
          <div class="factor-grid">
            <div class="factor-item">
              <monitor :size="18" />
              <span>{{ $t('carbon.info.workstation') }}</span>
            </div>
            <div class="factor-item">
              <building2 :size="18" />
              <span>{{ $t('carbon.info.building_energy') }}</span>
            </div>
            <div class="factor-item">
              <zap :size="18" />
              <span>{{ $t('carbon.info.electricity_mix') }}</span>
            </div>
            <div class="factor-item">
              <utensils-crossed :size="18" />
              <span>{{ $t('carbon.info.meals') }}</span>
            </div>
            <div class="factor-item">
              <cloud :size="18" />
              <span>{{ $t('carbon.info.cloud_infra') }}</span>
            </div>
            <div class="factor-item">
              <train-front :size="18" />
              <span>{{ $t('carbon.info.commute') }}</span>
            </div>
          </div>
        </div>
        <a
          class="doc-link"
          :href="docPdfUrl"
          download
        >
          {{ $t('carbon.info.read_doc') }}
          <arrow-right :size="18" />
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ArrowRight,
  Cloud,
  Monitor,
  Building2,
  Zap,
  UtensilsCrossed,
  TrainFront
} from 'lucide-vue-next'
import docPdfUrl from '../assets/carbon-emissions-calculating-emissions.pdf'

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
  background: var(--bg-overlay);
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
  background: var(--bg-modal);
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
  color: var(--text-heading);
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1.5rem;
  line-height: 1;
}

.close-btn:hover {
  color: var(--text-heading);
}

.modal-text {
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.6;
  margin-bottom: 1.25rem;
}

.formula {
  align-items: center;
  background: var(--bg-card);
  border-radius: 8px;
  color: var(--text-primary);
  display: flex;
  font-family: monospace;
  font-size: 1rem;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 1.5rem;
  padding: 1.25rem;
}

.formula .operator {
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.formula .highlight {
  color: var(--accent-green);
}

.factors-section h3 {
  color: var(--text-secondary);
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
  background: var(--bg-surface);
  border-radius: 6px;
  color: var(--text-muted);
  display: flex;
  font-size: 0.875rem;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
}

.doc-link {
  align-items: center;
  background: var(--accent-green);
  border-radius: 8px;
  color: #fff;
  display: flex;
  font-size: 0.9375rem;
  font-weight: 600;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 1.5rem;
  padding: 0.875rem;
  text-decoration: none;
  width: 100%;
}

@media (max-width: 768px) {
  .modal-overlay {
    align-items: flex-end;
  }

  .modal {
    border-radius: 12px 12px 0 0;
    max-height: 90vh;
    max-width: none;
    overflow-y: auto;
    width: 100%;
  }

  .formula {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .factor-grid {
    grid-template-columns: 1fr;
  }

  .doc-link {
    display: flex;
  }
}
</style>
