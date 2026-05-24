# DataWraith — Decisions

## 2026-05-24 — Bootstrap scaffold before full engine

Decision: create package, contracts, docs, CI, and minimal UI/CLI first before
implementing the full Concurrency scenario.

Reason: the brief prioritizes engine-first quality and stable module ownership.
A healthy scaffold lets Dev A/B/C work in parallel without changing public
contracts mid-phase.

## 2026-05-24 — pgserver version marker

Decision: declare `pgserver>=0.1.4,<0.2.0; python_version < '3.13'` and load it
lazily.

Reason: PyPI currently lists `pgserver` 0.1.4 as latest and provides wheels
through Python 3.12. The original brief mentioned `pgserver>=0.2`, but that
version is not available. Lazy loading keeps Python 3.13 scaffold checks green
while documenting that embedded PostgreSQL requires Python 3.12 for now.

## 2026-05-24 — Start with dry-run engine primitives on Python 3.13

Decision: implement schema parsing, seed planning, and CLI dry-runs before real
database execution.

Reason: the active local runtime is Python 3.13 and cannot start `pgserver`.
Dry-run primitives are still Phase 1-aligned, testable, and become reusable by
the Python 3.12 `ShadowDB` execution path.


## 2026-05-24 - Build Phase 2 behind the Python 3.12 DB gate

Decision: implement the Phase 2 RW-heavy workload, compare command, rule-based
analyzer, and PyInstaller workflow while keeping real embedded PostgreSQL E2E
tests skipped unless `pgserver` is available.

Reason: the user explicitly approved continuing auto-build work, but the local
runtime still cannot install/start `pgserver`. Unit tests and dry-runs keep the
new contracts healthy without falsely claiming real DB verification.


## 2026-05-24 - Keep Phase 3 AI offline-first until provider calls are safe

Decision: implement BYOK setup/status and `sdb ai analyze` with deterministic
rule-based migration suggestions first, while deferring provider-backed network
AI enrichment.

Reason: Phase 3 should establish a stable advisory contract without exposing
keys, adding telemetry, or making unverified external calls. Suggestions remain
human-reviewed and are never auto-applied.


## 2026-05-24 - Keep Phase 4 security local-only and report-first

Decision: implement the security/isolation scenario only against embedded
ShadowDB and export reports to SARIF, JUnit XML, and a minimal dependency-free
PDF format.

Reason: Phase 4 should be testable in CI and safe by default. External DB
connections, production writes, telemetry, and polished PDF design are deferred
until the local contracts and report formats are stable.


## 2026-05-24 - Add safe local PostgreSQL fallback for Python 3.13+

Decision: keep embedded `pgserver` as the default experience where available,
but allow execute commands to use `--database-url` or `DATAWRAITH_DATABASE_URL`
when the URL targets localhost/loopback or a local socket.

Reason: `pgserver` still gates embedded execution to Python 3.12, which makes
the project harder to try on current runtimes. A local PostgreSQL fallback makes
DataWraith more accessible for contributors and GitHub users without weakening
the safety rule against accidental production database chaos testing.


## 2026-05-24 - Add GitHub landing page and fallback E2E for v1 testing

Decision: add a root `README.md`, `docker-compose.yml`, and a GitHub Actions
PostgreSQL fallback E2E job.

Reason: long-form project memory still belongs in `docs/`, but GitHub needs a
root README for discoverability. The Docker/CI fallback gives contributors a
repeatable way to test Phase 1-4 execute paths without waiting on Python 3.12
embedded `pgserver` availability.


## 2026-05-24 - Add recipe and quickstart UX shortcuts

Decision: add `sdb recipes` and `sdb quickstart` as first-class CLI commands,
and surface them at the top of the TUI.

Reason: scenario syntax is powerful but too long for first-time users to
memorize. Copy-paste recipes and a safe smoke-flow command reduce activation
friction without hiding the underlying expert commands.

## 2026-05-24 — Cloud PostgreSQL safety guidance

Decision: v1 documentation now explicitly states that Neon, Supabase, and other
hosted PostgreSQL services are conceptually compatible but not direct execution
targets. DataWraith remains local-only by default and rejects non-local URLs.

Rationale: chaos/security scenarios can create writes, locks, noisy logs, and
cost/traffic side effects. The safe workflow is to export schema-only cloud
PostgreSQL metadata, restore it into a local shadow PostgreSQL instance, seed
synthetic data, and run DataWraith locally.

Future option: add an explicit advanced remote-shadow mode only after designing
strong confirmation, allowlist/denylist, disposable-branch guidance, and secret
redaction safeguards.
