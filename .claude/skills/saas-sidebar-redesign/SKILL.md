---
name: saas-sidebar-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface - a collapsible vertical navigation sidebar on the left instead of a top nav bar, a consistent spacing/type scale built on design tokens, and a polished professional look. Use this skill whenever the user wants to move navigation from a top bar to a left sidebar, make a Vue app look like a modern SaaS dashboard or admin panel, modernize or "professionalize" a Vue UI, introduce consistent spacing or design tokens, or restyle App.vue / the app shell, even if they never say "sidebar" or "SaaS".
---

# SaaS Sidebar Redesign for Vue 3

Turn a Vue 3 app with a top navigation bar into a SaaS-style shell: left sidebar, slim top bar, token-driven spacing and typography, consistent cards/tables/badges. The work is mostly CSS and layout; the app's behavior must not change.

The point of the redesign is consistency. A sidebar alone looks like a patch if the pages inside it still use ten different paddings. So the job has two halves: build the new shell, then bring the shared surface (cards, tables, headers, spacing) onto one scale.

## Ground rules

- **Do not change behavior.** Routes, API calls, stores, i18n keys, props and emitted events stay as they are. Only markup structure and styling move. If a change would alter behavior, stop and ask.
- **Keep the brand.** Reuse the app's existing primary color, neutrals and fonts as the token values. The goal is a more polished version of this app, not a different product.
- **No new dependencies without asking.** Icons are inline SVG (see `references/sidebar-implementation.md`). If the project pins a registry or restricts packages, a new package is a decision for the user.
- **Follow the project's own rules first.** Read CLAUDE.md or contribution docs before editing. Some projects require delegating `.vue` work to a specific agent, ban emojis in UI, or require tests; those rules beat anything here.
- **Match the project's component style** (Options API with `setup()`, or `<script setup>`). The skeletons in the references use `<script setup>`; convert them if the project does not.
- **Public repositories:** do not paste credentials, internal hostnames or private registry URLs into code or docs.

## Workflow

### 1. Recon (read before you write)

Run the detector to get a fast fact sheet, then read the files it points at:

```bash
python <skill-dir>/scripts/detect_vue_shell.py <path-to-vue-project-root>
```

It reports: Vue/router/i18n/UI-library versions, where the router is defined, the nav items found in `App.vue` (or the layout file), the styling approach (global CSS in App.vue, scoped, Tailwind, a component library), how many distinct hex colors and spacing values exist, and which header extras sit next to the nav (language switcher, profile menu, search, filters).

Then answer these questions yourself, from the code, before designing:

| Question | Why it matters |
|---|---|
| Where is the shell (the file that renders `<router-view>`)? | That is the file you restructure. |
| Where do nav labels come from (i18n keys, hard-coded strings)? | Keep using the same source; never hard-code a new label. |
| What sits in the header besides nav links? | Each item needs a new home: sidebar footer, top bar right side, or stays put. |
| Is there a global bar between header and content (filters, breadcrumbs)? | It moves into the content column, under the top bar. |
| Where do the shared utility classes live (`.card`, `.badge`, `table`)? | This is where the spacing pass has the most leverage. |
| Does any page assume the old layout (sticky offsets of 70px, `100vh` math, full-width heroes)? | Grep for `top: 70px`, `calc(100vh`, `position: sticky`, and fix them. |

### 2. Define design tokens

Create the token layer first, with values taken from the app's existing styles, so everything after it can reference variables instead of literals. Use `references/design-tokens.md` for the scale and naming. Put tokens in a dedicated stylesheet (for example `src/styles/tokens.css`) imported once in `main.js`, or in an unscoped `:root` block in `App.vue` if the project keeps everything there.

Keep the token set small: spacing (4px base), type scale, radii, shadows, a few semantic colors (surface, border, text, text-muted, primary, primary-soft, success/warning/danger), and layout sizes (sidebar width, collapsed width, top bar height, content max width).

### 3. Build the shell

Create these pieces (details and skeletons in `references/sidebar-implementation.md`):

