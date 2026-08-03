import { ref } from 'vue'
import { api } from '../api'

// Factory function (not a singleton) - budget/recommendations are single-view state
export function useRestocking() {
  const budget = ref(0)
  const maxBudget = ref(1000)
  const recommendations = ref(null)
  const loading = ref(true)
  const submitting = ref(false)
  const error = ref(null)
  const orderResult = ref(null)

  let debounceTimer = null

  const fetchRecommendations = async () => {
    try {
      loading.value = true
      error.value = null
      recommendations.value = await api.getRestockingRecommendations(budget.value)
    } catch (err) {
      error.value = 'Failed to load recommendations: ' + err.message
    } finally {
      loading.value = false
    }
  }

  const loadRecommendations = ({ immediate = false } = {}) => {
    clearTimeout(debounceTimer)
    if (immediate) {
      return fetchRecommendations()
    }
    debounceTimer = setTimeout(fetchRecommendations, 300)
  }

  const placeOrder = async () => {
    if (!recommendations.value?.items?.length) return

    try {
      submitting.value = true
      error.value = null
      orderResult.value = null

      const order = await api.submitRestockOrder({
        budget: budget.value,
        items: recommendations.value.items.map(item => ({
          item_sku: item.item_sku,
          quantity: item.quantity
        }))
      })

      orderResult.value = order
    } catch (err) {
      error.value = 'Failed to submit order: ' + err.message
    } finally {
      submitting.value = false
    }
  }

  const initialize = async () => {
    loading.value = true
    error.value = null

    try {
      // Compute max useful budget from lightweight demand data instead of an
      // initial (and previously discarded) recommendations fetch - avoids
      // calling fetchRecommendations() twice on every mount.
      const forecasts = await api.getDemandForecasts()
      const maxUsefulBudget = forecasts.reduce((sum, forecast) => {
        const gap = Math.max(0, forecast.forecasted_demand - forecast.current_demand)
        return sum + gap * forecast.unit_cost
      }, 0)

      maxBudget.value = Math.max(Math.round(maxUsefulBudget * 100) / 100, 1)
      budget.value = Math.round(maxBudget.value / 2)
    } catch (err) {
      error.value = 'Failed to load recommendations: ' + err.message
      loading.value = false
      return
    }

    await fetchRecommendations()
  }

  return {
    budget,
    maxBudget,
    recommendations,
    loading,
    submitting,
    error,
    orderResult,
    loadRecommendations,
    placeOrder,
    initialize
  }
}
