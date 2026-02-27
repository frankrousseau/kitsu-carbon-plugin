import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useMainStore } from '../stores/main'

export const useCarbon = () => {
  const store = useMainStore()

  const unit = ref(localStorage.getItem('carbon-unit') || 'kg')
  const activeTab = ref(localStorage.getItem('carbon-tab') || 'matrix')
  const showInfo = ref(false)

  watch(unit, (v) => localStorage.setItem('carbon-unit', v))
  watch(activeTab, (v) => localStorage.setItem('carbon-tab', v))

  const onKeydown = (e) => {
    if (e.key === 'Escape') showInfo.value = false
  }

  onMounted(() => window.addEventListener('keydown', onKeydown))
  onUnmounted(() => window.removeEventListener('keydown', onKeydown))

  const formatValue = (kg) => {
    if (unit.value === 't') {
      return (kg / 1000).toFixed(2)
    }
    if (kg >= 1000) {
      return Math.round(kg).toLocaleString()
    }
    if (kg >= 1) {
      return kg.toFixed(1)
    }
    return kg.toFixed(2)
  }

  const formatValueOrDash = (kg) => {
    if (kg === 0) return '-'
    return formatValue(kg)
  }

  const formatNumber = (num) => Math.round(num).toLocaleString()

  const getImpactClass = (kg, maxEmission) => {
    if (kg === null || kg === undefined || kg === 0) return ''
    if (maxEmission === 0) return 'low'
    const ratio = kg / maxEmission
    if (ratio >= 0.66) return 'high'
    if (ratio >= 0.33) return 'medium'
    return 'low'
  }

  const getBarWidth = (kg, maxEmission) => (kg / maxEmission) * 100

  const getPercent = (kg, totalCo2Kg) => {
    if (totalCo2Kg === 0) return '0.0'
    return ((kg / totalCo2Kg) * 100).toFixed(1)
  }

  const unitLabel = computed(() => (unit.value === 'kg' ? 'kgCO2e' : 'tCO2e'))

  const getTaskTypeColor = (taskTypeName) => {
    const tt = store.taskTypes.find(
      (t) =>
        t.name === taskTypeName ||
        t.name.toLowerCase() === taskTypeName.toLowerCase()
    )
    return tt?.color || null
  }

  const taskTypeHeaderStyle = (taskTypeName) => {
    const color = getTaskTypeColor(taskTypeName)
    if (!color) return {}
    return {
      borderLeft: `2px solid ${color}30`,
      background: `${color}10`,
      textAlign: 'center'
    }
  }

  const taskTypeCellStyle = (taskTypeName) => {
    const color = getTaskTypeColor(taskTypeName)
    if (!color) return {}
    return {
      borderLeft: `2px solid ${color}30`,
      borderRight: `1px solid ${color}30`,
      background: `${color}08`
    }
  }

  const weeklyChangeClass = (data) => {
    const pct = data.weekly_change_percent || 0
    if (pct > 0) return 'change-up'
    if (pct < 0) return 'change-down'
    return 'change-neutral'
  }

  const weeklyChangeLabel = (data) => {
    const pct = data.weekly_change_percent || 0
    if (pct > 0) return `+${pct}%`
    if (pct < 0) return `${pct}%`
    return '0%'
  }

  return {
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
    getTaskTypeColor,
    taskTypeHeaderStyle,
    taskTypeCellStyle,
    weeklyChangeClass,
    weeklyChangeLabel
  }
}
