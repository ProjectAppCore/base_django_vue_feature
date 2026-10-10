---
trigger: manual
description: Project intelligence and lessons learned. Reference for project-specific patterns, preferences, and key insights discovered during development.
---

# Lessons Learned — Base Django Vue Feature

This file captures important patterns, preferences, and project intelligence that help work more effectively with this codebase. Updated as new insights are discovered.

> Refreshed 2026-08-12: earlier revisions carried patterns from the parent lineage (single `content` app, BusinessProposal/email registry, Nuxt `serve_nuxt`). None of that exists in this template — everything below is verified against the current code.

---

## 1. Architecture Patterns

### Single Django App: `base_feature_app`
- All domain code lives in `base_feature_app`; `django_attachments` is the only sibling app.
- **Per-domain packages**: `models/`, `views/`, `urls/`, `serializers/` are packages with one module per domain (`auth`, `blog`, `product`, `sale`, `staging_phase_banner`, `user`, `captcha`). New domains follow the same split.

### Service Layer
- Business logic belongs in `base_feature_app/services/` (currently `auth_service.py`); views stay thin.

### Guest checkout, protected products
- `Sale` stores customer data inline (email/address — **no FK to User**), holds `SoldProduct` via M2M; `SoldProduct → Product` is `on_delete=PROTECT`. Sales can be deleted (custom `delete()` cleans sold products); products referenced by sales cannot.

### Health endpoint as identity probe
- `/api/health/` returns `{status, project, environment}` — `project` = clone dir name, `environment` reads the **setting** (not raw `os.getenv`). Reason: a dead staging domain can fall through DNS/nginx to another app; external probes must verify WHO answered (fleet lesson F24).

## 2. Code Style & Conventions

### Backend: Function-Based Views (FBV)
- **All** DRF views use `@api_view` decorators, not class-based views. Never convert to CBV unless explicitly requested.

### Frontend: Pinia Stores
- Both Options API (`frontend/src/stores/auth.js`) and setup stores (`frontend/src/stores/product.js`) exist. Preserve the style of the store being extended; neither requires a conversion.
- HTTP requests go through the centralized service under `frontend/src/stores/services/`.
- i18n is frontend-side (`stores/i18n.js`, `language.js`) — models have **no** bilingual paired fields in this template.

### Naming
- Backend: snake_case. Frontend stores: camelCase/snake files (`stagingBanner.js`, `auth.js`); components PascalCase; composables `use*`.

## 3. Development Workflow

### Environment selection — the trap
- `DJANGO_SETTINGS_MODULE` picks the settings module (`manage.py` defaults to `settings_dev` → **SQLite**, DEBUG, console email; `settings_prod` → MySQL).
- `DJANGO_ENV` is a separate flag (`IS_PRODUCTION`) driving huey `immediate` and the health payload. **It does not switch databases.** Never run tests with `DJANGO_ENV=production` expecting MySQL.

### Backend commands always need the venv
```bash
cd backend && source venv/bin/activate && <command>   # or venv/bin/python
```
- The venv is also load-bearing for E2E: `playwright.config.mjs` boots `../backend/venv/bin/python manage.py runserver 127.0.0.1:8001`.

### Huey immediate mode in development
- With `DJANGO_ENV != 'production'`, huey runs `immediate=True` — no Redis/worker needed locally. No huey tasks are defined in the template yet.

### Frontend dev: Vite proxy
- Vite proxies API paths to the backend (`VITE_BACKEND_URL`, default `http://127.0.0.1:8000/`); the E2E webServer overrides it to `:8001`. Both servers must run for full functionality (Playwright self-provisions both, `reuseExistingServer: true`).

### Test execution rules
- Never run the full suite — always specify files; batches ≤20 tests.
- Backend: `pytest base_feature_app/tests/<file> -v` (from `backend/`, venv active).
- Frontend unit: `npm test -- test/<file>` (Jest).
- E2E: max 2 files per `npx playwright test` invocation; `RECAPTCHA_*` env emptied by the webServer.
- E2E seed recipe (mirrors `ci.yml`): migrate + `admin@gmail.com`/`password` + `create_fake_data 12`.

## 4. Testing Insights

### Backend conftest.py
- Custom coverage report (Unicode bars) replaces default pytest-cov output; `api_client` fixture provides an unauthenticated DRF APIClient; sub-suites carry their own fixtures.

### Flow map discipline
- Every user flow lives in `frontend/e2e/flow-definitions.json` (id, module, priority P1–P4, outcome classes) with `docs/USER_FLOW_MAP.md` as the readable mirror; specs tag `@flow:<id>` / `@outcome:<class>`. The Playwright reporter emits `e2e-results/flow-coverage.json`.
- Quality bar: `docs/TESTING_QUALITY_STANDARDS.md` + gate (`scripts/test_quality_gate.py`, `.testquality.yml`, baseline `.junk-baseline.json`). CI runs the gate at `--junk-severity=error`.

### Known traps
- `pytest.ini` `python_files = test_*.py` collects `management/commands/test_email.py` (not a test).
- `frontend/test/e2e/` is a dead legacy Playwright suite (no runner executes it) — do not add specs there; real E2E lives in `frontend/e2e/`.
- The QA engine's registry fallback says `db=mysql` for this project; the test path is SQLite (see §3).
