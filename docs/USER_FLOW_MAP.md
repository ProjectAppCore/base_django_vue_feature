# User Flow Map

Version: 1.1.1
Last Updated: 2026-10-10
Description: End-to-end user flows for the Base Feature frontend (Vite + Vue 3 SPA), grouped by role, with the outcome classes (success / error / failure / display) each flow is expected to exercise.
Sources: frontend/e2e/flow-definitions.json, frontend/e2e/helpers/flow-tags.js, frontend/e2e specs, frontend/src/router/index.js, frontend/src/views/**, frontend/src/components/**, frontend/src/stores/**, backend/base_feature_app/{views,urls,permissions,admin.py}.

## Roles

- **Guest**: unauthenticated visitor. Can access all public routes (`/`, `/catalog`, `/product/:id`, `/blogs`, `/blog/:id`, `/manual`, `/about_us`, `/contact`, `/sign_in`, `/sign_up`, `/checkout`), sign in, sign up.
- **User**: authenticated customer (`User.Role.CUSTOMER`, the default). Adds `/dashboard` and the guest-route redirect away from `/sign_in`/`/sign_up`. Can navigate to `/backoffice` (router does not block it — see Admin Flows) but its API calls will 403.
- **Admin**: a user with `is_staff=True` — either a `User.Role.ADMIN` account or a Django superuser (`backend/base_feature_app/models/user.py:32-46`). Gates `users/` and `sales/` (`backend/base_feature_app/permissions/roles.py:16-22`) and the Django-admin-only "Login as this user" impersonation action (`backend/base_feature_app/admin.py:144-167`). **This role previously had zero flows in this map; it now has three (see Admin Flows). The gate is enforced entirely server-side — the Vue router does not check role/staff, only `requiresAuth`.**

## Conventions

- **Outcome classes** — every flow declares the subset of these it can actually exercise, no flow gets a free pass to `success`-only:
  - `success`: an action completes and produces a success state/message.
  - `error`: an action produces a validation or permission error message.
  - `failure`: an action is attempted and fails server-side (5xx, timeout, network down).
  - `display`: information is viewed (list/detail/table/empty state); reachability must come from UI navigation, and assertions must check real data, not bare visibility.
- **Priority**: P1 primary conversion/security path — P2 secondary but real user action — P3 supporting/edge content — P4 cosmetic or template-boilerplate.
- **Evidence**: every entry below cites the view/component/store/endpoint file(s) it was derived from — no flow in this document is guessed.
- **Selectors**: `data-testid` / ARIA role preferred per project convention. Noted per-flow below where the underlying markup has neither (see SELECTOR-DISCIPLINE note at the end).
- **`roles: [...]`** is documentation only (per `e2e-user-flows-check`); the coverage audit does not validate it. `shared` = behavior is identical for Guest and User.

## Shared Flows (Guest + User)

### Auth module

#### auth-login-email: Login with email/password
- Module: auth · Priority: P1 · Route: `/sign_in` · Roles: shared
- Description: User signs in with email and password credentials.
- Evidence: `frontend/src/views/auth/SignIn.vue:179-217`, endpoint `backend/base_feature_app/views/auth.py:48-75`.
- E2E Coverage: success ✅ (`frontend/e2e/auth/auth-login.spec.js`)

**Steps**
1. Open `/sign_in`; email/password fields visible.
2. Fill in email and password, submit.
3. `POST sign_in/` returns 200 → `authStore.login()`, then `window.location.href = '/dashboard'` (full reload, not a router push).

**Branches**
- Empty form submission stays on `/sign_in` (HTML5 `required` blocks it).
- Already-authenticated visitors are redirected to `/dashboard` by the guest guard (`auth-guest-redirect`).
- If a reCAPTCHA site key is configured, the form also requires a completed captcha before submit (`SignIn.vue:185-188`).

---

#### auth-login-invalid: Login with invalid credentials
- Module: auth · Priority: P1 · Route: `/sign_in` · Roles: shared
- Description: User sees a domain error when submitting invalid credentials (401).
- Evidence: `frontend/src/views/auth/SignIn.vue:206-208`; backend `backend/base_feature_app/views/auth.py:72-73`.
- E2E Coverage: error ✅ (`frontend/e2e/auth/auth-login.spec.js`)

**Steps**
1. Open `/sign_in`, fill in a non-existent/incorrect email+password.
2. `POST sign_in/` returns 401.
3. Toast (SweetAlert2, `role="alert"`) reads "Invalid credentials"; page stays on `/sign_in`.

**Branches**
- This flow is scoped specifically to the `status === 401` branch. The `else` branch (any other response) is a distinct, separately-modeled flow — see `auth-login-server-error` below.

---

#### auth-login-server-error: Login fails on server-side error *(new)*
- Module: auth · Priority: P2 · Route: `/sign_in` · Roles: shared
- Description: Sign-in fails for a reason other than invalid credentials — disabled account, captcha rejection, 5xx, or network/timeout — and shows a generic failure notification.
- Evidence: `frontend/src/views/auth/SignIn.vue:206-211` (`else` branch: any `error.response?.status !== 401`, including no `.response` at all on a network failure); backend paths that land here: disabled-account 403 (`backend/base_feature_app/services/auth_service.py:41-46`, mapped in `backend/base_feature_app/views/auth.py:67-70`), captcha-rejected 400 (`views/auth.py:54-59`).
- E2E Coverage: failure ✅ (`frontend/e2e/auth/auth-login.spec.js` — closed 2026-08-13)

**Steps**
1. Open `/sign_in`, submit valid-looking credentials.
2. Backend responds with anything other than 200/401 (403 disabled account, 400 captcha, 5xx) — or the request never completes (network down/timeout).
3. Toast reads "Error signing in"; page stays on `/sign_in`; reCAPTCHA widget resets if present.

**Notes**
- This branch and `auth-login-invalid`'s are mutually exclusive by status code, so they were split into two flow ids rather than one `outcomes:[...]` array, consistent with how `blog-detail-view`/`blog-detail-not-found` are already split in this map.
- Testable today via Playwright route interception (`page.route('**/sign_in/', route => route.fulfill({status:500,...}))` or `route.abort()`) — no special account fixture required for the network/5xx case; the disabled-account case needs a seeded inactive user.

