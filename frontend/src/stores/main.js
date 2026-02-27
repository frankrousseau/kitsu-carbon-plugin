import { defineStore } from 'pinia'

export const useMainStore = defineStore('main', {
  state: () => ({
    taskTypes: [],
    openProductions: [],
    sequences: [],
    episodes: [],
    assetTypes: []
  }),

  actions: {
    async fetchTaskTypes() {
      try {
        const response = await fetch('/api/data/task-types')
        if (response.ok) {
          this.taskTypes = await response.json()
        }
      } catch (err) {
        console.error('Failed to fetch task types:', err)
      }
    },

    async fetchOpenProductions() {
      try {
        const response = await fetch('/api/data/projects/open')
        if (response.ok) {
          this.openProductions = await response.json()
        }
      } catch (err) {
        console.error('Failed to fetch open productions:', err)
      }
    },

    async fetchSequences(productionId) {
      try {
        const response = await fetch(
          `/api/data/projects/${productionId}/sequences`
        )
        if (response.ok) {
          this.sequences = await response.json()
        }
      } catch (err) {
        console.error('Failed to fetch sequences:', err)
      }
    },

    async fetchEpisodes(productionId) {
      try {
        const response = await fetch(
          `/api/data/projects/${productionId}/episodes`
        )
        if (response.ok) {
          this.episodes = await response.json()
        }
      } catch (err) {
        console.error('Failed to fetch episodes:', err)
      }
    },

    async fetchAssetTypes(productionId) {
      try {
        const response = await fetch(
          `/api/data/projects/${productionId}/asset-types`
        )
        if (response.ok) {
          this.assetTypes = await response.json()
        }
      } catch (err) {
        console.error('Failed to fetch asset types:', err)
      }
    },

    async init() {
      try {
        await Promise.all([this.fetchTaskTypes(), this.fetchOpenProductions()])
      } catch (err) {
        console.error('Failed to initialize store:', err)
      }
    },

    async setCurrentProduction(productionId) {
      if (!productionId) {
        this.sequences = []
        this.episodes = []
        this.assetTypes = []
        return
      }

      const production = this.openProductions.find((p) => p.id === productionId)
      if (!production) {
        console.warn(`Production ${productionId} not found in open productions`)
        this.sequences = []
        this.episodes = []
        this.assetTypes = []
        return
      }

      const isTVShow = production.production_type === 'tvshow'

      if (isTVShow) {
        this.sequences = []
        await Promise.all([
          this.fetchEpisodes(productionId),
          this.fetchAssetTypes(productionId)
        ])
      } else {
        this.episodes = []
        await Promise.all([
          this.fetchSequences(productionId),
          this.fetchAssetTypes(productionId)
        ])
      }
    }
  }
})
