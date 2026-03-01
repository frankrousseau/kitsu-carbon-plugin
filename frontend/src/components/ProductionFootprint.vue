<template>
  <div class="carbon-tracking">
    <footprint-header
      :subtitle="projectName"
      :unit="unit"
      @update:unit="unit = $event"
      @show-info="showInfo = true"
    />

    <div v-if="initialLoading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <template v-else>
      <stat-cards
        emissions-label="Total Project Emissions"
        man-days-subtitle="Cumulative across all steps"
        :total-co2-kg="summary.total_co2_kg"
        :total-man-days="summary.total_man_days"
        :weekly-average="summary.weekly_average_co2_kg"
        :weekly-change-percent="data.weekly_change_percent"
        :unit-label="unitLabel"
        :format-value="formatValue"
        :format-number="formatNumber"
      />

      <view-tabs v-model="activeTab" breakdown-label="Step breakdown" />

      <div class="entity-filters">
        <button
          :class="{ active: entityFilter === 'Shot' }"
          @click="entityFilter = 'Shot'"
        >
          Shots
        </button>
        <button
          :class="{ active: entityFilter === 'Asset' }"
          @click="entityFilter = 'Asset'"
        >
          Assets
        </button>
      </div>

      <div v-if="loading" class="loading">Loading...</div>
      <div v-else-if="activeTab === 'matrix'" ref="tableScrollRef" class="matrix-view table-scroll">
        <table class="matrix-table">
          <thead>
            <tr>
              <th class="col-name">{{ rowLabel }}</th>
              <th class="col-total" style="text-align: center">ALL</th>
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
              <td class="col-name">All {{ rowLabel }}</td>
              <td class="col-total">
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
            <tr v-for="row in matrixRows" :key="row.name">
              <td class="col-name">{{ row.name }}</td>
              <td class="col-total">
                {{ formatValue(row.total) }}
              </td>
              <td
                v-for="tt in taskTypes"
                :key="tt"
                :class="getImpactClass(row.byTaskType[tt] || 0, maxEmission)"
                :style="taskTypeCellStyle(tt)"
              >
                {{ row.byTaskType[tt] ? formatValue(row.byTaskType[tt]) : '-' }}
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
              <th class="col-name">PRODUCTION STEP</th>
              <th>EMISSION IMPACT</th>
              <th>VALUE</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in breakdownRows"
              :key="item.name"
              :style="taskTypeRowStyle(item.name)"
            >
              <td class="col-name">{{ item.name }}</td>
              <td class="bar-cell">
                <div class="bar-track">
                  <div
                    class="bar-fill"
                    :class="getImpactClass(item.co2_kg, maxBreakdownEmission)"
                    :style="{
                      width: getBarWidth(item.co2_kg, maxBreakdownEmission) + '%'
                    }"
                  ></div>
                </div>
              </td>
              <td class="value-cell">
                <span class="kg">{{ formatValue(item.co2_kg) }} {{ unitLabel }}</span>
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
import { useDragScroll } from '../composables/useDragScroll'
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

const tableScrollRef = ref(null)
useDragScroll(tableScrollRef)

const props = defineProps({
  productionId: {
    type: String,
    required: true
  }
})

const entityFilter = ref('Shot')
const initialLoading = ref(true)
const loading = ref(false)
const error = ref(null)
const projectName = ref('')
const summary = ref({
  total_co2_kg: 0,
  total_man_days: 0,
  weekly_average_co2_kg: 0
})
const data = ref({
  details: [],
  by_task_type: {},
  total_co2_kg: 0,
  total_man_days: 0
})

const currentProduction = computed(() => {
  return store.openProductions.find((p) => p.id === props.productionId)
})

const isTVShow = computed(() => {
  return currentProduction.value?.production_type === 'tvshow'
})

const rowLabel = computed(() => {
  if (entityFilter.value === 'Asset') return 'ASSET TYPES'
  return isTVShow.value ? 'EPISODES' : 'SEQUENCES'
})

const groupNameField = computed(() => {
  if (entityFilter.value === 'Asset') return 'asset_type_name'
  return isTVShow.value ? 'episode_name' : 'sequence_name'
})

const footprintEndpoint = computed(() => {
  const base = `/api/plugins/carbon/productions/${props.productionId}/footprint`
  if (entityFilter.value === 'Asset') return `${base}/assets`
  return isTVShow.value ? `${base}/episodes` : `${base}/sequences`
})

const allTaskTypes = computed(() => {
  const prod = currentProduction.value
  if (prod && prod.task_types) {
    const taskTypeMap = {}
    store.taskTypes.forEach((tt) => {
      taskTypeMap[tt.id] = tt.name
    })
    return prod.task_types
      .map((id) => taskTypeMap[id])
      .filter(Boolean)
  }
  if (store.taskTypes.length > 0) {
    return store.taskTypes.map((tt) => tt.name)
  }
  const types = new Set()
  data.value.details.forEach((item) => types.add(item.task_type_name))
  return Array.from(types)
})