---

#### auth-register: Register new account
- Module: auth · Priority: P1 · Route: `/sign_up` · Roles: shared
- Description: User registers a new account via the sign-up form.
- Evidence: `frontend/src/views/auth/SignUp.vue:231-284`; endpoint `backend/base_feature_app/views/auth.py:15-45`.
- E2E Coverage: success ✅, error ✅, failure ✅ (all `frontend/e2e/auth/auth-register.spec.js` — failure closed 2026-08-13)

**Steps**
1. Open `/sign_up`; fill first/last name, email, password, confirm password; submit.
2. `POST sign_up/` 201 → `authStore.login()` → `window.location.href = '/dashboard'`.

**Branches**
- Empty form stays on `/sign_up` (HTML5 `required`).
- Password < 8 chars, or password/confirm mismatch → client-side warning toast, no request sent (currently tested: mismatch case, `@outcome:error`).
- **Server-side outcomes are unified in one catch block** (`SignUp.vue:271-279`): `error.response.data.error` (e.g. duplicate-email 400 from `register_user`, `backend/.../services/auth_service.py:23-24`) and a bare network/5xx failure (`error?.message`, e.g. "Network Error") both resolve through the *same* message pipeline. That is why `failure` is added to this flow's own `outcomes` array rather than split into a new id, unlike login: there is no code-level branch to point a separate id at.

---

#### auth-google-login: Sign in or register with Google *(new)*
- Module: auth · Priority: P3 · Routes: `/sign_in`, `/sign_up` · Roles: shared
- Description: User authenticates via the "Continue with Google" button; backend creates or logs in the account.
- Evidence: button + flag `frontend/src/views/auth/SignIn.vue:80-98,145-146,219-224` and `frontend/src/views/auth/SignUp.vue:129-147,197-198,289-291`; shared handler `frontend/src/helpers/googleLogin.js:11-50`; endpoint `backend/base_feature_app/views/auth.py:78-106`.
- E2E Coverage: exempt (`expectedSpecs: 0`) — **structurally abstained, not a gap**: every e2e test sets `window.__E2E_DISABLE_GOOGLE_LOGIN__ = true` before navigation (`frontend/e2e/helpers/test.js:19-21`), so the button never renders in a spec run. Backend logic is fully unit-covered (`backend/base_feature_app/tests/services/test_auth_service.py:126-236`; `backend/base_feature_app/tests/views/test_auth_endpoints.py:167-317`).

