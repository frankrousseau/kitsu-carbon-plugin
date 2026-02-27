<template>
  <div class="carbon-tracking">
    <footprint-header
      :subtitle="projectName"
      :unit="unit"
      @update:unit="unit = $event"
      @show-info="showInfo = true"
    />

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <template v-else>
      <stat-cards
        emissions-label="Total Project Emissions"
        man-days-subtitle="Cumulative across all steps"
        :total-co2-kg="data.total_co2_kg"
        :total-man-days="data.total_man_days"
        :weekly-average="weeklyAverage"
        :weekly-change-percent="data.weekly_change_percent"
        :unit-label="unitLabel"
        :format-value="formatValue"
        :format-number="formatNumber"
      />

      <view-tabs v-model="activeTab" breakdown-label="Step breakdown" />

      <div v-if="activeTab === 'matrix'" class="matrix-view table-scroll">
        <table class="matrix-table">
          <thead>
            <tr>
              <th>TASK TYPES</th>
              <th style="text-align: center">ALL</th>
              <th
                v-for="tt in taskTypes"
                :key="tt"
                :style="taskTypeHeaderStyle(tt)"
              >
                {{ tt }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr class="total-row">
              <td>All Task Types</td>
              <td>
                {{ formatValue(data.total_co2_kg) }}
              </td>
              <td
                v-for="tt in taskTypes"
                :key="tt"
                :style="taskTypeCellStyle(tt)"
              >
                {{ formatValue(getTaskTypeTotal(tt)) }}
              </td>
            </tr>
            <tr v-for="item in sortedByEmission" :key="item.task_type_id">
              <td>{{ item.task_type_name }}</td>
              <td>
                {{ formatValue(item.co2_kg) }}
              </td>
              <td
                v-for="tt in taskTypes"
                :key="tt"
                :class="
                  getImpactClass(
                    item.task_type_name === tt ? item.co2_kg : 0,
                    maxEmission
                  )
                "
                :style="taskTypeCellStyle(tt)"
              >
                {{
                  item.task_type_name === tt ? formatValue(item.co2_kg) : '-'
                }}
              </td>
            </tr>
          </tbody>
        </table>
        <impact-legend />
      </div>

      <div v-else class="breakdown-view">
        <table class="breakdown-table">
          <thead>
            <tr>
              <th>PRODUCTION STEP</th>
              <th>EMISSION IMPACT</th>
              <th>VALUE</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in sortedByEmission"
              :key="item.task_type_id"
              :style="taskTypeRowStyle(item.task_type_name)"
            >
              <td>{{ item.task_type_name }}</td>
              <td class="bar-cell">
                <div class="bar-track">
                  <div
                    class="bar-fill"
                    :class="getImpactClass(item.co2_kg, maxEmission)"
                    :style="{
                      width: getBarWidth(item.co2_kg, maxEmission) + '%'
                    }"
                  ></div>
                </div>
              </td>
              <td class="value-cell">
                <span class="kg">{{ formatValue(item.co2_kg) }} kg</span>
                <span class="percent"
                  >{{ getPercent(item.co2_kg, data.total_co2_kg) }}%</span
                >
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <info-modal :visible="showInfo" @close="showInfo = false" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useMainStore } from '../stores/main'
import { useCarbon } from '../composables/useCarbon'
import FootprintHeader from './FootprintHeader.vue'
import ViewTabs from './ViewTabs.vue'
import StatCards from './StatCards.vue'
import ImpactLegend from './ImpactLegend.vue'
import InfoModal from './InfoModal.vue'

const store = useMainStore()

const {
  unit,
  activeTab,
  showInfo,
  unitLabel,
  formatValue,
  formatNumber,
  getImpactClass,
  getBarWidth,
  getPercent,
  getTaskTypeColor,
  taskTypeHeaderStyle,
  taskTypeCellStyle
} = useCarbon()

const props = defineProps({
  productionId: {
    type: String,
    required: true
  }
})

const loading = ref(true)
const error = ref(null)
const projectName = ref('')
const data = ref({
  details: [],
  total_co2_kg: 0,
  total_man_days: 0
})

const allTaskTypes = computed(() => {
  if (store.taskTypes.length > 0) {
    return store.taskTypes.map((tt) => tt.name).sort()
  }
  const types = new Set()
  data.value.details.forEach((item) => types.add(item.task_type_name))
  return Array.from(types).sort()
})

