<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <!-- Budget slider -->
    <div class="card">
      <div class="budget-row">
        <label for="budget-slider" class="budget-label">{{ t('restocking.budgetLabel') }}</label>
        <span class="budget-value">{{ formatMoney(budget) }}</span>
      </div>
      <input
        id="budget-slider"
        v-model.number="budget"
        type="range"
        min="0"
        max="100000"
        step="1000"
        class="budget-slider"
      />
      <div class="budget-scale">
        <span>{{ formatMoney(0) }}</span>
        <span>{{ formatMoney(100000) }}</span>
      </div>
    </div>

    <div v-if="loading && !result" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="result">
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.summary.totalCost') }}</div>
          <div class="stat-value">{{ formatMoney(result.total_cost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.summary.remainingBudget') }}</div>
          <div class="stat-value">{{ formatMoney(result.remaining_budget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.itemCount') }}</div>
          <div class="stat-value">{{ items.length }}</div>
        </div>
      </div>

      <!-- Order result / failure messages -->
      <div v-if="orderError" class="error">{{ orderError }}</div>
      <div v-if="placedOrder" class="confirmation">
        <strong>{{ t('restocking.orderSuccess') }}</strong>
        <div class="confirmation-details">
          <span>{{ t('restocking.orderNumber') }}: <strong>{{ placedOrder.order_number }}</strong></span>
          <span>{{ t('restocking.expectedDelivery') }}: <strong>{{ formatDate(placedOrder.expected_delivery) }}</strong></span>
          <span>{{ t('restocking.leadTime') }}: <strong>{{ formatDays(placedOrder.lead_time_days) }}</strong></span>
        </div>
        <router-link to="/orders" class="confirmation-link">{{ t('restocking.viewOrders') }}</router-link>
      </div>

      <div class="card" :class="{ refreshing: loading }">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ items.length }})</h3>
          <button
            type="button"
            class="place-order-btn"
            :disabled="!canPlaceOrder"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="items.length === 0" class="empty-state">{{ t('restocking.empty') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.onHand') }}</th>
                <th class="num">{{ t('restocking.table.forecastedDemand') }}</th>
                <th class="num">{{ t('restocking.table.shortfall') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.sku">
                <td>
                  <strong>{{ translateProductName(item.name) }}</strong>
                  <div class="sku">{{ item.sku }}</div>
                </td>
                <td>{{ item.category }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td class="num">{{ item.quantity_on_hand.toLocaleString() }}</td>
                <td class="num">{{ item.forecasted_demand.toLocaleString() }}</td>
                <td class="num">{{ item.shortfall.toLocaleString() }}</td>
                <td class="num"><strong>{{ item.quantity.toLocaleString() }}</strong></td>
                <td class="num">{{ formatMoney(item.unit_cost, 2) }}</td>
                <td class="num"><strong>{{ formatMoney(item.line_total, 2) }}</strong></td>
                <td class="num">{{ formatDays(item.lead_time_days) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const DEBOUNCE_MS = 300

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const budget = ref(20000)
    const result = ref(null)
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const orderError = ref(null)
    const placedOrder = ref(null)

    const items = computed(() => (result.value ? result.value.items : []))

    // Order is only valid when the displayed items match the current slider value
    const canPlaceOrder = computed(() =>
      items.value.length > 0 && !submitting.value && !loading.value
    )

    // Backend amounts are USD; formatCurrency converts to JPY for the ja locale
    const formatMoney = (amount, decimals = 0) => {
      return decimals > 0
        ? formatCurrencyWithDecimals(amount, currentCurrency.value, decimals)
        : formatCurrency(amount, currentCurrency.value)
    }

    const formatDays = (count) => {
      return t(count === 1 ? 'common.dayCount' : 'common.daysCount', { count })
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' })
    }

    // Monotonic request id: only the latest request may write results,
    // so a slow earlier response cannot overwrite a newer one.
    let requestId = 0

    const loadRecommendations = async () => {
      const myId = ++requestId
      loading.value = true
      error.value = null
      try {
        const data = await api.getRestockRecommendations(budget.value)
        if (myId !== requestId) return // stale response
        result.value = data
      } catch (err) {
        if (myId !== requestId) return
        error.value = t('restocking.loadError') + ': ' + err.message
        result.value = null
      } finally {
        if (myId === requestId) loading.value = false
      }
    }

    // Debounce slider changes so dragging does not fire a request per step
    let debounceTimer = null
    watch(budget, () => {
      placedOrder.value = null
      orderError.value = null
      // Mark loading immediately so Place Order cannot use stale items
      loading.value = true
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, DEBOUNCE_MS)
    })

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return // guards double submit
      submitting.value = true
      orderError.value = null
      placedOrder.value = null
      try {
        placedOrder.value = await api.createRestockOrder({
          budget: budget.value,
          items: items.value.map(i => ({ sku: i.sku, quantity: i.quantity }))
        })
      } catch (err) {
        // Prefer the backend's detail message (e.g. over budget / unknown SKU)
        const detail = err.response && err.response.data && err.response.data.detail
        orderError.value = typeof detail === 'string'
          ? detail
          : t('restocking.orderError') + ': ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)
    onBeforeUnmount(() => {
      clearTimeout(debounceTimer)
      requestId++ // invalidate any in-flight request
    })

    return {
      t,
      budget,
      result,
      items,
      loading,
      error,
      submitting,
      orderError,
      placedOrder,
      canPlaceOrder,
      formatMoney,
      formatDays,
      formatDate,
      placeOrder,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.75rem;
}

.budget-label {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.budget-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #0f172a;
  border: 2px solid white;
  box-shadow: 0 0 0 1px #64748b;
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #0f172a;
  border: 2px solid white;
  box-shadow: 0 0 0 1px #64748b;
}

.budget-slider:focus-visible::-webkit-slider-thumb {
  box-shadow: 0 0 0 3px #cbd5e1;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #64748b;
}

.num {
  text-align: right;
}

.sku {
  font-size: 0.75rem;
  color: #64748b;
}

/* Dim the table while a newer recommendation is being fetched */
.refreshing {
  opacity: 0.6;
  transition: opacity 0.15s ease;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1e293b;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  color: #64748b;
  cursor: not-allowed;
}

.confirmation {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}

.confirmation-details {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.5rem;
  margin: 0.5rem 0;
}

.confirmation-link {
  color: #2563eb;
  font-weight: 500;
  text-decoration: none;
}

.confirmation-link:hover {
  text-decoration: underline;
}
</style>