**Steps**
1. Click "Continue with Google" (rendered by `vue3-google-login`'s `<GoogleLogin>`, a third-party iframe/button — not addressable via `data-testid`).
2. On credential, `POST google_login/`; success sets tokens and redirects to `/dashboard`, distinguishing "Registration successful!" vs "Sign in successful!" by `res.data.created`.

**Branches**
- Missing/rejected credential from Google → client-side "Google login failed" (`googleLogin.js:13-16`), no request sent.
- Backend `ValueError` on email resolution → 400; invalid/expired Google token → 401 (`views/auth.py:96-102`).
- Network/5xx → generic "Error during Google authentication" (same unified-pipeline pattern as `auth-register`).
- **Resolved 2026-08-13**: declared `exempt` (`expectedSpecs: 0`) rather than tested. Mocking Google Identity Services end-to-end, or building a controlled e2e test seam, remains a possible future product decision but is not required for coverage — the current `__E2E_DISABLE_GOOGLE_LOGIN__` flag is a deliberate structural exclusion, not an untested gap.

---

#### auth-logout: Sign out
- Module: auth · Priority: P2 · Route: `/` (header), also `/dashboard` · Roles: shared
- Description: User signs out; session/localStorage cleared.
- Evidence: `frontend/src/components/layouts/Header.vue:59-63,139-142,192-196`; also duplicated on `frontend/src/views/Dashboard.vue:11,24-27`.
- E2E Coverage: success ✅ (`frontend/e2e/auth/auth-logout.spec.js`)

**Steps**
1. Authenticated state in localStorage; open `/`.
2. Click "Sign Out" (`data-testid="header-sign-out"`, or `mobile-sign-out` on mobile).
3. `access_token` removed from localStorage; "Sign In" link reappears; redirected to `/`.

**Branches**
- Dashboard also exposes its own inline sign-out button (`Dashboard.vue:11`) that calls the same `authStore.signOut()` and redirects to `/sign_in` instead of `/` — same store action, different landing route; not modeled as a separate flow (same interaction, cosmetic redirect-target difference).

---

#### auth-protected-redirect: Protected route redirect
- Module: auth · Priority: P1 · Routes: `/dashboard`, `/backoffice` · Roles: shared
- Description: Unauthenticated user is redirected to `/sign_in` when accessing `requiresAuth` routes.
- Evidence: `frontend/src/router/index.js:107-112`.
- E2E Coverage: success ✅ (`frontend/e2e/auth/auth-protected-redirect.spec.js` — covers both `/dashboard` and `/backoffice`)

**Steps**
1. Clear cookies/localStorage; navigate directly to `/dashboard` or `/backoffice`.
2. Guard redirects to `/sign_in`.

**Branches**
- Applies to any route with `meta.requiresAuth` — currently `/dashboard` and `/backoffice`.
- This is the *logged-out* case for `/backoffice`. The *logged-in-but-non-staff* case is a different, previously-undeclared flow — see `backoffice-users-list` / `backoffice-sales-list` under Admin Flows.

---

#### auth-guest-redirect: Guest route redirect
- Module: auth · Priority: P2 · Routes: `/sign_in`, `/sign_up` · Roles: shared
- Description: Authenticated user is redirected away from guest-only routes.
- Evidence: `frontend/src/router/index.js:114-116`.
- E2E Coverage: success ✅ (`frontend/e2e/auth/auth-guest-redirect.spec.js`)

**Steps**
1. Authenticated state in localStorage; navigate to `/sign_in`.
2. Guard redirects to `/dashboard`.

**Branches**
- Applies to any route with `meta.requiresGuest` — currently `/sign_in`, `/sign_up`.

---

### Shopping module

#### shopping-catalog-browse: Browse product catalog
- Module: shopping · Priority: P1 · Route: `/catalog` · Roles: shared
- Evidence: `frontend/src/views/product/Catalog.vue`.
- E2E Coverage: success ✅ (`frontend/e2e/shopping/shopping-catalog.spec.js`)

**Steps**: open `/catalog`; category filter (`data-testid="category-filter"`) is clickable; product links (`a[href*="/product/"]`) navigate to detail.

**Branches**: sub-category checkboxes (`data-testid="subcategory-checkbox"`) refine the filter (`CategoryFilter.vue` → `SubCategoryFilter.vue`); empty catalog still renders the page shell (not independently asserted — see Cross-Cutting Notes).

---

#### shopping-product-detail: View product detail
- Module: shopping · Priority: P1 · Route: `/product/:product_id` · Roles: shared
- Evidence: `frontend/src/views/product/Detail.vue`.
- E2E Coverage: success ✅, display ✅ (both `frontend/e2e/shopping/shopping-product-detail.spec.js`)

**Steps**: from `/catalog`, open a product; quantity stepper (`data-testid="quantity-decrement/value/increment"`) adjusts; gallery/price/description load from the API.

**Branches**: non-existent product id (e.g. `/product/999999`) — `product` is a `computed` that returns `undefined`, so the entire `v-if="product"` panel (including add-to-cart) is absent (`Detail.vue:3`). No error message is shown; see the semantic note under Cross-Cutting Notes for how this differs from the blog case.

---

#### shopping-cart-add: Add product to cart
- Module: shopping · Priority: P1 · Route: `/product/:product_id` · Roles: shared
- Evidence: `frontend/src/views/product/Detail.vue:166-172`; store `frontend/src/stores/product.js:88-99`.
- E2E Coverage: success ✅ (`frontend/e2e/shopping/shopping-cart.spec.js`)

**Steps**: click "Add to Cart" (`data-testid="add-to-cart"`); Pinia store persists to localStorage; header cart badge updates.

**Branches**: adding the same product again increments its quantity instead of duplicating a row; the cart overlay's own per-row "Add" link (`CartProduct.vue:23-26`) performs the same increment — same store action, different entry point.

---

#### shopping-cart-remove: Remove product from cart *(new)*
- Module: shopping · Priority: P2 · Routes: cart overlay (any page), `/checkout` · Roles: shared
- Description: User removes a product, or decrements its quantity, from the cart overlay or the checkout page.
- Evidence: `frontend/src/components/product/CartProduct.vue:23-31` (emits `removeProduct`) → `frontend/src/components/product/ShoppingCart.vue:156-172` (`handleRemoveProduct`); independently on `frontend/src/views/product/Checkout.vue:146-150,267-269`; store `frontend/src/stores/product.js:105-118` (`removeProductFromCart` — decrements qty, or drops the row at qty 1).
- E2E Coverage: success ✅ (`frontend/e2e/shopping/shopping-cart.spec.js` — closed 2026-08-13)

**Steps**
1. Open the cart overlay (or `/checkout`) with ≥1 item.
2. Click "Remove" on a line item.
3. Quantity decrements, or the row disappears when quantity was 1; subtotal updates; localStorage (`cartProducts`) updates.

**Notes**: purely client-side Pinia state — no server round trip, so `success` is the only applicable outcome (no `error`/`failure` surface).

---

#### shopping-cart-persist: Cart persists across pages
- Module: shopping · Priority: P2 · Routes: `/product/:id`, `/catalog` · Roles: shared
- E2E Coverage: display ✅ (`frontend/e2e/shopping/shopping-cart.spec.js` — **repaired 2026-08-13**: the dead `cart-count` selector and its passes-either-way URL fallback were replaced with real overlay assertions (`cart-overlay` visible + `Qty 1` line item), and the unguarded `localStorage.clear()` in the file's `beforeEach` — which re-ran on every navigation, wiped the cart mid-test and is why the false green survived — now uses the idempotent sessionStorage guard from `auth-login.spec.js`). The `Header.vue` badge still lacks `data-testid="cart-count"` (product backlog).

**Steps**: add a product from detail, navigate to `/catalog`, cart state (item count) should still be reflected.

---

#### shopping-checkout-complete: Complete checkout flow
- Module: shopping · Priority: P1 · Route: `/checkout` · Roles: shared
- Evidence: `frontend/src/views/product/Checkout.vue` (`handleSubmit`), `frontend/src/stores/product.js` (`createSale`), `backend/base_feature_app/serializers/sale.py` (`SaleSerializer.create`).
- E2E scenarios: success, error and failure in `frontend/e2e/shopping/shopping-checkout.spec.js`. The success scenario verifies a real POST 201; runtime execution is accredited by the artifacts and CI of the associated PR.

**Steps**: add a real catalog product, open the cart, follow its Checkout button, fill email/card/expiry/cvc/address/city/state/postal (all `data-testid="checkout-*"`) and click "Pay Now". While the request is pending the submit button is disabled and duplicate submits are ignored. Only `POST create-sale/` returning 201 clears the cart, shows "Order created successfully" and navigates to `/`. The demo creates an order; it does not process card payments.

**Branches**: empty required fields keep the user on `/checkout` (HTML5 validation), the `error` outcome. HTTP 400/500 or a network failure shows a localized error, preserves the cart and form, and enables another deliberate submission; this is the `failure` outcome. No automatic retry of order creation is added.

---

### Blog module

#### blog-list-view: View blog listing
- Module: blog · Priority: P2 · Route: `/blogs` · Roles: shared
- E2E Coverage: success ✅ (`frontend/e2e/blog/blog-list.spec.js`)

**Steps**: open `/blogs`; blog links (`a[href*="/blog/"]`) navigate to detail.

---

#### blog-detail-view: View blog detail
- Module: blog · Priority: P2 · Route: `/blog/:blog_id` · Roles: shared
- E2E Coverage: success ✅ (`frontend/e2e/blog/blog-detail.spec.js` — open-from-list, and back-navigation)

**Steps**: open a post from `/blogs`; article (`data-testid="blog-article"`) shows title/description/image.

---

#### blog-detail-not-found: Blog detail handles non-existent entry
- Module: blog · Priority: P3 · Route: `/blog/999999` · Roles: shared
- E2E Coverage: display ✅ (`frontend/e2e/blog/blog-detail.spec.js`)

**Steps**: navigate directly to a non-existent blog id.

**Semantic note (resolved 2026-08-13 — relabeled, not a test gap)**: `Detail.vue` initializes `blog = reactive({})` (`frontend/src/views/blog/Detail.vue:33`), which is always truthy, so `v-if="blog"` never hides the article region (`:3,54-56`). A missing id renders an **empty** article (blank `<h1>`, broken image) rather than any error message. The existing spec's own comment already says this: *"The scaffold has no real not-found handling... Asserting the empty title documents that degraded behavior — a template gap worth closing"* (`frontend/e2e/blog/blog-detail.spec.js:6-11,47-53`). Per the outcome-class rubric this is a degraded **`display`** (empty state), not an `error` (validation/permission message) — relabeled to `display` this run (`flow-definitions.json`, the spec's `@outcome:` tag, and this doc updated together; no test-body change needed, the spec already asserted the empty state correctly). The template gap itself — `Detail.vue` has no real not-found handling — is left open as a product-backlog item, not a test gap.

---

### Home module

#### home-carousel-navigate: Navigate home trending grids
- Module: home · Priority: P3 · Route: `/` · Roles: shared
- Description: todos los productos y blogs recibidos se muestran en orden, en grillas estáticas de 1/2/5 columnas. Se conservan los nombres de componentes y el ID del flujo.
- Evidence: `frontend/src/components/product/ProductCarousel.vue`, `frontend/src/components/blog/BlogCarousel.vue`, `frontend/src/views/Home.vue`.
- E2E: `frontend/e2e/home/home-carousels.spec.js`; escenarios actualizados, ejecución de esta ronda pendiente del QA combinado.

**Steps**: abrir Inicio, comprobar cantidad contra la respuesta real del API, llegar al último producto/blog con scroll normal y abrir su detalle verificando ID y título. No hay flechas, transform ni autoplay.

**Matriz**: 835×1194 primero (2 columnas); 412×915 (1); 1195×835, 1440×900 y 2560×1440 (5). La interacción comprueba ausencia de overflow horizontal del documento. No se infiere acceso por cambios de transform.

**Outcomes**: success — navegación al registro correcto. Error/failure no tienen estados propios de estas grillas; carga/datos vacíos conservan el comportamiento existente y se verifican en unit.

---

### Navigation module

#### header-search: Search modal open/close
- Module: navigation · Priority: P2 · Roles: shared
- Description: búsqueda disponible directamente en la barra, también en celular/tableta, sin abrir el menú móvil.
- Evidence: `frontend/src/components/layouts/Header.vue`, `frontend/src/components/layouts/SearchBar.vue`.
- E2E: `frontend/e2e/navigation/navigation-search.spec.js`; escenarios actualizados, ejecución de esta ronda pendiente del QA combinado.

**Steps**: abrir `header-search`, buscar un título real, seleccionar su resultado y verificar ID/título del detalle y cierre del overlay. Otro escenario conserva el cierre mediante `search-close`.

**Matriz**: 835×1194 primero; luego 412×915, 1195×835, 1440×900 y 2560×1440. El trigger mide al menos 44×44 px; el Header no produce overflow horizontal. SearchBar conserva sus controles y layout internos; su presentación con muchos resultados requiere inspección visual, no se certifica por esta actualización.

**Outcomes**: success — búsqueda/navegación y cierre. Error/failure no tienen presentación propia en la búsqueda actual; no se inventan nuevos estados.

---

#### header-cart-overlay: Cart overlay open/close
- Module: navigation · Priority: P2 · Roles: shared
- Evidence: `frontend/src/components/layouts/Header.vue`, `frontend/src/components/product/ShoppingCart.vue`.
- E2E: success y display en `frontend/e2e/navigation/navigation-cart-overlay.spec.js`; escenarios actualizados, ejecución de esta ronda pendiente del QA combinado.

**Steps**: agregar un artículo por la interfaz del catálogo y abrir `header-cart` directamente desde la barra. El panel y Checkout quedan disponibles sin animación decorativa. Cerrar con `cart-close`, reabrir y comprobar título, cantidad, subtotal y almacenamiento conservados; navegar a Checkout. El backdrop mantiene su cierre donde queda expuesto (desde 1024 px); en celular/tableta vertical el panel ocupa todo el ancho y se usa el botón real.

**Matriz**: 835×1194 primero; luego 412×915, 1195×835, 1440×900 y 2560×1440. Los controles de la barra miden al menos 44×44 px y no producen overflow horizontal. Sin skips móviles, viewport forzado ni cambios internos en ShoppingCart.

**Branches**: carrito vacío muestra “No products” y su enlace “Continue Shopping” abre catálogo; carrito con artículos conserva líneas, subtotal y Checkout. Los contratos de creación de pedido y sus fallos pertenecen a los flujos de checkout existentes, que se reejecutan como regresión.

---

#### theme-toggle: Switch color theme
- Module: navigation · Priority: P4 · Roles: shared
- Description: una única instancia de ThemeToggle está disponible directamente en la barra a todos los anchos; la preferencia persiste.
- Evidence: `frontend/src/components/layouts/Header.vue`, `frontend/src/components/layouts/ThemeToggle.vue`, `frontend/src/stores/theme.js`.
- E2E: `frontend/e2e/navigation/navigation-theme-toggle.spec.js`; escenarios actualizados, ejecución de esta ronda pendiente del QA combinado.

**Steps**: abrir “Toggle theme”, seleccionar Light/Dark/System y recargar; la preferencia se conserva. El escenario de esta revisión selecciona Dark y comprueba la clase de `<html>` después de la recarga.

**Matriz**: 835×1194 primero; luego 412×915, 1195×835, 1440×900 y 2560×1440. Trigger de 44×44 px y opciones de al menos 44 px de alto, sin overflow horizontal del documento. Headless UI mantiene rol `menuitem` para las opciones y navegación por teclado.

**Outcomes**: success — preferencia aplicada y conservada. No hay API ni error/failure propios de esta acción.

---

#### not-found-page: 404 not found page
- Module: navigation · Priority: P3 · Route: `/:pathMatch(.*)*` · Roles: shared
- E2E Coverage: display ✅ (`frontend/e2e/navigation/navigation-not-found.spec.js`)

---

### Static module

#### static-about: View About Us page
- Module: static · Priority: P4 · Route: `/about_us` · Roles: shared
- E2E Coverage: display ✅ (`frontend/e2e/static/static-pages.spec.js`)

#### static-contact: View Contact page
- Module: static · Priority: P4 · Route: `/contact` · Roles: shared
- E2E Coverage: display ✅ (`frontend/e2e/static/static-pages.spec.js`)

**Note**: the Contact page's `<form>` (`frontend/src/views/Contact.vue:18-34`) has no `@submit` handler and no `v-model` bindings — it is decorative markup, not a functioning flow. Correctly excluded (nothing to submit).

---

### Manual module *(new module)*

#### manual-view: View the operations manual *(new)*
- Module: manual · Priority: P3 · Route: `/manual` · Roles: shared
- Description: User opens the public Manual page from the header nav and browses sections/process cards via the sidebar.
- Evidence: route `frontend/src/router/index.js:74-79`; view `frontend/src/views/manual/Manual.vue`; nav link `frontend/src/components/layouts/Header.vue:23-25,120-123`; sidebar `frontend/src/components/manual/ManualSidebar.vue` (collapsible sections, mobile drawer).
- E2E Coverage: display ✅ (`frontend/e2e/manual/manual-view.spec.js` — closed 2026-08-13)

**Steps**: click "Manual" in the header; sidebar TOC lists sections; each section renders `ProcessCard`s; sidebar links jump to `#section-<id>` anchors.

---

#### manual-search: Search the manual *(new)*
- Module: manual · Priority: P3 · Route: `/manual` · Roles: shared
- Description: User searches manual sections by keyword, navigates results with the keyboard, and jumps to a matching process card.
- Evidence: `frontend/src/components/manual/ManualSearch.vue:76-188` (Fuse.js fuzzy index, debounced, `role="searchbox"`/`role="listbox"`/`role="option"`); `frontend/src/lib/manual/useManualSearch.js`.
- E2E Coverage: success ✅, display ✅ (`frontend/e2e/manual/manual-search.spec.js` — closed 2026-08-13)

**Steps**: type a query (`role="searchbox"`); results list (`role="option"`) appears; arrow keys move `highlighted`, Enter selects, Escape clears; selecting a result scrolls to and highlights the matching `ProcessCard`.

**Branches**: empty result set shows a "no results" message (`ManualSearch.vue:40-45`) — this is the `display` outcome (no message, no server call, purely a rendered empty state driven by the local Fuse index).

---

### Platform module *(new module — scaffold-wide infrastructure, not a product feature)*

#### staging-phase-banner-display: Staging review banner *(new)*
- Module: platform · Priority: P4 · Roles: shared (visible on every route)
- Description: Sticky banner shown site-wide during an active (non-expired) staging review phase, with day-count and phase label.
- Evidence: `frontend/src/components/staging/StagingGate.vue:1-33` (wraps `<RouterView>` in `frontend/src/App.vue:2`); `frontend/src/components/staging/StagingPhaseBanner.vue:1-46` (`data-testid="staging-phase-banner"`); backend `backend/base_feature_app/views/staging_phase_banner.py:10-21`.
- E2E Coverage: display ✅ (`frontend/e2e/platform/staging-banner.spec.js` — closed 2026-08-13; serial file that seeds the singleton per test and resets it to inert (`started_at=None`) on exit)

**Notes**: the `StagingPhaseBanner` singleton defaults `is_visible=True` but `started_at=null` (`backend/base_feature_app/models/staging_phase_banner.py:26-28`), and `isActive` requires both `is_visible` **and** `started_at` (`StagingGate.vue:23-29`) — so the gate is **inert by default** until an admin explicitly sets `started_at`. Testing this flow requires seeding that row (Django admin or direct API/DB fixture).

---

#### staging-review-expired-overlay: Staging review expired overlay *(new)*
- Module: platform · Priority: P3 · Roles: shared (blocks every route when active)
- Description: Full-site blocking overlay shown once the staging review window has expired, replacing all content with WhatsApp/email contact CTAs.
- Evidence: `frontend/src/components/staging/StagingExpiredOverlay.vue:1-57` (`data-testid="staging-expired-overlay"`, `staging-expired-whatsapp`, `staging-expired-email`); mutually exclusive with the banner via `StagingGate.vue:31-32`.
- E2E Coverage: display ✅ (`frontend/e2e/platform/staging-banner.spec.js` — closed 2026-08-13, same serial file)

**Notes**: higher priority than the banner (P3 vs P4) because, unlike the banner, this state **replaces `<slot />` entirely** — every other page becomes unreachable while it is active. Same fixture-seeding requirement as above. `stagingBanner` store fetch failures are silently swallowed (`frontend/src/stores/stagingBanner.js:38-40`, comment: "gate falls back to rendering children unchanged") — there is no distinct `failure`/`error` UI state for this module; a backend outage looks identical to "staging feature inactive."

---

## Admin Flows

*(Previously: "Admin: No dedicated frontend flows found in the current app or E2E suite." That was already inaccurate at the time it was written — `Backoffice.vue` was added in the same commit as that sentence. It is corrected here.)*

#### admin-login-handoff: Admin impersonation session handoff *(new)*
- Module: auth · Priority: P2 · Route: `/admin-login` · Roles: admin
- Description: The Vue app redeems the access/refresh tokens issued by the Django-admin "Login as this user" action and lands the admin authenticated as the target user; missing/invalid tokens redirect to `/sign_in`.
- Evidence: trigger (Django admin, **not** part of `frontend/src`) — `backend/base_feature_app/admin.py:123-167` (`login_as_link`, restricted to `request.user.is_active and request.user.is_superuser`; blocks impersonating another superuser or an inactive target, surfaced via Django's own `messages.error` on the admin change page); redemption — `frontend/src/views/auth/AdminLogin.vue:24-40`; router `frontend/src/router/index.js:26-31`.
- E2E Coverage: success ✅, error ✅ (`frontend/e2e/admin/admin-login-handoff.spec.js` — closed 2026-08-13, real cross-system handoff: Django-admin session → popup → token redemption on the Vite origin); unit-level coverage also exists for the redemption side (`frontend/test/views/AdminLogin.test.js`) and the Django-admin trigger (`backend/base_feature_app/tests/admin/test_admin.py`).

**Steps**
1. (Trigger, Django admin — reachable in the e2e harness at `http://127.0.0.1:8001/admin/`, already used as the Playwright `webServer` health-check URL) superuser opens a user's admin change page, clicks "Login as this user".
2. Backend issues tokens, redirects to `{FRONTEND_URL}/admin-login?access=...&refresh=...&redirect=/`.
3. `AdminLogin.vue` sets tokens, calls `authStore.restoreSession()`, replaces to the sanitized `redirect` target (open-redirect guarded: only same-origin absolute paths — `safeRedirectTarget`, `AdminLogin.vue:18-22`).

**Branches**
- Missing `access` or `refresh` query param → `router.replace({name:'sign_in'})` (`error` outcome).
- Django-side guard rejects impersonating another superuser or an inactive target (`admin.py:151-157`) — this happens **before** the Vue app is ever reached, so it is out of scope for `frontend/e2e/` proper; noted here for completeness since it is the same end-to-end user story.

---

#### backoffice-users-list: Backoffice — list users *(new)*
- Module: admin · Priority: P2 · Route: `/backoffice` · Roles: admin
- Description: Staff user views the Users table; a non-staff authenticated user gets a permission error instead of data.
- Evidence: `frontend/src/views/Backoffice.vue:14-45` (table: email/role/staff/active), `:96-107` (`fetchUsers`); endpoint `backend/base_feature_app/views/user_crud.py:12-20` (`IsAdminUser`).
- E2E Coverage: display ✅, error ✅ (`frontend/e2e/admin/backoffice.spec.js` — closed 2026-08-13; the backend 403 contract is additionally covered by `backend/base_feature_app/tests/views/test_crud_endpoints.py::test_users_list_rejects_non_staff_authenticated`). The *logged-out* redirect for this route remains covered by `auth-protected-redirect`.

**Steps**
1. Sign in as a staff user (`is_staff=True`); open `/backoffice`.
2. `GET users/` 200 → table rows render (`display`).

**Branches**
- Sign in as a **non-staff** authenticated user (default `Role.CUSTOMER`, `is_staff=False`) → router lets them through (`requiresAuth` only, no staff check) → `GET users/` 403 → `error.value = 'Could not load backoffice data. Make sure you are signed in with a staff user.'` (`error` outcome, real and cheap to set up — no route mocking needed, just a regular non-staff account).
- The same catch block also fires on a genuine network/5xx failure loading `users/`, with the identical message — technically a `failure`-class code path too, but not declared here since the code does not distinguish it from the permission case (no separate assertable state); noted for the Architect.

---

#### backoffice-sales-list: Backoffice — list sales *(new)*
- Module: admin · Priority: P2 · Route: `/backoffice` · Roles: admin
- Description: Staff user views the Sales table; a non-staff authenticated user gets a permission error instead of data.
- Evidence: `frontend/src/views/Backoffice.vue:47-80` (table: id/email/city/state/postal), `:109-120` (`fetchSales`); endpoint `backend/base_feature_app/views/sale_crud.py:11-19` (`IsAdminUser`).
- E2E Coverage: display ✅, error ✅ (`frontend/e2e/admin/backoffice.spec.js` — closed 2026-08-13; backend 403 contract idem via `test_sales_list_rejects_non_staff_authenticated`)

**Steps / Branches**: identical shape to `backoffice-users-list`, independent "Refresh" button and independent API call (`sales/`), same shared error copy on both permission-denied and generic failure.

---

## Cross-Cutting Notes (evidence-only, not ranked — ranking is the Architect's call)

1. **Checkout now observes creation failures.** `Checkout.vue` waits for the status returned by `createSale` and requires 201 before clearing the cart. HTTP/network rejection stays visible on checkout with preserved inputs and cart; the store propagates the failure. `shopping-checkout-complete` now declares `failure`. Component/store tests cover the change; E2E execution is accredited by the artifacts and CI of the associated PR.

2. **Two "error"-tagged flows were really degraded empty-display states, not error messages — relabeled 2026-08-13.** `blog-detail-not-found`: `Detail.vue` initializes `blog = reactive({})` (`frontend/src/views/blog/Detail.vue:33`), which is always truthy, so a missing blog id renders an *empty* article shell (blank `<h1>`, broken image) instead of hiding anything or showing a message (`:54-56`). The existing spec's own comment already names this: *"The scaffold has no real not-found handling... a template gap worth closing"* (`frontend/e2e/blog/blog-detail.spec.js:6-11,47-53`). `shopping-product-detail`'s not-found branch is the cleaner sibling of the same pattern: `product` is a `computed` returning `undefined` for a bad id, so the whole `v-if="product"` panel is correctly absent (`frontend/src/views/product/Detail.vue:3`) — no message either, just nothing rendered. Both flows' declared outcome and both specs' `@outcome:` tags are now `display` (`frontend/e2e/blog/blog-detail.spec.js`, `frontend/e2e/shopping/shopping-product-detail.spec.js`); no test-body change was needed, only the classification. The underlying template gap (no real not-found handling) is left open as a product-backlog item, not a test gap.

3. **Silent fetch-failure swallow, app-wide.** `frontend/src/stores/product.js:78-80` (`fetchProducts`), `frontend/src/stores/blog.js:37-39` (`fetchBlogs`), and `frontend/src/stores/stagingBanner.js:38-40` (`fetchState`, comment: "Silent failure: gate falls back to rendering children unchanged") all catch fetch errors with `console.error`/silent-fallback only — no UI-visible error state anywhere. A backend outage while browsing home/catalog/blogs/manual is visually indistinguishable in the DOM from "zero records available." Because the skill requires `display` flows to assert real data (not bare visibility), and a network failure and an empty dataset render identically here, this was **not** added as a declared `failure`/`error` outcome on `shopping-catalog-browse`, `blog-list-view`, or `home-carousel-navigate` — there is no distinct, assertable state to test against.

4. **Dead/phantom selector.** `[data-testid="cart-count"]` is asserted in `frontend/e2e/shopping/shopping-cart.spec.js:59` but does not exist anywhere in `frontend/src` (confirmed via full-tree search; the header cart badge at `frontend/src/components/layouts/Header.vue:44-48` has no `data-testid`). Already flagged in commit `0535511`'s message as a "dead cart-count selector; verification branch unreachable" — the `shopping-cart-persist` test's fallback assertion (`toHaveURL(/\/catalog/)`) is what actually passes today.

5. **Dead language-switch code — confirms no locale-switch flow exists.** `frontend/src/views/product/Checkout.vue:246-248` defines `handleLanguage` but it is never bound in any template; `frontend/src/stores/i18n.js:29-35` defines `setLocale` but no `.vue` file ever calls it. Two separate store implementations for switching language/locale exist in the codebase and neither has a UI trigger — confirms no such user-facing flow should be in this map.

6. **Ambiguous-selector risk for newly-mapped flows.** `Backoffice.vue`'s two "Refresh" buttons (Users section and Sales section) share the identical accessible name, so `page.getByRole('button', {name:'Refresh'})` would match both ambiguously. `CartProduct.vue`'s per-row "Add"/"Remove" links (`:23-31`) carry no distinguishing attribute per product row. Both are concrete selector-fragility risks for whoever writes specs against `backoffice-users-list`/`backoffice-sales-list` and `shopping-cart-remove`.

## E2E Coverage Index

| Flow id | Module | Priority | Outcomes declared | Coverage by outcome | Spec file(s) |
|---|---|---|---|---|---|
| auth-login-email | auth | P1 | success | success ✅ | auth/auth-login.spec.js |
| auth-login-invalid | auth | P1 | error | error ✅ | auth/auth-login.spec.js |
| auth-login-server-error | auth | P2 | failure | failure ✅ | auth/auth-login.spec.js |
| auth-register | auth | P1 | success, error, failure | success ✅ · error ✅ · failure ✅ | auth/auth-register.spec.js |
| auth-google-login | auth | P3 | exempt (expectedSpecs:0) | — (structurally abstained) | — |
| auth-logout | auth | P2 | success | success ✅ | auth/auth-logout.spec.js |
| auth-protected-redirect | auth | P1 | success | success ✅ | auth/auth-protected-redirect.spec.js |
| auth-guest-redirect | auth | P2 | success | success ✅ | auth/auth-guest-redirect.spec.js |
| admin-login-handoff | auth | P2 | success, error | success ✅ · error ✅ | admin/admin-login-handoff.spec.js |
| shopping-catalog-browse | shopping | P1 | success | success ✅ | shopping/shopping-catalog.spec.js |
| shopping-product-detail | shopping | P1 | success, display | success ✅ · display ✅ | shopping/shopping-product-detail.spec.js |
| shopping-cart-add | shopping | P1 | success | success ✅ | shopping/shopping-cart.spec.js |
| shopping-cart-remove | shopping | P2 | success | success ✅ | shopping/shopping-cart.spec.js |
| shopping-cart-persist | shopping | P2 | display | display ✅ (repaired 2026-08-13) | shopping/shopping-cart.spec.js |
| shopping-checkout-complete | shopping | P1 | success, error, failure | success · error · failure (execution evidence in PR artifacts/CI) | shopping/shopping-checkout.spec.js |
| blog-list-view | blog | P2 | success | success ✅ | blog/blog-list.spec.js |
| blog-detail-view | blog | P2 | success | success ✅ | blog/blog-detail.spec.js |
| blog-detail-not-found | blog | P3 | display | display ✅ (relabeled 2026-08-13, see notes) | blog/blog-detail.spec.js |
| home-carousel-navigate | home | P3 | success | success: ejecución ronda 2 pendiente | home/home-carousels.spec.js |
| header-search | navigation | P2 | success | success: ejecución ronda 2 pendiente | navigation/navigation-search.spec.js |
| header-cart-overlay | navigation | P2 | success, display | success/display: ejecución ronda 2 pendiente | navigation/navigation-cart-overlay.spec.js |
| theme-toggle | navigation | P4 | success | success: ejecución ronda 2 pendiente | navigation/navigation-theme-toggle.spec.js |
| not-found-page | navigation | P3 | display | display ✅ | navigation/navigation-not-found.spec.js |
| static-about | static | P4 | display | display ✅ | static/static-pages.spec.js |
| static-contact | static | P4 | display | display ✅ | static/static-pages.spec.js |
| manual-view | manual | P3 | display | display ✅ | manual/manual-view.spec.js |
| manual-search | manual | P3 | success, display | success ✅ · display ✅ | manual/manual-search.spec.js |
| backoffice-users-list | admin | P2 | display, error | display ✅ · error ✅ | admin/backoffice.spec.js |
| backoffice-sales-list | admin | P2 | display, error | display ✅ · error ✅ | admin/backoffice.spec.js |
| staging-phase-banner-display | platform | P4 | display | display ✅ | platform/staging-banner.spec.js |
| staging-review-expired-overlay | platform | P3 | display | display ✅ | platform/staging-banner.spec.js |

**Aggregate**: 31 flows (was 20; 30 required + 1 exempt) · 40 outcome-instances (was 23): success 18, error 6, failure 3 (was 0), display 13 (was 4) · priority split P1:8 P2:12 P3:7 P4:4.

**Coverage (2026-08-13, post-QA run)**: 30/30 of the required flows covered; 1 flow is exempt. `auth-google-login` is declared `exempt` (`expectedSpecs: 0`) — structurally abstained, not a gap: every e2e test sets `window.__E2E_DISABLE_GOOGLE_LOGIN__` (`frontend/e2e/helpers/test.js:19-21`) so the button never renders, external-provider verification remains outside this exemption. Permissive backend tests are not evidence that Google authentication is secure.


**Checkout execution evidence**: the historical coverage totals above do not certify the revised checkout behavior. Its success spec verifies a real POST 201 and visible confirmation; failure specs verify preserved inputs and cart after HTTP/network rejection. Their runtime execution is accredited by the artifacts and CI of the associated PR, rather than by this static map.
