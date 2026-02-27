<template>
  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-header">
        <span>{{ emissionsLabel }}</span>
        <cloud :size="20" />
      </div>
      <div class="stat-value">
        <span class="value">{{ formatValue(totalCo2Kg) }}</span>
        <span class="unit">{{ unitLabel }}</span>
      </div>
      <div
        v-if="weeklyChangePercent !== undefined"
        class="weekly-change"
        :class="changeClass"
      >
        <trending-up v-if="weeklyChangePercent > 0" :size="14" />
        <trending-down v-else-if="weeklyChangePercent < 0" :size="14" />
        <minus v-else :size="14" />
        <span>{{ changeLabel }} vs last week</span>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-header">
        <span>Weekly Average Emissions</span>
        <calendar :size="20" />
      </div>
      <div class="stat-value">
        <span class="value">{{ formatValue(weeklyAverage) }}</span>
        <span class="unit">{{ unitLabel }} / week</span>
      </div>
      <div class="stat-subtitle">Based on logged time</div>
    </div>

    <div class="stat-card">
      <div class="stat-header">
        <span>Total Man-Days</span>
        <users :size="20" />
      </div>
      <div class="stat-value">
        <span class="value">{{ formatNumber(totalManDays) }}</span>
        <span class="unit">logged</span>
      </div>
      <div class="stat-subtitle">{{ manDaysSubtitle }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  Cloud,
  Calendar,
  Users,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-vue-next'

const props = defineProps({
  emissionsLabel: {
    type: String,
    required: true
  },
  manDaysSubtitle: {
    type: String,
    required: true
  },
  totalCo2Kg: {
    type: Number,
    required: true
  },
  totalManDays: {
    type: Number,
    required: true
  },
  weeklyAverage: {
    type: Number,
    required: true
  },
  weeklyChangePercent: {
    type: Number,
    default: undefined
  },
  unitLabel: {
    type: String,
    required: true
  },
  formatValue: {
    type: Function,
    required: true
  },
  formatNumber: {
    type: Function,
    required: true
  }
})

const changeClass = computed(() => {
  const pct = props.weeklyChangePercent || 0
  if (pct > 0) return 'change-up'
  if (pct < 0) return 'change-down'
  return 'change-neutral'
})

const changeLabel = computed(() => {
  const pct = props.weeklyChangePercent || 0
  if (pct > 0) return `+${pct}%`
  if (pct < 0) return `${pct}%`
  return '0%'
})
</script>

<style scoped>
.stats-row {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(3, 1fr);
  margin-bottom: 1.5rem;
}

.stat-card {
  background: #202225;
  border-radius: 8px;
  padding: 1rem 1.25rem;
}

.stat-header {
  align-items: center;
  color: #888;
  display: flex;
  font-size: 0.875rem;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.stat-header svg {
  opacity: 0.5;
}

.stat-value {
  align-items: baseline;
  display: flex;
  gap: 0.5rem;
}

.stat-value .value {
  color: #fff;
  font-size: 2rem;
  font-weight: 600;
}

.stat-value .unit {
  color: #888;
  font-size: 0.875rem;
}

.stat-subtitle {
  color: #666;
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.weekly-change {
  align-items: center;
  border-radius: 4px;
  display: inline-flex;
  font-size: 0.75rem;
  font-weight: 500;
  gap: 0.35rem;
  margin-top: 0.5rem;
  padding: 0.25rem 0.6rem;
}

.weekly-change.change-up {
  background: rgba(255, 82, 82, 0.15);
  color: #ff5252;
}

.weekly-change.change-down {
  background: rgba(0, 170, 60, 0.15);
  color: #00aa3c;
}

.weekly-change.change-neutral {
  background: rgba(136, 136, 136, 0.15);
  color: #888;
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