1. **Nav config** - one array of `{ to, labelKey, icon }` objects in a small module, so the sidebar loops over data rather than repeating `<router-link>` blocks. Labels come from the existing i18n keys.
2. **`NavIcon` component** - inline SVG icons keyed by name, `currentColor` stroke, `aria-hidden="true"`. Pick icons that describe each section (dashboard grid, boxes, receipt, chart, and so on). No emoji.
3. **`useSidebar` composable** - `collapsed` (persisted in localStorage, guarded for SSR/private mode) and `mobileOpen`, with `toggleCollapsed`, `openMobile`, `closeMobile`. Close the drawer on route change and on Escape.
4. **`AppSidebar` component** - brand block at the top, nav list in the middle, secondary items (profile, language) at the bottom, collapse toggle. Active state from the router (`router-link-active`, with exact matching for the root route).
5. **`AppTopbar` component (slim)** - mobile menu button, page-level actions on the right (language switcher, profile menu). Skip it if the app has nothing to put there; do not add an empty bar.
6. **App shell** - CSS grid: `sidebar | content`. Under the breakpoint (1024px by default) the sidebar becomes an off-canvas drawer with a backdrop. The content column owns the scroll and the max-width.

Move existing header components (language switcher, profile menu) rather than rewriting them. Their events and props stay the same; only their slot in the layout changes. They may need small style tweaks to read well on a dark or tinted sidebar.

### 4. Spacing and polish pass

Walk the shared styles, then the page-level styles, and bring them onto the tokens. Prioritize by leverage:

1. Shared classes (cards, stat cards, tables, badges, buttons, form controls, page headers). One fix improves every page.
2. Page wrappers and section gaps: pick one vertical rhythm (for example `--space-6` between sections, `--space-4` inside cards) and apply it everywhere.
3. Page-specific one-offs that visibly break the scale. Do not chase every literal; fix what a user would notice.

Polish details that make the difference between "functional" and "professional":

- A clear active nav state (tinted background plus an accent bar or color change), a quieter hover state, and a visible focus ring (`:focus-visible`) on every interactive element.
- Consistent corner radius and one or two shadow levels, not a different shadow per component.
- Table headers in small uppercase muted type, comfortable row height, subtle row hover.
- Transitions of 150-200ms on color/background/width; wrap them in `@media (prefers-reduced-motion: no-preference)`.
- Page header pattern: title, one-line description, optional actions on the right.

### 5. Verify

Do these checks; do not report success on a clean build alone.

- Build succeeds (`npm run build` or the project's equivalent) and no new console errors appear.
- Every nav entry routes correctly and shows the active state, including the root route (it must not stay active on every page) and nested routes.
- Keyboard: Tab reaches every nav item, the collapse toggle and the mobile menu button in a sensible order; Escape closes the drawer; focus is visible.
- Accessibility basics: `<nav aria-label="...">` on the sidebar, `aria-current="page"` on the active link (router-link sets this), a real `<button>` with `aria-label` and `aria-expanded` for toggles, collapsed items keep an accessible name (`aria-label`/`title`).
- Responsive: check at roughly 1440px, 1024px and 390px wide. At narrow widths there is no horizontal page scroll and the drawer opens and closes.
- Longest label: switch to the language with the longest strings (for example Japanese or German) and confirm nothing truncates badly in expanded mode.
- If a browser tool (Playwright or similar) is available, take screenshots at those three widths and look at them. If not, say plainly that the visual check was not done and list what to look at.
- Search the diff for emoji, hard-coded colors that bypass tokens, and leftover references to the old header (`top-nav`, `nav-tabs`, sticky offsets).

### 6. Report

Finish with a short summary: files added and changed, the token values chosen and where they came from, what was verified and how, what was not verified, and any behavior-adjacent decision the user should confirm (for example where the language switcher ended up). Do not commit unless asked.

## Judgment calls

- **Sidebar color:** default to a light sidebar with a subtle border when the app is light-themed; a dark sidebar is a bigger visual statement, so offer it as an option rather than imposing it.
- **Many nav items (more than about 8):** group them under small muted section headings. Do not invent groups the app does not have; group by what the routes already imply.
- **Per-page filters or tool bars:** keep them in the content column; do not move them into the sidebar unless the user asks.
- **Third-party UI libraries (Element Plus, Vuetify, PrimeVue):** use the library's own theming and layout components instead of fighting them with overrides. Read `references/sidebar-implementation.md` section "Component libraries" first.
- **Tailwind projects:** express tokens through the Tailwind config and use utility classes in the new components; the skeletons translate directly.

## Reference files

- `references/design-tokens.md` - token names, the spacing/type scale, shadows, layout sizes, and how to derive them from an existing palette.
- `references/sidebar-implementation.md` - skeletons for nav config, `NavIcon`, `useSidebar`, `AppSidebar`, `AppTopbar`, the shell CSS, and library/Tailwind notes.
- `references/reference-app.md` - a worked before/after for a real app (a Vue 3 inventory dashboard with a top nav), useful as a calibration example.
- `scripts/detect_vue_shell.py` - the recon script from step 1.
