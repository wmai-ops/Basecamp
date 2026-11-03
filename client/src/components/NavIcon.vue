<template>
  <svg
    class="nav-icon"
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.75"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path v-for="(d, i) in paths" :key="`${name}-${i}`" :d="d" />
  </svg>
</template>

<script>
import { computed } from 'vue'

// Each icon is a list of path strings on a 24x24 grid
const ICONS = {
  dashboard: ['M3 3h7v9H3z', 'M14 3h7v5h-7z', 'M14 12h7v9h-7z', 'M3 16h7v5H3z'],
  inventory: ['M21 8l-9-5-9 5 9 5 9-5z', 'M3 8v8l9 5 9-5V8', 'M12 13v8'],
  orders: ['M6 2h12v20l-3-2-3 2-3-2-3 2z', 'M9 7h6', 'M9 11h6', 'M9 15h4'],
  finance: ['M3 6h18v12H3z', 'M3 10h18', 'M7 15h3'],
  demand: ['M3 17l6-6 4 4 8-8', 'M15 7h6v6'],
  restocking: ['M21 12a9 9 0 0 1-15.5 6.2', 'M3 12A9 9 0 0 1 18.5 5.8', 'M18 2v4h-4', 'M6 22v-4h4'],
  reports: ['M4 20V10', 'M10 20V4', 'M16 20v-7', 'M22 20H2'],
  fallback: ['M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z']
}

export default {
  name: 'NavIcon',
  props: {
    name: { type: String, required: true }
  },
  setup(props) {
    const paths = computed(() => ICONS[props.name] || ICONS.fallback)
    return { paths }
  }
}
</script>

<style scoped>
.nav-icon {
  flex-shrink: 0;
}
</style>
