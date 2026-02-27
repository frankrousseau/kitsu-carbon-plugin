<template>
  <div class="carbon-tracking">
    <footprint-header
      subtitle="All Productions"
      :unit="unit"
      @update:unit="unit = $event"
      @show-info="showInfo = true"
    />

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <template v-else>
      <stat-cards
        emissions-label="Total Studio Emissions"
        man-days-subtitle="Cumulative across all productions"
        :total-co2-kg="data.total_co2_kg"
        :total-man-days="data.total_man_days"
        :weekly-average="weeklyAverage"
        :weekly-change-percent="data.weekly_change_percent"
        :unit-label="unitLabel"
        :format-value="formatValue"
        :format-number="formatNumber"
      />

      <view-tabs v-model="activeTab" breakdown-label="Production breakdown" />

      <div v-if="activeTab === 'matrix'" class="matrix-view table-scroll">
        <table class="matrix-table">
          <thead>
            <tr>
              <th>PRODUCTIONS</th>
              <th style="text-align: center">ALL STEPS</th>
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
              <td>All Productions</td>
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
            <tr v-for="prod in productions" :key="prod.name">
              <td>{{ prod.name }}</td>
              <td>
                {{ formatValue(prod.total) }}
              </td>
              <td
                v-for="tt in taskTypes"
                :key="tt"
                :class="
                  getImpactClass(
                    getProductionTaskType(prod.name, tt),
                    maxEmission
                  )
                "
                :style="taskTypeCellStyle(tt)"
              >
                {{ formatValueOrDash(getProductionTaskType(prod.name, tt)) }}
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
              <th>PRODUCTION</th>
              <th>EMISSION IMPACT</th>
              <th>VALUE</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="prod in productions" :key="prod.name">
              <td>{{ prod.name }}</td>
              <td class="bar-cell">
                <div class="bar-track">
                  <div
                    class="bar-fill"
                    :class="getImpactClass(prod.total, maxEmission)"
                    :style="{
                      width: getBarWidth(prod.total, maxEmission) + '%'
                    }"
                  ></div>
                </div>
              </td>
              <td class="value-cell">
                <span class="kg">{{ formatValue(prod.total) }} kg</span>
                <span class="percent"
                  >{{ getPercent(prod.total, data.total_co2_kg) }}%</span
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
import { ref, computed, onMounted } from 'vue'
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
  formatValueOrDash,
  formatNumber,
  getImpactClass,
  getBarWidth,
  getPercent,
  taskTypeHeaderStyle,
  taskTypeCellStyle
} = useCarbon()

const loading = ref(true)
const error = ref(null)
const data = ref({
  details: [],
  by_project: {},
  by_task_type: {},
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
    return productions.value.some((prod) => prod.taskTypes[tt] > 0)
  })
})

const productions = computed(() => {
  const prodMap = {}
  data.value.details.forEach((item) => {
    if (!prodMap[item.project_name]) {
      prodMap[item.project_name] = {
        name: item.project_name,
        total: 0,
        taskTypes: {}
      }
    }
    prodMap[item.project_name].total += item.co2_kg
    prodMap[item.project_name].taskTypes[item.task_type_name] = item.co2_kg
  })
  return Object.values(prodMap).sort((a, b) => b.total - a.total)
})

const weeklyAverage = computed(() => {
  const prods = store.openProductions
  if (prods.length === 0) return 0
  let oldest = null
  let latest = null
  prods.forEach((p) => {
    if (p.start_date) {
      const d = new Date(p.start_date)
      if (!oldest || d < oldest) oldest = d
    }
    if (p.end_date) {
      const d = new Date(p.end_date)
      if (!latest || d > latest) latest = d
    }
  })
  if (!oldest) return 0
  if (!latest) latest = new Date()
  const ms = latest - oldest
  const weeks = Math.max(ms / (7 * 24 * 60 * 60 * 1000), 1)
  return data.value.total_co2_kg / weeks
})

const maxEmission = computed(() => {
  if (productions.value.length === 0) return 1
  return Math.max(...productions.value.map((p) => p.total))
})

const getTaskTypeTotal = (taskTypeName) => {
  const byTT = data.value.by_task_type || {}
  return byTT[taskTypeName]?.co2_kg || 0
}

const getProductionTaskType = (prodName, taskTypeName) => {
  const prod = productions.value.find((p) => p.name === prodName)
  return prod?.taskTypes[taskTypeName] || 0
}

const fetchData = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await fetch('/api/plugins/carbon/footprint')
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    data.value = await response.json()
  } catch (err) {
    error.value = `Failed to load data: ${err.message}`
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
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

.breakdown-table tbody tr:nth-child(odd) {
  background: #46494f;
}

.breakdown-table tbody tr:nth-child(even) {
  background: #36393f;
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
