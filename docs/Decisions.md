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
