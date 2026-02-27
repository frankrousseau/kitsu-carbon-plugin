import { createRouter, createWebHashHistory } from 'vue-router'
import CarbonFootprint from './components/CarbonFootprint.vue'

const routes = [
  {
    path: '/',
    name: 'carbon',
    component: CarbonFootprint
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// Transfer real URL query params (set by Kitsu) into the hash-based route
// so Vue Router can access them and preserve them during navigation.
let queryTransferred = false
router.beforeEach((to, from, next) => {
  if (!queryTransferred) {
    queryTransferred = true
    const realParams = new URLSearchParams(window.location.search)
    if (realParams.toString()) {
      const query = {}
      realParams.forEach((value, key) => {
        query[key] = value
      })
      next({ path: to.path, query })
      return
    }
  }
  next()
})

export default router
