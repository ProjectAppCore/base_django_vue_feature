---
trigger: manual
description: Tech stack, dev setup, environment selection, design patterns and testing strategy. Read before implementation tasks.
---

# Technical — Base Django Vue Feature

## 1. Stack (verified versions, 2026-08-12)

| Layer | Tech |
|---|---|
| Backend | Django **6.0.5**, DRF **3.17.1**, simplejwt **5.5.1**, django-cors-headers 4.9, easy_thumbnails, django_attachments, django-cleanup, dbbackup, huey ≥2.5 (RedisHuey), gunicorn 23 |
| Frontend | Vue **3.5.x**, Pinia **3.0.x**, vue-router **5.0.x**, axios 1.16, Tailwind **4.3**, Vite (dev/build) |
| Testing | pytest (+ custom coverage reporter in `backend/conftest.py`), Jest **29.7**, Playwright **1.60** |
| Data | SQLite (dev/tests) · MySQL 8 utf8mb4 (`settings_prod`) · Redis (huey broker in prod) |

## 2. Environment selection — TWO independent mechanisms (do not conflate)

1. **`DJANGO_SETTINGS_MODULE`** picks the settings module. `manage.py` defaults to `base_feature_project.settings_dev` (DEBUG=True, **SQLite**, console email). `settings_prod` = MySQL utf8mb4. `backend/pytest.ini` pins `settings_dev` → **tests always run SQLite**.
2. **`DJANGO_ENV`** is only a flag read inside `settings.py` (`IS_PRODUCTION`): it drives huey `immediate=not IS_PRODUCTION` and the `/api/health/` `environment` field. It does **not** select the settings module. Never use `DJANGO_ENV=production` to "switch DB" here.

> Fleet note: the QA engine's registry fallback reports `db=mysql` for this project — that is wrong for the test path. Evidence: `backend/pytest.ini`, `settings_dev.py`.

## 3. Dev setup

```bash
# Backend (venv is REQUIRED — playwright's webServer boots ../backend/venv/bin/python)
cd backend && python3 -m venv venv && venv/bin/pip install -r requirements.txt
venv/bin/python manage.py migrate --no-input
# e2e seed (mirrors ci.yml):
venv/bin/python manage.py shell -c "from base_feature_app.models import User; User.objects.filter(email='admin@gmail.com').exists() or User.objects.create_user(email='admin@gmail.com', password='password', is_active=True)"
venv/bin/python manage.py create_fake_data 12

# Frontend
cd frontend && npm install   # Jest unit, Playwright e2e (chromium cached in ~/.cache/ms-playwright)
```

- `mysqlclient==2.2.8` builds in the venv (system libmysqlclient present on the work host) but is unused under `settings_dev`.
- E2E self-provisions: `playwright.config.mjs` `webServer` boots Django on `127.0.0.1:8001` and Vite on `127.0.0.1:5174` (`reuseExistingServer: true`, `RECAPTCHA_*` emptied). baseURL `http://127.0.0.1:5174`. Only the **Desktop Chrome** project is active.

## 4. Design patterns

- **Per-domain packages**: `models/`, `views/`, `urls/`, `serializers/` are packages with one module per domain (auth, blog, product, sale, staging_phase_banner, user, captcha).
- **FBV only**: DRF views use `@api_view` decorators. Never convert to CBV unprompted.
- **Service layer**: business logic in `services/` (currently `auth_service.py`); views stay thin.
- **Pinia stores**: both Options API (`frontend/src/stores/auth.js`) and setup stores (`frontend/src/stores/product.js`) exist; preserve the style of the store being extended. HTTP goes through the centralized service under `frontend/src/stores/services/`.
- **Custom admin**: `admin_site` (mounted at `/admin/`) plus default admin at `/admin-gallery/`.

## 5. Testing strategy

| Layer | Location | Count (2026-08-12) | Runner |
|---|---|---|---|
| Backend | `backend/base_feature_app/tests/` (8 sub-suites) + `django_attachments/tests.py` | 30 files / ~267 tests | `venv/bin/pytest` (settings_dev/SQLite), batches ≤20 |
| Frontend unit | `frontend/test/` (outside `test/e2e/`) | 26 files / ~312 cases | `npm test -- test/<file>` (Jest) |
| E2E | `frontend/e2e/` | 16 specs / 28 cases | `npx playwright test` (≤2 files per invocation) |

- **Flow map**: `frontend/e2e/flow-definitions.json` (20 flows, P1–P4, outcome classes success/error/failure/display) + human-readable `docs/USER_FLOW_MAP.md`. Spec tags `@flow:<id>` map 1:1 to flow ids; the Playwright reporter `e2e/reporters/flow-coverage-reporter.mjs` emits `e2e-results/flow-coverage.json`.
- **Quality gate**: `scripts/test_quality_gate.py` (+ `scripts/quality/`), config `.testquality.yml`, baseline `.junk-baseline.json`. CI runs it with `--junk-severity=error` (`.github/workflows/test-quality-gate.yml`). The in-repo copy is a fork of `vps-ops-toolkit/workflows/testing/` — keep it synced (`sync-test-quality-core.sh`).
- **CI** (`.github/workflows/ci.yml`): backend-tests · frontend-unit-tests · frontend-e2e-tests (migrate + seed + playwright) · coverage-summary (sticky PR comment).

## 6. Known technical constraints

- `pytest.ini` `python_files = test_*.py` also collects `management/commands/test_email.py` (a command, not a test) — collection hazard.
- `frontend/test/e2e/` holds 8 legacy Playwright specs that no runner executes (Jest ignores them; Playwright's testDir is `frontend/e2e/`).
- `package.json` still exposes `e2e:mobile` / `e2e:tablet` scripts, but those Playwright projects are commented out in the config.
