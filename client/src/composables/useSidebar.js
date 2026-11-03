import { ref, getCurrentInstance, onMounted, onBeforeUnmount } from 'vue'

const STORAGE_KEY = 'sidebar-collapsed'

// Tablet tier: the sidebar is a permanent icon rail that expands as an overlay
const TABLET_QUERY = '(min-width: 640px) and (max-width: 1023px)'
// Tier boundaries; crossing any of them resets transient open states
const TIER_QUERIES = [TABLET_QUERY, '(min-width: 1024px)']

// localStorage can throw (private mode, blocked storage); fall back to defaults
const readCollapsed = () => {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'true'
  } catch (err) {
    return false
  }
}

// Module-level so every consumer shares one state
const collapsed = ref(readCollapsed()) // desktop preference, persisted
const mobileOpen = ref(false) // phone drawer
const railExpanded = ref(false) // tablet overlay, session-only
const isTablet = ref(
  typeof window !== 'undefined' && !!window.matchMedia && window.matchMedia(TABLET_QUERY).matches
)

let lists = []
let consumers = 0

// A breakpoint change must never leave a stale overlay, backdrop or drawer
const onTierChange = () => {
  isTablet.value = window.matchMedia(TABLET_QUERY).matches
  railExpanded.value = false
  mobileOpen.value = false
}

// One shared set of listeners, ref-counted so they are removed with the last consumer
const attach = () => {
  if (consumers++ > 0 || typeof window === 'undefined' || !window.matchMedia) return
  isTablet.value = window.matchMedia(TABLET_QUERY).matches
  lists = TIER_QUERIES.map((q) => {
    const mql = window.matchMedia(q)
    mql.addEventListener('change', onTierChange)
    return mql
  })
}

const detach = () => {
  if (--consumers > 0) return
  consumers = 0
  lists.forEach((mql) => mql.removeEventListener('change', onTierChange))
  lists = []
}

export function useSidebar() {
  if (getCurrentInstance()) {
    onMounted(attach)
    onBeforeUnmount(detach)
  }

  const toggleCollapsed = () => {
    collapsed.value = !collapsed.value
    try {
      localStorage.setItem(STORAGE_KEY, String(collapsed.value))
    } catch (err) {
      // Persistence is best effort
    }
  }

  const toggleRail = () => {
    railExpanded.value = !railExpanded.value
  }

  const closeRail = () => {
    railExpanded.value = false
  }

  const openMobile = () => {
    mobileOpen.value = true
  }

  const closeMobile = () => {
    mobileOpen.value = false
  }

  return {
    collapsed,
    mobileOpen,
    railExpanded,
    isTablet,
    toggleCollapsed,
    toggleRail,
    closeRail,
    openMobile,
    closeMobile
  }
}
