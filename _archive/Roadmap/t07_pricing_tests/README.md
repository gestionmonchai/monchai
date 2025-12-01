# T07 Pricing Test Suite (Mon Chai)

This suite provides **API tests (pytest)**, **UI tests (Playwright)** and **performance tests (k6)** for Pricing (roadmaps 42–46).

## Structure
- `api_pytest/` — pytest API tests
  - `conftest.py` — CLI options: `--base-url`, `--org-id`, `--auth-token`
  - `helpers.py` — minimal HTTP helpers (httpx)
  - `test_t07_42_price_lists.py`
  - `test_t07_43_discounts.py`
  - `test_t07_44_taxes.py`
  - `test_t07_45_simulator.py`
- `ui_playwright/`
  - `t07_pricing.spec.ts` — UI smoke for lists & simulator
- `perf_k6/`
  - `t07_simulator.js` — simulator p95 < 200ms
  - `t07_price_list_read.js` — lists read p95 < 600ms

## Prereqs
- Python 3.10+, `pip install pytest httpx`
- Node 18+, `npm i -D @playwright/test && npx playwright install`
- k6 `https://k6.io`

## Run
### API (pytest)
```bash
export BASE_URL=http://localhost:8000
export AUTH_TOKEN=devtoken
pytest -q api_pytest -m t07 --base-url $BASE_URL --auth-token $AUTH_TOKEN
```

### UI (Playwright)
```bash
export BASE_URL=http://localhost:3000
npx playwright test ui_playwright/t07_pricing.spec.ts --headed
```

### Perf (k6)
```bash
export BASE_URL=http://localhost:8000
export AUTH_TOKEN=devtoken
k6 run perf_k6/t07_simulator.js
k6 run perf_k6/t07_price_list_read.js
```

## Notes
- Endpoints and payloads follow the **contracts** from the detailed roadmaps.
- Adjust IDs (clients, cuvées, UOM) to your seed data or load the fixtures defined in roadmaps 42–46.
- Make sure RBAC/RLS and CSRF are satisfied in your environment.
