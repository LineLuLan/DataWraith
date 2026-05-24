# DataWraith â€” Risks

## Active risks

- **Embedded PostgreSQL availability**: `pgserver` currently has no Python 3.13
  wheel. Mitigation: keep Python 3.12 embedded mode and support a safe local
  PostgreSQL fallback through `--database-url` / `DATAWRAITH_DATABASE_URL`.
- **Accidental production targeting**: chaos/security scenarios can modify data.
  Mitigation: reject non-local PostgreSQL URLs by default and document the
  local-only safety model.
- **Real DB E2E coverage**: current local validation runs on Python 3.13 without
  `pgserver`. Mitigation: CI now has a Python 3.13 local PostgreSQL fallback
  E2E job; manual Python 3.12 embedded E2E remains required before release tags.