const taskTypes = computed(() => {
  const taskTypeEntityMap = {}
  store.taskTypes.forEach((tt) => {
    taskTypeEntityMap[tt.name] = tt.for_entity
  })
  return allTaskTypes.value.filter((tt) => {
    if (taskTypeEntityMap[tt] !== entityFilter.value) return false
    return data.value.details.some(
      (item) => item.task_type_name === tt && item.co2_kg > 0
    )
  })
})

const matrixRows = computed(() => {
  const nameField = groupNameField.value
  const rowMap = {}
  data.value.details.forEach((item) => {
    const name = item[nameField]
    if (!name) return
    if (!rowMap[name]) {
      rowMap[name] = { name, byTaskType: {}, total: 0 }
    }
    rowMap[name].byTaskType[item.task_type_name] =
      (rowMap[name].byTaskType[item.task_type_name] || 0) + item.co2_kg
    rowMap[name].total += item.co2_kg
  })
  return Object.values(rowMap).sort((a, b) => a.name.localeCompare(b.name))
})

const maxEmission = computed(() => {
  if (matrixRows.value.length === 0) return 1
  const allValues = matrixRows.value.flatMap((row) =>
    Object.values(row.byTaskType)
  )
  return Math.max(...allValues, 1)
})

const breakdownRows = computed(() => {
  const byTT = data.value.by_task_type || {}
  return Object.entries(byTT)
    .map(([name, val]) => ({ name, co2_kg: val.co2_kg }))
    .sort((a, b) => b.co2_kg - a.co2_kg)
})

const maxBreakdownEmission = computed(() => {
  if (breakdownRows.value.length === 0) return 1
  return Math.max(...breakdownRows.value.map((r) => r.co2_kg))
})

const getTaskTypeTotal = (taskTypeName) => {
  const byTT = data.value.by_task_type || {}
  return byTT[taskTypeName]?.co2_kg || 0
}

const taskTypeRowStyle = (taskTypeName) => {
  const color = getTaskTypeColor(taskTypeName)
  if (!color) return {}
  return {
    background: `${color}10`,
    borderBottom: `2px solid ${color}`
  }
}

const fetchSummary = async () => {
  try {
    const response = await fetch(
      `/api/plugins/carbon/productions/${props.productionId}/footprint/summary`
    )
    if (response.ok) {
      const result = await response.json()
      summary.value = result
      projectName.value = result.project_name || ''
    }
  } catch (err) {
    console.error('Failed to fetch summary:', err)
  }
}

const fetchData = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await fetch(footprintEndpoint.value)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const result = await response.json()
    data.value = result
  } catch (err) {
    error.value = `Failed to load data: ${err.message}`
  } finally {
    loading.value = false
    initialLoading.value = false
  }
}

watch(
  () => props.productionId,
  () => {
    fetchSummary()
    fetchData()
  },
  { immediate: true }
)

watch(isTVShow, () => fetchData())

watch(entityFilter, () => fetchData())
</script>

<style scoped>
.carbon-tracking {
  background: #36393f;
  color: #e0e0e0;
  display: flex;
  flex-direction: column;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  height: 100vh;
  overflow: hidden;
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

.entity-filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.entity-filters button {
  background: transparent;
  border: 1px solid #555;
  border-radius: 4px;
  color: #888;
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0.35rem 0.75rem;
}

.entity-filters button.active {
  background: #00aa3c;
  border-color: #00aa3c;
  color: #fff;
}

.table-scroll {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.breakdown-view {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.matrix-table {
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.875rem;
  min-width: max-content;
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
  position: sticky;
  text-align: left;
  text-transform: uppercase;
  top: 0;
  z-index: 2;
}

.matrix-table td {
  border-bottom: 1px solid #202225;
  padding: 0.75rem;
  text-align: center;
}

.matrix-table .col-name {
  color: #e0e0e0;
  left: 0;
  position: sticky;
  text-align: left;
  width: 200px;
  z-index: 1;
}

.matrix-table th.col-name {
  z-index: 3;
}

.matrix-table tbody tr:nth-child(odd) .col-name {
  background: #46494f;
}

.matrix-table tbody tr:nth-child(even) .col-name {
  background: #36393f;
}

.matrix-table .total-row .col-name {
  background: #4f525a;
}

.matrix-table .col-total {
  width: 120px;
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

.matrix-table .total-row .col-name {
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

.breakdown-table .col-name {
  font-weight: 500;
  width: 200px;
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
