<template>
  <div class="app">
    <AppSidebar />

    <div class="content-column">
      <header class="topbar">
        <button
          type="button"
          class="menu-button"
          :aria-label="t('nav.openMenu')"
          @click="openMobile"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <div class="topbar-actions">
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </header>
      <!-- Restocking is budget-driven and ignores the shared filters, so hide the bar there -->
      <FilterBar v-if="$route.path !== '/restocking'" />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import AppSidebar from './components/AppSidebar.vue'
import { useSidebar } from './composables/useSidebar'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    AppSidebar
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const { openMobile } = useSidebar()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      openMobile,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>


<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  font-size: var(--text-base);
  background: var(--canvas);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Visible keyboard focus for every interactive element */
:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

/* Shell: sidebar | content. The content column owns the scroll. */
.app {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  height: 100vh;
  overflow: hidden;
}

.content-column {
  min-width: 0;
  height: 100vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: var(--z-topbar);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  height: var(--topbar-h);
  padding: 0 var(--content-pad);
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-left: auto;
}

.menu-button {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--line);
  border-radius: var(--radius-control);
  background: var(--surface);
  color: var(--text-soft);
  cursor: pointer;
}

.menu-button:hover {
  background: var(--canvas);
  border-color: var(--line-strong);
}

@media (prefers-reduced-motion: no-preference) {
  .menu-button {
    transition: background-color 0.15s ease, border-color 0.15s ease;
  }
}

/* Tablet: the sidebar is a docked 72px rail; the overlay never changes this column */
@media (min-width: 640px) and (max-width: 1023px) {
  .app {
    grid-template-columns: var(--sidebar-w-collapsed) minmax(0, 1fr);
  }
}

/* Phone: off-canvas drawer opened from the top bar */
@media (max-width: 639px) {
  .app {
    grid-template-columns: minmax(0, 1fr);
  }

  .menu-button {
    display: inline-flex;
  }
}

.main-content {
  flex: 1;
  max-width: var(--content-max);
  width: 100%;
  margin: 0 auto;
  padding: var(--space-5) var(--content-pad);
}

/* ---- Page header ---- */
.page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.page-header h2 {
  font-size: var(--text-xl);
  font-weight: 700;
  line-height: 1.2;
  color: var(--ink);
  margin-bottom: var(--space-1);
  letter-spacing: -0.02em;
}

.page-header p {
  color: var(--muted);
  font-size: var(--text-base);
}

/* ---- Stat cards ---- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.stat-card {
  background: var(--surface);
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-card);
  border: 1px solid var(--line);
}

@media (prefers-reduced-motion: no-preference) {
  .stat-card {
    transition: border-color 0.15s ease;
  }
}

.stat-card:hover {
  border-color: var(--line-strong);
}

.stat-label {
  color: var(--muted);
  font-size: var(--text-sm);
  font-weight: 500;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: 700;
  line-height: 1.2;
  color: var(--ink);
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.stat-card.warning .stat-value {
  color: var(--warning);
}

.stat-card.success .stat-value {
  color: var(--success);
}

.stat-card.danger .stat-value {
  color: var(--danger);
}

.stat-card.info .stat-value {
  color: var(--primary);
}

/* ---- Cards ---- */
.card {
  background: var(--surface);
  border-radius: var(--radius-card);
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--line);
  margin-bottom: var(--space-5);
}

/* Negative margins let the header divider span the full card width */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: calc(var(--space-4) * -1) calc(var(--space-5) * -1) var(--space-4);
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--line);
}

.card-title {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -0.01em;
}

/* ---- Tables ---- */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
}

thead {
  background: var(--canvas);
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

th {
  text-align: left;
  height: 40px;
  padding: var(--space-2) var(--space-3);
  font-weight: 500;
  color: var(--muted);
  font-size: var(--text-sm);
}

td {
  height: 44px;
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--hover);
  color: var(--text-soft);
  font-size: var(--text-base);
}

@media (prefers-reduced-motion: no-preference) {
  tbody tr {
    transition: background-color 0.15s ease;
  }
}

tbody tr:hover {
  background: var(--canvas);
}

/* ---- Badges ---- */
.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-badge);
  font-size: var(--text-xs);
  font-weight: 600;
  line-height: 1.4;
}

.badge.success,
.badge.increasing {
  background: var(--success-bg);
  color: var(--success-fg);
}

.badge.warning,
.badge.medium {
  background: var(--warning-bg);
  color: var(--warning-fg);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--danger-bg);
  color: var(--danger-fg);
}

.badge.info,
.badge.low {
  background: var(--info-bg);
  color: var(--info-fg);
}

.badge.stable {
  background: var(--stable-bg);
  color: var(--stable-fg);
}

/* ---- States ---- */
.loading {
  text-align: center;
  padding: var(--space-7);
  color: var(--muted);
  font-size: var(--text-base);
}

.error {
  background: var(--danger-soft);
  border: 1px solid var(--danger-bg);
  color: var(--danger-fg);
  padding: var(--space-4);
  border-radius: var(--radius-control);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}
</style>
