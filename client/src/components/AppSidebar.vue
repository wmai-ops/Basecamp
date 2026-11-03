<template>
  <div class="sidebar-shell">
    <!-- Backdrop only exists for the mobile drawer -->
    <div
      v-if="mobileOpen || (isTablet && railExpanded)"
      class="sidebar-backdrop"
      aria-hidden="true"
      @click="closeAll"
    ></div>

    <aside
      :class="['sidebar', { 'is-collapsed': collapsed, 'is-open': mobileOpen, 'is-rail-open': isTablet && railExpanded }]"
    >
      <div class="brand">
        <svg class="brand-mark" width="32" height="32" viewBox="0 0 32 32" aria-hidden="true" focusable="false">
          <rect width="32" height="32" rx="8" fill="currentColor" />
          <path d="M9 12l7-4 7 4v8l-7 4-7-4z" fill="none" stroke="#ffffff" stroke-width="1.75" stroke-linejoin="round" />
          <path d="M9 12l7 4 7-4M16 16v8" fill="none" stroke="#ffffff" stroke-width="1.75" stroke-linejoin="round" />
        </svg>
        <div class="brand-text">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
        <button
          type="button"
          class="drawer-close"
          :aria-label="t('nav.closeMenu')"
          @click="closeMobile"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>
      </div>

      <nav :aria-label="t('nav.mainNavigation')" class="nav">
        <ul class="nav-list">
          <li v-for="item in items" :key="item.to">
            <router-link
              :to="item.to"
              class="nav-item"
              :aria-label="t(item.labelKey)"
              :title="railMode ? t(item.labelKey) : null"
            >
              <NavIcon :name="item.icon" />
              <span class="nav-label">{{ t(item.labelKey) }}</span>
            </router-link>
          </li>
        </ul>
      </nav>

      <button
        ref="toggleEl"
        type="button"
        class="collapse-toggle"
        :aria-expanded="String(!railMode)"
        :aria-label="railMode ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
        :title="railMode ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
        @click="onToggle"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <rect x="3" y="4" width="18" height="16" rx="2" />
          <path d="M9 4v16" />
          <path :d="railMode ? 'M14 9l3 3-3 3' : 'M17 9l-3 3 3 3'" />
        </svg>
        <span class="nav-label">{{ railMode ? t('nav.expandSidebar') : t('nav.collapseSidebar') }}</span>
      </button>
    </aside>
  </div>
</template>

<script>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import { useSidebar } from '../composables/useSidebar'
import { navItems } from '../config/navigation'
import NavIcon from './NavIcon.vue'

export default {
  name: 'AppSidebar',
  components: { NavIcon },
  setup() {
    const { t } = useI18n()
    const route = useRoute()
    const {
      collapsed, mobileOpen, railExpanded, isTablet,
      toggleCollapsed, toggleRail, closeRail, closeMobile
    } = useSidebar()
    const toggleEl = ref(null)

    // True when the sidebar shows icons only: collapsed on desktop, closed rail on tablet.
    // Phone drawer always shows labels (its toggle is hidden), so the value is moot there.
    const railMode = computed(() => (isTablet.value ? !railExpanded.value : collapsed.value))

    const onToggle = () => (isTablet.value ? toggleRail() : toggleCollapsed())

    const closeAll = () => {
      closeMobile()
      closeRail()
    }

    // Overlay and drawer close after navigating
    watch(() => route.fullPath, closeAll)

    // Return focus to the toggle when the tablet overlay closes. Skipped when the
    // close came from leaving the tablet tier (resize), which must not steal focus.
    watch(railExpanded, (open, wasOpen) => {
      if (wasOpen && !open && isTablet.value) {
        nextTick(() => toggleEl.value && toggleEl.value.focus())
      }
    })

    const onKeydown = (event) => {
      if (event.key === 'Escape' && (mobileOpen.value || railExpanded.value)) {
        closeAll()
      }
    }

    onMounted(() => document.addEventListener('keydown', onKeydown))
    onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))

    return {
      t,
      items: navItems,
      collapsed,
      mobileOpen,
      railExpanded,
      isTablet,
      railMode,
      toggleEl,
      onToggle,
      closeAll,
      closeMobile
    }
  }
}
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  width: var(--sidebar-w);
  height: 100vh;
  background: var(--surface);
  border-right: 1px solid var(--line);
  padding: var(--space-4) var(--space-3);
  overflow-y: auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-1) var(--space-2) var(--space-4);
  min-height: var(--topbar-h);
}

