<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <div class="budget-slider-row">
        <label class="budget-label" for="budget-slider">{{ t('restocking.budgetLabel') }}</label>
        <span class="budget-value">{{ currencySymbol }}{{ Math.round(budget).toLocaleString() }}</span>
      </div>
      <input
        id="budget-slider"
        type="range"
        min="0"
        :max="maxBudget"
        step="50"
        v-model.number="budget"
        @input="loadRecommendations()"
        class="budget-slider"
      />

      <div v-if="recommendations" class="budget-summary">
        <div class="budget-summary-item">
          <span class="budget-summary-label">{{ t('restocking.totalCost') }}</span>
          <span class="budget-summary-value">{{ currencySymbol }}{{ recommendations.total_cost.toLocaleString() }}</span>
        </div>
        <div class="budget-summary-item">
          <span class="budget-summary-label">{{ t('restocking.remainingBudget') }}</span>
          <span class="budget-summary-value">{{ currencySymbol }}{{ recommendations.remaining_budget.toLocaleString() }}</span>
        </div>
      </div>
    </div>

    <div v-if="orderResult" class="success-banner">
      {{ t('restocking.orderSuccess', { orderNumber: orderResult.order_number }) }}
    </div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ recommendations?.items?.length || 0 }})</h3>
        <button
          class="place-order-btn"
          :disabled="!recommendations?.items?.length || submitting"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
        </button>
      </div>

      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="!recommendations?.items?.length" class="no-recommendations">
        {{ t('restocking.noRecommendations') }}
      </div>
      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th>{{ t('restocking.table.sku') }}</th>
              <th>{{ t('restocking.table.itemName') }}</th>
              <th>{{ t('restocking.table.trend') }}</th>
              <th>{{ t('restocking.table.recommendedQty') }}</th>
              <th>{{ t('restocking.table.quantity') }}</th>
              <th>{{ t('restocking.table.unitCost') }}</th>
              <th>{{ t('restocking.table.lineCost') }}</th>
              <th>{{ t('restocking.table.leadTime') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in recommendations.items" :key="item.item_sku">
              <td><strong>{{ item.item_sku }}</strong></td>
              <td>{{ item.item_name }}</td>
              <td>
                <span :class="['badge', item.trend]">
                  {{ t(`trends.${item.trend}`) }}
                </span>
              </td>
              <td>{{ item.recommended_qty }}</td>
              <td>
                {{ item.quantity }}
                <span v-if="item.is_partial" class="badge partial-badge">{{ t('restocking.partial') }}</span>
              </td>
              <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
              <td><strong>{{ currencySymbol }}{{ item.line_cost.toLocaleString() }}</strong></td>
              <td>{{ item.lead_time_days }} {{ t('common.days') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { onMounted, computed } from 'vue'
import { useRestocking } from '../composables/useRestocking'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const {
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
    } = useRestocking()

    onMounted(() => initialize())

    return {
      t,
      currencySymbol,
      budget,
      maxBudget,
      recommendations,
      loading,
      submitting,
      error,
      orderResult,
      loadRecommendations,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.budget-slider-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-runnable-track {
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  margin-top: -6px;
  cursor: pointer;
  transition: transform 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: transform 0.15s ease;
}

.budget-slider::-moz-range-thumb:hover {
  transform: scale(1.1);
}

.budget-slider:focus::-webkit-slider-thumb {
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
}

.budget-summary {
  display: flex;
  gap: 2rem;
  margin-top: 0.5rem;
}

.budget-summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.budget-summary-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-summary-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.card-header {
  gap: 1rem;
}

.place-order-btn {
  padding: 0.625rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: transform 0.2s ease, opacity 0.2s ease;
  white-space: nowrap;
}

.place-order-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
  font-weight: 500;
}

.no-recommendations {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

.partial-badge {
  margin-left: 0.5rem;
  background: #fed7aa;
  color: #92400e;
  padding: 0.15rem 0.5rem;
  font-size: 0.625rem;
}
</style>