const taskTypes = computed(() => {
  return allTaskTypes.value.filter((tt) => {
    return data.value.details.some(
      (item) => item.task_type_name === tt && item.co2_kg > 0
    )
  })
})

const sortedByEmission = computed(() => {
  return [...data.value.details].sort((a, b) => b.co2_kg - a.co2_kg)
})

const maxEmission = computed(() => {
  if (data.value.details.length === 0) return 1
  return Math.max(...data.value.details.map((d) => d.co2_kg))
})

const weeklyAverage = computed(() => {
  const prod = store.openProductions.find((p) => p.id === props.productionId)
  if (!prod || !prod.start_date) return 0
  const start = new Date(prod.start_date)
  const end = prod.end_date ? new Date(prod.end_date) : new Date()
  const ms = end - start
  const weeks = Math.max(ms / (7 * 24 * 60 * 60 * 1000), 1)
  return data.value.total_co2_kg / weeks
})

const getTaskTypeTotal = (taskTypeName) => {
  const item = data.value.details.find((d) => d.task_type_name === taskTypeName)
  return item ? item.co2_kg : 0
}

const taskTypeRowStyle = (taskTypeName) => {
  const color = getTaskTypeColor(taskTypeName)
  if (!color) return {}
  return {
    background: `${color}10`,
    borderBottom: `2px solid ${color}`
  }
}

const fetchData = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await fetch(
      `/api/plugins/carbon/productions/${props.productionId}/footprint/task-types`
    )
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const result = await response.json()
    data.value = result
    projectName.value = result.project_name || ''
  } catch (err) {
    error.value = `Failed to load data: ${err.message}`
  } finally {
    loading.value = false
  }
}

watch(
  () => props.productionId,
  () => fetchData(),
  { immediate: true }
)
</script>

<style scoped>
.carbon-tracking {
  background: #36393f;
  color: #e0e0e0;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  min-height: 100vh;
  padding: 1.5rem;
}

.loading,
.error {
  color: #888;
  padding: 2rem;
  text-align: center;
}

.error {
  color: #ff5252;
}

.table-scroll {
  overflow-x: auto;
}

.matrix-table {
  border: 1px solid #202225;
  border-collapse: collapse;
  border-radius: 6px;
  font-size: 0.875rem;
  min-width: max-content;
  overflow: hidden;
  width: 100%;
}

.matrix-table th,
.matrix-table td {
  min-width: 120px;
}

.matrix-table th {
  background: #42464e;
  border-bottom: 1px solid #202225;
  color: #fff;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  padding: 0.75rem;
  text-align: left;
  text-transform: uppercase;
}

.matrix-table td {
  border-bottom: 1px solid #202225;
  padding: 0.75rem;
  text-align: center;
}

.matrix-table td:first-child {
  color: #e0e0e0;
  text-align: left;
}

.matrix-table tbody tr:nth-child(odd) {
  background: #46494f;
}

.matrix-table tbody tr:nth-child(even) {
  background: #36393f;
}

.matrix-table .total-row {
  background: #4f525a !important;
}

.matrix-table .total-row td:first-child {
  font-weight: 600;
}

.matrix-table td.low {
  color: #00aa3c;
}
.matrix-table td.medium {
  color: #fb923c;
}
.matrix-table td.high {
  color: #ff5252;
}

.breakdown-table {
  border: 1px solid #202225;
  border-collapse: collapse;
  border-radius: 6px;
  overflow: hidden;
  width: 100%;
}

.breakdown-table th {
  background: #42464e;
  border-bottom: 1px solid #202225;
  color: #fff;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  padding: 0.75rem;
  text-align: left;
  text-transform: uppercase;
}

.breakdown-table td {
  border-bottom: 1px solid #202225;
  padding: 0.75rem;
}

.breakdown-table td:first-child {
  font-weight: 500;
  width: 150px;
}

.bar-cell {
  width: 60%;
}

.bar-track {
  background: #202225;
  border-radius: 4px;
  height: 24px;
  overflow: hidden;
}

.bar-fill {
  border-radius: 4px;
  height: 100%;
  transition: width 0.3s ease;
}

.bar-fill.low {
  background: #00aa3c;
}
.bar-fill.medium {
  background: #fb923c;
}
.bar-fill.high {
  background: #ff5252;
}

.value-cell {
  text-align: right;
  white-space: nowrap;
}

.value-cell .kg {
  display: block;
  font-weight: 600;
}

.value-cell .percent {
  color: #666;
  display: block;
  font-size: 0.75rem;
}
</style>