.brand-mark {
  flex-shrink: 0;
  color: var(--primary);
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.brand-name {
  font-size: var(--text-md);
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-subtitle {
  font-size: var(--text-xs);
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav {
  flex: 1;
}

.nav-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-item,
.collapse-toggle {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  height: 40px;
  padding: 0 var(--space-3);
  border: none;
  border-radius: var(--radius-control);
  background: transparent;
  color: var(--muted);
  font-family: inherit;
  font-size: var(--text-base);
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  text-align: left;
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-item:hover,
.collapse-toggle:hover {
  background: var(--hover);
  color: var(--ink);
}

/* Root route matches every path by prefix, so only its exact match counts */
.nav-item.router-link-exact-active,
.nav-item.router-link-active:not([href='/']) {
  background: var(--primary-soft);
  color: var(--primary);
}

.nav-item.router-link-exact-active::before,
.nav-item.router-link-active:not([href='/'])::before {
  content: '';
  position: absolute;
  left: calc(var(--space-3) * -1);
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--primary);
}

.nav-item:focus-visible,
.collapse-toggle:focus-visible,
.drawer-close:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

.drawer-close {
  display: none;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-control);
  background: transparent;
  color: var(--muted);
  cursor: pointer;
}

.drawer-close:hover {
  background: var(--hover);
  color: var(--ink);
}

.sidebar-backdrop {
  display: none;
}

@media (prefers-reduced-motion: no-preference) {
  .sidebar {
    transition: width 0.18s ease;
  }

  .nav-item,
  .collapse-toggle,
  .drawer-close {
    transition: background-color 0.15s ease, color 0.15s ease;
  }
}

/* Desktop: in-flow, collapsible to an icon rail */
@media (min-width: 1024px) {
  .sidebar {
    position: sticky;
    top: 0;
  }

  .sidebar.is-collapsed {
    width: var(--sidebar-w-collapsed);
  }

  .sidebar.is-collapsed .brand {
    justify-content: center;
    padding-left: 0;
    padding-right: 0;
  }

  .sidebar.is-collapsed .brand-text,
  .sidebar.is-collapsed .nav-label {
    display: none;
  }

  .sidebar.is-collapsed .nav-item,
  .sidebar.is-collapsed .collapse-toggle {
    justify-content: center;
    padding: 0;
  }
}

/* Tablet: permanent 72px icon rail. The shell reserves the grid column; the sidebar
   itself is absolute so expanding it overlays the content instead of reflowing it. */
@media (min-width: 640px) and (max-width: 1023px) {
  .sidebar-shell {
    position: relative;
    width: var(--sidebar-w-collapsed);
    height: 100vh;
  }

  .sidebar {
    position: absolute;
    top: 0;
    left: 0;
    z-index: var(--z-sidebar);
    width: var(--sidebar-w-collapsed);
  }

  .sidebar.is-rail-open {
    width: var(--sidebar-w);
    box-shadow: var(--shadow-float);
  }

  .sidebar:not(.is-rail-open) .brand {
    justify-content: center;
    padding-left: 0;
    padding-right: 0;
  }

  .sidebar:not(.is-rail-open) .brand-text,
  .sidebar:not(.is-rail-open) .nav-label {
    display: none;
  }

  .sidebar:not(.is-rail-open) .nav-item,
  .sidebar:not(.is-rail-open) .collapse-toggle {
    justify-content: center;
    padding: 0;
  }

  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: var(--z-backdrop);
    background: rgba(15, 23, 42, 0.4);
  }
}

/* Phone: off-canvas drawer, collapsed state is ignored */
@media (max-width: 639px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    z-index: var(--z-sidebar);
    max-width: 85vw;
    box-shadow: var(--shadow-float);
    visibility: hidden;
    transform: translateX(-100%);
  }

  .sidebar.is-open {
    visibility: visible;
    transform: none;
  }

  .collapse-toggle {
    display: none;
  }

  .drawer-close {
    display: inline-flex;
  }

  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: var(--z-backdrop);
    background: rgba(15, 23, 42, 0.4);
  }
}
</style>
