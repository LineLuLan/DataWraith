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
- **Windows embedded pgserver**: `pgserver` installs on Windows Python 3.12 but
  bundled `initdb` is flaky on GitHub Windows runners. Mitigation: Windows CI
  keeps package/dry-run/build coverage while real DB execution is covered by
  Linux/macOS embedded jobs and the Linux PostgreSQL fallback E2E job.
