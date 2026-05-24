# DataWraith — Technical Blueprint E2E

> **Mục đích**: Tài liệu này dành cho **Claude Code** và **3 dev của 100B Studio** đọc để build DataWraith từ con số 0. Có đủ context để Claude Code generate code chuẩn xác mà không cần guess.
>
> **Loại**: Engineering blueprint, không phải product brief.
> **Phiên bản**: v1.0 (Phase 1 focus)
> **Cập nhật**: 21/05/2026

---

## Mục lục

1. [Context & Vai trò](#1-context--vai-trò)
2. [Repository Structure](#2-repository-structure)
3. [Core Dependencies & pyproject.toml](#3-core-dependencies--pyprojecttoml)
4. [Module API Contracts](#4-module-api-contracts)
5. [Data Models (Pydantic)](#5-data-models-pydantic)
6. [Engine Layer Specification](#6-engine-layer-specification)
7. [TUI Layer Specification](#7-tui-layer-specification)
8. [CLI Layer Specification](#8-cli-layer-specification)
9. [Output Layer Specification](#9-output-layer-specification)
10. [Shadow DB (pgserver Integration)](#10-shadow-db-pgserver-integration)
11. [Testing Strategy](#11-testing-strategy)
12. [CI/CD Pipeline](#12-cicd-pipeline)
13. [Phase 1 Build Order](#13-phase-1-build-order)
14. [CLAUDE.md Templates](#14-claudemd-templates)
15. [Error Handling Conventions](#15-error-handling-conventions)
16. [Logging & Telemetry](#16-logging--telemetry)
17. [Performance Targets](#17-performance-targets)
18. [Security Considerations](#18-security-considerations)
19. [Future Phases Roadmap](#19-future-phases-roadmap)

---

## 1. Context & Vai trò

### 1.1. Sản phẩm

**DataWraith** = PostgreSQL chaos-testing tool chạy local. User cài `pip install datawraith`, gõ `sdb` để mở TUI hoặc dùng sub-command cho CI/CD.

### 1.2. Team (3 dev)

| Dev | Module ownership | Branch | Stack mạnh |
|---|---|---|---|
| **Dev A** | `engine/` + `core/shadow_db.py` | `dev-a/engine` | asyncio, asyncpg, SQL |
| **Dev B** | `tui/` + `output/` | `dev-b/tui` | Textual, UI/UX |
| **Dev C** | `build/` + `ai/` (Phase 3+) | `dev-c/build` | DevOps, packaging |

### 1.3. Claude Code workflow

- Mỗi dev có 1 instance Claude Code chạy local trong branch của mình
- Đọc `CLAUDE.md` của module owned + brief này làm context
- PR sang `main` qua GitHub, Claude Code review trước merge
- Daily sync 15 phút, weekly architecture call 30 phút

### 1.4. Quy tắc bất di bất dịch

1. **Python 3.12+** only
2. **MIT License**, public repo từ Day 1
3. **No external services** (không SaaS, không hosted API)
4. **PostgreSQL only** Phase 1-4
5. **Async-first** cho I/O (asyncio)
6. **Pydantic 2** cho data models
7. **Type hints bắt buộc** (`from __future__ import annotations`)
8. **No print()** — dùng `logging` hoặc Textual log widget
9. **Test coverage > 70%** cho engine module

---

## 2. Repository Structure

```
datawraith/                         # Repo root
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Lint + test + build
│       ├── publish.yml             # Auto-publish to PyPI on tag
│       └── release.yml             # Build .exe artifacts (Phase 2+)
├── docs/                           # mkdocs-material site
│   ├── index.md
│   ├── quickstart.md
│   ├── scenarios/
│   └── api/
├── datawraith/                     # Python package
│   ├── __init__.py
│   ├── __main__.py                 # python -m datawraith
│   ├── cli.py                      # Typer entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic Settings
│   │   ├── shadow_db.py            # pgserver wrapper
│   │   ├── types.py                # Shared enums/types
│   │   └── exceptions.py           # Custom exceptions
│   ├── engine/                     # Dev A
│   │   ├── __init__.py
│   │   ├── CLAUDE.md
│   │   ├── runner.py               # Scenario orchestrator
│   │   ├── seeder.py               # Faker + mimesis
│   │   ├── analyzer.py             # pg_stat_statements parser
│   │   ├── schema_parser.py        # .sql -> DDL
│   │   └── scenarios/
│   │       ├── __init__.py
│   │       ├── base.py             # Scenario ABC class
│   │       ├── concurrency.py      # Phase 1
│   │       ├── rw_heavy.py         # Phase 2
│   │       ├── migration.py        # Phase 3
│   │       └── security.py         # Phase 4
│   ├── tui/                        # Dev B
│   │   ├── __init__.py
│   │   ├── CLAUDE.md
│   │   ├── app.py                  # Main Textual App
│   │   ├── theme.py                # Color tokens
│   │   ├── screens/
│   │   │   ├── splash.py
│   │   │   ├── init.py
│   │   │   ├── seed.py
│   │   │   ├── attack.py
│   │   │   └── report.py
│   │   └── widgets/
│   │       ├── log_panel.py
│   │       ├── metrics_chart.py
│   │       ├── culprits_table.py
│   │       └── ascii_wraith.py
│   ├── ai/                         # Dev C (Phase 3+)
│   │   ├── __init__.py
│   │   ├── CLAUDE.md
│   │   ├── bridge.py               # Main analyze() function
│   │   ├── prompts.py              # Prompt templates
│   │   └── providers/
│   │       ├── anthropic_provider.py
│   │       ├── openai_provider.py
│   │       ├── gemini_provider.py
│   │       └── ollama_provider.py
│   └── output/                     # Dev B
│       ├── __init__.py
│       ├── json_exporter.py
│       ├── sarif_exporter.py       # Phase 4
│       ├── junit_exporter.py       # Phase 4
│       ├── pdf_exporter.py         # Phase 4
│       └── ascii_renderer.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures
│   ├── test_shadow_db.py
│   ├── test_engine/
│   │   ├── test_concurrency.py
│   │   ├── test_seeder.py
│   │   └── test_analyzer.py
│   ├── test_tui/
│   │   └── test_app.py
│   ├── test_output/
│   │   └── test_json_exporter.py
│   └── fixtures/
│       ├── sample_schema.sql
│       └── sample_data.json
├── CLAUDE.md                       # Root context file
├── README.md
├── LICENSE                         # MIT
├── pyproject.toml
├── .gitignore
├── .python-version                 # 3.12
├── ruff.toml                       # Linting config
└── mkdocs.yml                      # Docs config
```

---

## 3. Core Dependencies & pyproject.toml

```toml
[project]
name = "datawraith"
version = "0.1.0"
description = "PostgreSQL chaos-testing tool — pip install, no Docker, no setup"
readme = "README.md"
authors = [
    { name = "100B Studio", email = "hello@datawraith.dev" }
]
license = { text = "MIT" }
requires-python = ">=3.12"
keywords = ["postgresql", "chaos-testing", "load-testing", "database", "tui"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Database",
    "Topic :: Software Development :: Testing",
]
dependencies = [
    "pgserver>=0.2.0",
    "psycopg[binary]>=3.2.0",
    "asyncpg>=0.30.0",
    "textual>=1.0.0",
    "typer>=0.12.0",
    "faker>=30.0.0",
    "mimesis>=18.0.0",
    "rich>=13.0.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "keyring>=25.0.0",                  # Secure API key storage
]

[project.optional-dependencies]
ai = [
    "openai>=1.50.0",
    "anthropic>=0.40.0",
    "google-generativeai>=0.8.0",
]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.7.0",
    "mypy>=1.11.0",
    "pyinstaller>=6.0.0",               # Phase 2+
    "textual-dev>=1.6.0",               # TUI dev tools
    "mkdocs-material>=9.5.0",
]

[project.scripts]
sdb = "datawraith.cli:app"
datawraith = "datawraith.cli:app"

[project.urls]
Homepage = "https://datawraith.dev"
Repository = "https://github.com/100b-studio/datawraith"
Documentation = "https://datawraith.dev/docs"
Issues = "https://github.com/100b-studio/datawraith/issues"

[build-system]
requires = ["hatchling>=1.25.0"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["datawraith"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --cov=datawraith --cov-report=term-missing"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "ASYNC", "UP"]
ignore = ["E501"]  # Handled by formatter

[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_configs = true
```

---

## 4. Module API Contracts

**Đây là phần quan trọng nhất**. Lock từ Tuần 1, không đổi giữa phase. Mọi module phải implement đúng signature.

### 4.1. Scenario interface (Engine)

```python
# datawraith/engine/scenarios/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import AsyncIterator
from datawraith.core.types import (
    ScenarioConfig, ScenarioResult, ScenarioEvent
)
from datawraith.core.shadow_db import ShadowDB


class Scenario(ABC):
    """Abstract base for all chaos test scenarios.
    
    Every scenario MUST:
    1. Accept ShadowDB instance + config
    2. Yield ScenarioEvent for live streaming to TUI
    3. Return final ScenarioResult
    4. Handle cleanup on exception
    """
    
    name: str  # Class attribute, e.g. "concurrency"
    display_name: str  # e.g. "Concurrency Test"
    
    def __init__(self, db: ShadowDB, config: ScenarioConfig):
        self.db = db
        self.config = config
    
    @abstractmethod
    async def run(self) -> AsyncIterator[ScenarioEvent]:
        """Execute scenario, yield events real-time.
        
        Last yielded event MUST be type=COMPLETED with result attached.
        """
        ...
    
    @abstractmethod
    def validate_config(self) -> list[str]:
        """Validate config before running. Return list of error messages.
        Empty list = valid.
        """
        ...
```

### 4.2. TUI ↔ Engine communication

```python
# Cách TUI gọi Engine
async def run_scenario(scenario_name: str, config: ScenarioConfig):
    db = ShadowDB()
    db.start()
    
    scenario_cls = SCENARIO_REGISTRY[scenario_name]
    scenario = scenario_cls(db, config)
    
    errors = scenario.validate_config()
    if errors:
        raise ConfigError(errors)
    
    try:
        async for event in scenario.run():
            yield event  # TUI consumes events
    finally:
        db.stop()
```

### 4.3. Output exporter interface

```python
# datawraith/output/base.py
from abc import ABC, abstractmethod
from pathlib import Path
from datawraith.core.types import ScenarioResult


class Exporter(ABC):
    format: str  # "json", "sarif", "junit", "pdf"
    extension: str  # ".json", ".sarif", ".xml", ".pdf"
    
    @abstractmethod
    def export(self, result: ScenarioResult, output_path: Path) -> None:
        ...
```

### 4.4. AI Bridge interface (Phase 3+)

```python
# datawraith/ai/bridge.py
from datawraith.core.types import ScenarioResult, AISuggestion


async def analyze(
    result: ScenarioResult,
    provider: str,  # "claude", "openai", "gemini", "ollama"
    api_key: str | None = None,
    ollama_url: str | None = None,
) -> AISuggestion:
    """Single entry point for AI analysis.
    
    Returns AISuggestion with:
    - reasoning: str
    - sql_fix: str | None
    - risk_level: Literal["low", "medium", "high"]
    - rollback_plan: str | None
    """
    ...
```

---

## 5. Data Models (Pydantic)

```python
# datawraith/core/types.py
from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class ScenarioType(StrEnum):
    CONCURRENCY = "concurrency"
    RW_HEAVY = "rw_heavy"
    MIGRATION = "migration"
    SECURITY = "security"


class EventType(StrEnum):
    STARTED = "started"
    LOG = "log"
    METRIC = "metric"
    WARNING = "warning"
    ERROR = "error"
    COMPLETED = "completed"


class Distribution(StrEnum):
    UNIFORM = "uniform"
    ZIPFIAN = "zipfian"
    REALISTIC = "realistic"


# === Config ===

class ScenarioConfig(BaseModel):
    """Base config for any scenario."""
    model_config = ConfigDict(frozen=True)
    
    duration_seconds: int = Field(default=60, ge=10, le=3600)
    workers: int = Field(default=100, ge=1, le=10000)
    target_qps: int | None = None
    

class ConcurrencyConfig(ScenarioConfig):
    """Phase 1 config."""
    concurrent_updates: int = Field(default=1000, ge=10, le=100000)
    target_table: str
    target_column: str
    isolation_level: Literal["read_committed", "repeatable_read", "serializable"] = "read_committed"


class RWHeavyConfig(ScenarioConfig):
    """Phase 2 config."""
    read_write_ratio: float = Field(default=0.7, ge=0.0, le=1.0)
    use_window_functions: bool = True
    use_multi_join: bool = True


# === Events (streamed during run) ===

class ScenarioEvent(BaseModel):
    """Streamed from scenario.run() to TUI."""
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    message: str | None = None
    data: dict | None = None


# === Result (final output) ===

class HealthMetrics(BaseModel):
    qps_max: float
    qps_avg: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    error_count: int
    error_rate: float
    deadlock_count: int = 0
    lock_wait_ms_total: float = 0.0
    connection_saturation_pct: float = 0.0


class Culprit(BaseModel):
    """A query/table that caused performance issue."""
    rank: int
    query_text: str
    impact_pct: float  # % of total time
    calls: int
    mean_exec_time_ms: float
    execution_plan: str  # ASCII-rendered EXPLAIN ANALYZE


class ScenarioResult(BaseModel):
    """Final output of a scenario run."""
    scenario_name: str
    scenario_type: ScenarioType
    config: dict  # Serialized config
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    health_score: int = Field(ge=0, le=100)
    metrics: HealthMetrics
    top_culprits: list[Culprit]
    raw_logs: list[str] = []  # Truncated for size


# === AI Bridge (Phase 3+) ===

class AISuggestion(BaseModel):
    provider: str
    model: str
    reasoning: str
    sql_fix: str | None = None
    risk_level: Literal["low", "medium", "high"]
    rollback_plan: str | None = None
    tokens_used: int | None = None
    cost_usd: float | None = None
```

---

## 6. Engine Layer Specification

### 6.1. Scenario Registry

```python
# datawraith/engine/scenarios/__init__.py
from datawraith.engine.scenarios.base import Scenario
from datawraith.engine.scenarios.concurrency import ConcurrencyScenario
# Phase 2-4:
# from datawraith.engine.scenarios.rw_heavy import RWHeavyScenario
# from datawraith.engine.scenarios.migration import MigrationScenario
# from datawraith.engine.scenarios.security import SecurityScenario


SCENARIO_REGISTRY: dict[str, type[Scenario]] = {
    "concurrency": ConcurrencyScenario,
    # Phase 2-4 will register here
}


def get_scenario(name: str) -> type[Scenario]:
    if name not in SCENARIO_REGISTRY:
        available = list(SCENARIO_REGISTRY.keys())
        raise ValueError(f"Unknown scenario '{name}'. Available: {available}")
    return SCENARIO_REGISTRY[name]
```

### 6.2. Concurrency Scenario (Phase 1 — chi tiết)

```python
# datawraith/engine/scenarios/concurrency.py
from __future__ import annotations
import asyncio
import asyncpg
import random
import time
from typing import AsyncIterator
from datetime import datetime
from datawraith.engine.scenarios.base import Scenario
from datawraith.core.types import (
    ConcurrencyConfig, ScenarioEvent, EventType,
    ScenarioResult, HealthMetrics, Culprit, ScenarioType
)


class ConcurrencyScenario(Scenario):
    """Race condition + deadlock detection.
    
    Pattern: N workers concurrently UPDATE same rows.
    Detects: deadlocks, lock waits, MVCC bloat, rollback rate.
    """
    
    name = "concurrency"
    display_name = "Concurrency Test"
    
    def __init__(self, db, config: ConcurrencyConfig):
        super().__init__(db, config)
        self.config: ConcurrencyConfig = config  # Type narrow
        self._stats = {
            "completed": 0,
            "errors": 0,
            "deadlocks": 0,
            "latencies_ms": [],
        }
    
    def validate_config(self) -> list[str]:
        errors = []
        if self.config.workers < 2:
            errors.append("Need at least 2 workers for concurrency test")
        if not self.config.target_table:
            errors.append("target_table is required")
        return errors
    
    async def run(self) -> AsyncIterator[ScenarioEvent]:
        started_at = datetime.now()
        
        yield ScenarioEvent(
            type=EventType.STARTED,
            message=f"Starting {self.config.workers} workers on {self.config.target_table}"
        )
        
        # Enable pg_stat_statements
        await self._enable_extensions()
        
        # Get initial state
        baseline = await self._get_baseline()
        yield ScenarioEvent(
            type=EventType.LOG,
            message=f"Baseline: {baseline['row_count']} rows, "
                    f"{baseline['table_size_mb']:.1f}MB"
        )
        
        # Spawn workers
        deadline = time.time() + self.config.duration_seconds
        worker_tasks = [
            self._worker(worker_id, deadline)
            for worker_id in range(self.config.workers)
        ]
        
        # Stream metrics every 1s while workers running
        metrics_task = asyncio.create_task(
            self._stream_metrics(deadline)
        )
        
        # Run all workers concurrently
        async for event in self._gather_with_events(worker_tasks):
            yield event
        
        metrics_task.cancel()
        
        # Compute final result
        completed_at = datetime.now()
        result = await self._build_result(started_at, completed_at)
        
        yield ScenarioEvent(
            type=EventType.COMPLETED,
            data={"result": result.model_dump()}
        )
    
    async def _enable_extensions(self):
        async with self.db.connection() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")
    
    async def _get_baseline(self) -> dict:
        async with self.db.connection() as conn:
            row = await conn.fetchrow(f"""
                SELECT 
                    COUNT(*) as row_count,
                    pg_total_relation_size('{self.config.target_table}'::regclass) / 1024.0 / 1024.0 as table_size_mb
                FROM {self.config.target_table}
            """)
            return dict(row)
    
    async def _worker(self, worker_id: int, deadline: float):
        """Single worker performing concurrent UPDATEs."""
        pool = await asyncpg.create_pool(
            self.db.get_uri(),
            min_size=1, max_size=2
        )
        
        try:
            while time.time() < deadline:
                start = time.time()
                try:
                    async with pool.acquire() as conn:
                        # Pick random row
                        target_id = random.randint(1, 1000)
                        
                        await conn.execute(f"""
                            UPDATE {self.config.target_table}
                            SET {self.config.target_column} = 
                                {self.config.target_column} + 1
                            WHERE id = $1
                        """, target_id)
                    
                    latency_ms = (time.time() - start) * 1000
                    self._stats["latencies_ms"].append(latency_ms)
                    self._stats["completed"] += 1
                    
                except asyncpg.DeadlockDetectedError:
                    self._stats["deadlocks"] += 1
                    self._stats["errors"] += 1
                except Exception:
                    self._stats["errors"] += 1
        finally:
            await pool.close()
    
    async def _stream_metrics(self, deadline: float):
        """Yield METRIC events every 1s."""
        # Implementation: read self._stats, yield via queue
        # Detail: needs proper async queue to TUI
        ...
    
    async def _gather_with_events(self, tasks):
        """Run tasks, yield WARNING/ERROR events as they occur."""
        ...
    
    async def _build_result(self, started_at, completed_at) -> ScenarioResult:
        """Compute final ScenarioResult."""
        latencies = sorted(self._stats["latencies_ms"])
        n = len(latencies)
        
        metrics = HealthMetrics(
            qps_max=max(self._stats["completed"] / (completed_at - started_at).total_seconds(), 0),
            qps_avg=self._stats["completed"] / (completed_at - started_at).total_seconds(),
            latency_p50_ms=latencies[n // 2] if n else 0,
            latency_p95_ms=latencies[int(n * 0.95)] if n else 0,
            latency_p99_ms=latencies[int(n * 0.99)] if n else 0,
            error_count=self._stats["errors"],
            error_rate=self._stats["errors"] / max(self._stats["completed"], 1),
            deadlock_count=self._stats["deadlocks"],
        )
        
        # Health score: 100 - (error_rate * 50) - (deadlock_count * 2)
        health_score = max(0, int(100 - metrics.error_rate * 50 - metrics.deadlock_count * 2))
        
        # Top culprits from pg_stat_statements
        top_culprits = await self._get_top_culprits()
        
        return ScenarioResult(
            scenario_name=self.name,
            scenario_type=ScenarioType.CONCURRENCY,
            config=self.config.model_dump(),
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
            health_score=health_score,
            metrics=metrics,
            top_culprits=top_culprits,
        )
    
    async def _get_top_culprits(self) -> list[Culprit]:
        """Query pg_stat_statements for top slow queries."""
        async with self.db.connection() as conn:
            rows = await conn.fetch("""
                SELECT 
                    query,
                    calls,
                    mean_exec_time,
                    total_exec_time
                FROM pg_stat_statements
                WHERE query NOT LIKE '%pg_stat_statements%'
                ORDER BY total_exec_time DESC
                LIMIT 5
            """)
            
            total_time = sum(r["total_exec_time"] for r in rows) or 1
            
            culprits = []
            for rank, row in enumerate(rows, 1):
                # Get execution plan
                plan = await self._get_execution_plan(conn, row["query"])
                
                culprits.append(Culprit(
                    rank=rank,
                    query_text=row["query"][:200],  # Truncate
                    impact_pct=(row["total_exec_time"] / total_time) * 100,
                    calls=row["calls"],
                    mean_exec_time_ms=row["mean_exec_time"],
                    execution_plan=plan,
                ))
            
            return culprits
    
    async def _get_execution_plan(self, conn, query: str) -> str:
        """Get EXPLAIN ANALYZE for query."""
        try:
            rows = await conn.fetch(f"EXPLAIN (ANALYZE, FORMAT TEXT) {query}")
            return "\n".join(r["QUERY PLAN"] for r in rows)
        except Exception:
            return "Unable to generate execution plan"
```

### 6.3. Seeder

```python
# datawraith/engine/seeder.py
from __future__ import annotations
import asyncpg
from faker import Faker
from mimesis import Generic
from datawraith.core.shadow_db import ShadowDB
from datawraith.core.types import Distribution


class Seeder:
    """Generate realistic test data into Shadow DB."""
    
    def __init__(self, db: ShadowDB):
        self.db = db
        self.fake = Faker()
        self.mimesis = Generic()
    
    async def seed_table(
        self,
        table: str,
        row_count: int,
        distribution: Distribution = Distribution.UNIFORM,
        batch_size: int = 10_000,
    ) -> int:
        """Insert N rows with given distribution.
        
        Returns actual rows inserted.
        """
        # Inspect table schema
        columns = await self._get_columns(table)
        
        inserted = 0
        async with self.db.connection() as conn:
            for batch_start in range(0, row_count, batch_size):
                batch_end = min(batch_start + batch_size, row_count)
                batch = self._generate_batch(columns, batch_end - batch_start, distribution)
                
                # Use COPY for speed
                await conn.copy_records_to_table(
                    table,
                    records=batch,
                    columns=[c["name"] for c in columns if c["name"] != "id"]
                )
                inserted += len(batch)
        
        return inserted
    
    async def _get_columns(self, table: str) -> list[dict]:
        """Get column info from information_schema."""
        async with self.db.connection() as conn:
            rows = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = $1
                ORDER BY ordinal_position
            """, table)
            return [dict(r) for r in rows]
    
    def _generate_batch(self, columns, size, distribution) -> list[tuple]:
        """Generate batch using mimesis (faster) for bulk."""
        # Implementation: column name → generator mapping
        # email → mimesis.person.email()
        # name → mimesis.person.full_name()
        # phone → mimesis.person.telephone()
        # date → distribution-aware date gen
        # ...
        ...
```

### 6.4. Analyzer

```python
# datawraith/engine/analyzer.py
"""Parse pg_stat_statements + pg_qualstats to find culprits.

For Phase 1: just rank by total_exec_time.
For Phase 2+: use pg_qualstats for index recommendations (rule-based, NO AI).
"""
```

---

## 7. TUI Layer Specification

### 7.1. Theme tokens

```python
# datawraith/tui/theme.py
"""Lofi cyberpunk color palette."""

COLORS = {
    "primary": "#B26AFF",       # Purple neon
    "secondary": "#00D4FF",     # Cyan
    "background": "#0A0E27",    # Dark navy
    "surface": "#151933",       # Slightly lighter navy
    "text": "#E0E6F0",          # Off-white
    "text_dim": "#7080A0",      # Muted blue-gray
    "success": "#00FF94",       # Neon green
    "warning": "#FFB800",       # Amber
    "error": "#FF4D6D",         # Hot pink
}

CSS = f"""
Screen {{
    background: {COLORS["background"]};
    color: {COLORS["text"]};
}}

Header {{
    background: {COLORS["primary"]};
    color: {COLORS["background"]};
}}

Footer {{
    background: {COLORS["surface"]};
}}

.metrics-card {{
    background: {COLORS["surface"]};
    border: tall {COLORS["primary"]};
}}

.log-line {{
    color: {COLORS["text_dim"]};
}}

.log-line-error {{
    color: {COLORS["error"]};
}}

.culprit-row {{
    background: {COLORS["surface"]};
}}
"""
```

### 7.2. App skeleton

```python
# datawraith/tui/app.py
from __future__ import annotations
from textual.app import App
from textual.binding import Binding
from datawraith.tui.screens.splash import SplashScreen
from datawraith.tui.theme import CSS


class DataWraithApp(App):
    """Main TUI application."""
    
    CSS = CSS
    TITLE = "DataWraith"
    SUB_TITLE = "PostgreSQL Chaos-Testing"
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("f1", "help", "Help"),
        Binding("f2", "pause", "Pause"),
        Binding("f3", "stop", "Stop"),
        Binding("f4", "export", "Export"),
    ]
    
    async def on_mount(self):
        await self.push_screen(SplashScreen())
```

### 7.3. Screen flow

```
SplashScreen (3s auto-advance)
    ↓
InitScreen (chọn schema file)
    ↓
SeedScreen (chọn rows + distribution)
    ↓
AttackScreen (chọn scenario)
    ↓
RunScreen (LIVE: log panel + metrics chart + culprits)
    ↓
ReportScreen (final result, export options)
```

### 7.4. Widgets cần build (Phase 1)

| Widget | File | Mục đích |
|---|---|---|
| `LogPanel` | `widgets/log_panel.py` | Scrollable log với syntax highlight |
| `MetricsChart` | `widgets/metrics_chart.py` | Real-time line chart (QPS, latency) |
| `CulpritsTable` | `widgets/culprits_table.py` | Top 3-5 slow queries table |
| `AsciiWraith` | `widgets/ascii_wraith.py` | Loading animation |

---

## 8. CLI Layer Specification

```python
# datawraith/cli.py
from __future__ import annotations
import typer
from pathlib import Path
from typing import Annotated
from datawraith.tui.app import DataWraithApp

app = typer.Typer(
    name="sdb",
    help="DataWraith — PostgreSQL chaos-testing tool",
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Open TUI if no sub-command given."""
    if ctx.invoked_subcommand is None:
        DataWraithApp().run()


@app.command()
def init(
    schema: Annotated[Path, typer.Argument(help="Path to .sql schema file")],
):
    """Initialize shadow DB from schema file."""
    typer.echo(f"Loading schema from {schema}")
    # Implementation


@app.command()
def seed(
    rows: Annotated[int, typer.Option(help="Number of rows")] = 100_000,
    distribution: Annotated[str, typer.Option(help="Data distribution")] = "uniform",
):
    """Seed shadow DB with test data."""
    typer.echo(f"Seeding {rows} rows with {distribution} distribution")
    # Implementation


@app.command()
def attack(
    scenario: Annotated[str, typer.Argument(help="Scenario name")],
    duration: Annotated[int, typer.Option(help="Duration in seconds")] = 60,
    workers: Annotated[int, typer.Option(help="Concurrent workers")] = 100,
    output: Annotated[Path | None, typer.Option(help="Export JSON to")] = None,
    headless: Annotated[bool, typer.Option(help="No TUI, just run")] = False,
):
    """Run chaos test scenario."""
    # Phase 1: concurrency only
    # Phase 2+: rw_heavy, migration, security


@app.command()
def doctor():
    """Health check: verify pgserver, ports, permissions."""
    # Implementation


@app.command()
def version():
    """Print version."""
    from datawraith import __version__
    typer.echo(f"DataWraith {__version__}")


if __name__ == "__main__":
    app()
```

---

## 9. Output Layer Specification

### 9.1. JSON Exporter (Phase 1)

```python
# datawraith/output/json_exporter.py
from __future__ import annotations
import json
from pathlib import Path
from datawraith.core.types import ScenarioResult
from datawraith.output.base import Exporter


class JSONExporter(Exporter):
    format = "json"
    extension = ".json"
    
    def export(self, result: ScenarioResult, output_path: Path) -> None:
        with output_path.open("w") as f:
            json.dump(
                result.model_dump(mode="json"),
                f,
                indent=2,
                default=str,
            )
```

### 9.2. ASCII Renderer (Phase 1)

```python
# datawraith/output/ascii_renderer.py
"""Render ScenarioResult as ASCII for terminal display."""

def render_result(result: ScenarioResult) -> str:
    """Generate ASCII art summary."""
    lines = [
        f"━━━ {result.scenario_name.upper()} ━━━",
        f"Duration: {result.duration_seconds:.1f}s",
        f"Health Score: {result.health_score}/100",
        "",
        "Metrics:",
        f"  QPS (avg/max):   {result.metrics.qps_avg:.0f} / {result.metrics.qps_max:.0f}",
        f"  Latency p99:     {result.metrics.latency_p99_ms:.1f}ms",
        f"  Errors:          {result.metrics.error_count}",
        f"  Deadlocks:       {result.metrics.deadlock_count}",
        "",
        "Top Culprits:",
    ]
    for c in result.top_culprits[:3]:
        lines.append(f"  {c.rank}. {c.query_text[:60]}... ({c.impact_pct:.1f}%)")
    
    return "\n".join(lines)
```

---

## 10. Shadow DB (pgserver Integration)

```python
# datawraith/core/shadow_db.py
from __future__ import annotations
import pgserver
import psycopg
import tempfile
import asyncio
import shutil
from pathlib import Path
from contextlib import asynccontextmanager, contextmanager
from datawraith.core.exceptions import ShadowDBError


class ShadowDB:
    """Embedded PostgreSQL via pgserver.
    
    Production-tested wrapper. Always use as context manager:
    
    ```python
    with ShadowDB() as db:
        await db.load_schema(sql)
        async with db.connection() as conn:
            await conn.execute("SELECT 1")
    ```
    """
    
    def __init__(
        self,
        data_dir: Path | None = None,
        cleanup_mode: str = "stop",
    ):
        """Initialize shadow DB.
        
        Args:
            data_dir: Where to store PG data. Default: temp dir.
            cleanup_mode: 'stop' (keep data) | 'delete' (remove on exit)
        """
        self._data_dir = data_dir or Path(tempfile.mkdtemp(prefix="datawraith_"))
        self._cleanup_mode = cleanup_mode
        self._server: pgserver.PostgresServer | None = None
        self._uri: str | None = None
    
    def start(self) -> str:
        """Start embedded PG, return connection URI.
        
        Raises:
            ShadowDBError: if PG fails to start.
        """
        try:
            self._server = pgserver.get_server(
                self._data_dir,
                cleanup_mode=self._cleanup_mode
            )
            self._uri = self._server.get_uri()
            
            # Verify connection works
            with psycopg.connect(self._uri, connect_timeout=5) as conn:
                conn.execute("SELECT 1")
            
            return self._uri
        except Exception as e:
            raise ShadowDBError(f"Failed to start shadow DB: {e}") from e
    
    def stop(self):
        """Stop PG and optionally clean up."""
        if self._server:
            try:
                self._server.cleanup()
            except Exception:
                pass
            self._server = None
        
        if self._cleanup_mode == "delete" and self._data_dir.exists():
            shutil.rmtree(self._data_dir, ignore_errors=True)
    
    def get_uri(self) -> str:
        """Get connection URI. Must call start() first."""
        if not self._uri:
            raise ShadowDBError("Shadow DB not started. Call start() first.")
        return self._uri
    
    @contextmanager
    def sync_connection(self):
        """Sync psycopg connection."""
        with psycopg.connect(self.get_uri()) as conn:
            yield conn
    
    @asynccontextmanager
    async def connection(self):
        """Async psycopg connection."""
        async with await psycopg.AsyncConnection.connect(self.get_uri()) as conn:
            yield conn
    
    async def load_schema(self, sql: str):
        """Execute DDL to set up schema."""
        async with self.connection() as conn:
            await conn.execute(sql)
    
    async def enable_extension(self, name: str):
        """Enable PG extension."""
        async with self.connection() as conn:
            await conn.execute(f"CREATE EXTENSION IF NOT EXISTS {name}")
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
```

---

## 11. Testing Strategy

### 11.1. Test pyramid

- **Unit tests** (60%): pure logic, no DB
- **Integration tests** (30%): với real pgserver instance
- **E2E tests** (10%): full scenario chạy end-to-end

### 11.2. Shared fixtures

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from pathlib import Path
from datawraith.core.shadow_db import ShadowDB


@pytest_asyncio.fixture
async def shadow_db():
    """Fresh shadow DB per test."""
    db = ShadowDB(cleanup_mode="delete")
    db.start()
    yield db
    db.stop()


@pytest_asyncio.fixture
async def seeded_db(shadow_db):
    """Shadow DB with sample schema + data."""
    schema = Path("tests/fixtures/sample_schema.sql").read_text()
    await shadow_db.load_schema(schema)
    # Seed 1000 rows
    yield shadow_db
```

### 11.3. Sample test

```python
# tests/test_engine/test_concurrency.py
import pytest
from datawraith.engine.scenarios.concurrency import ConcurrencyScenario
from datawraith.core.types import ConcurrencyConfig, EventType


@pytest.mark.asyncio
async def test_concurrency_basic(seeded_db):
    config = ConcurrencyConfig(
        duration_seconds=5,
        workers=10,
        concurrent_updates=100,
        target_table="products",
        target_column="stock",
    )
    
    scenario = ConcurrencyScenario(seeded_db, config)
    
    events = []
    async for event in scenario.run():
        events.append(event)
    
    # Must end with COMPLETED event
    assert events[-1].type == EventType.COMPLETED
    
    # Result has metrics
    result_data = events[-1].data["result"]
    assert result_data["health_score"] >= 0
    assert result_data["health_score"] <= 100
```

---

## 12. CI/CD Pipeline

### 12.1. `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, dev-*]
  pull_request:
    branches: [main]

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.12", "3.13"]
    
    runs-on: ${{ matrix.os }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Lint with ruff
        run: ruff check .
      
      - name: Type check
        run: mypy datawraith
      
      - name: Run tests
        run: pytest -v --cov=datawraith
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

### 12.2. `.github/workflows/publish.yml`

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # OIDC publish to PyPI
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Build
        run: |
          pip install build
          python -m build
      
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

---

## 13. Phase 1 Build Order

### Tuần 1: Foundation

**Day 1 (Cả team)**:
- [ ] Repo setup, MIT LICENSE, README skeleton
- [ ] pyproject.toml lock-in
- [ ] CI skeleton
- [ ] Lock all module API contracts (Section 4 này)

**Day 2-7 — Parallel work**:

**Dev A**:
- [ ] `core/shadow_db.py` (pgserver wrapper)
- [ ] `core/types.py` (all Pydantic models)
- [ ] `core/exceptions.py`
- [ ] Test: spin up pgserver, load sample schema, query

**Dev B**:
- [ ] `tui/theme.py` (colors + CSS)
- [ ] `tui/app.py` (skeleton)
- [ ] `tui/screens/splash.py` (3s splash)
- [ ] Test: `python -m datawraith` opens TUI

**Dev C**:
- [ ] pyproject.toml hoàn chỉnh
- [ ] `.github/workflows/ci.yml`
- [ ] TestPyPI setup
- [ ] `cli.py` skeleton với Typer

### Tuần 2: Init + Seed

**Dev A**:
- [ ] `engine/schema_parser.py`
- [ ] `engine/seeder.py` (Faker + mimesis)
- [ ] Test: seed 10K rows trong < 5s

**Dev B**:
- [ ] `tui/screens/init.py`
- [ ] `tui/screens/seed.py`
- [ ] File picker widget cho schema selection

**Dev C**:
- [ ] `cli.py` commands: init, seed
- [ ] Documentation site (mkdocs)
- [ ] Cloudflare Pages deploy

### Tuần 3-4: Concurrency Scenario

**Dev A**:
- [ ] `engine/scenarios/base.py` (Scenario ABC)
- [ ] `engine/scenarios/concurrency.py` (full implementation)
- [ ] `engine/analyzer.py` (pg_stat_statements parser)
- [ ] Stream events via asyncio.Queue

**Dev B**:
- [ ] `tui/widgets/log_panel.py`
- [ ] `tui/widgets/metrics_chart.py`
- [ ] `tui/widgets/culprits_table.py`
- [ ] `tui/screens/attack.py`

**Dev C**:
- [ ] `cli.py` command: attack
- [ ] CI matrix expand (Win/Mac/Linux)
- [ ] Release pipeline test

### Tuần 5: Output + Polish

**Dev A**:
- [ ] Edge cases: stuck queries, OOM, connection drop
- [ ] Performance tuning

**Dev B**:
- [ ] `output/json_exporter.py`
- [ ] `tui/screens/report.py`
- [ ] `tui/widgets/ascii_wraith.py` (animation)

**Dev C**:
- [ ] Alpha release v0.1.0-alpha → TestPyPI
- [ ] Smoke test on Win/Mac/Linux

### Tuần 6: Bug bash + Release

**All devs**:
- [ ] Bug fix marathon
- [ ] Documentation polish
- [ ] Demo GIF recording
- [ ] Landing page deploy
- [ ] **v0.1.0 release → PyPI + GitHub**
- [ ] Launch tweet

---

## 14. CLAUDE.md Templates

### 14.1. Root `/CLAUDE.md`

```markdown
# DataWraith — Claude Code Context

## Project
PostgreSQL chaos-testing tool. pip-installable. Embedded PG via pgserver. MIT.

## My role in this codebase
[Dev A / Dev B / Dev C — fill in]

## Stack lock-in
- Python 3.12+
- pgserver (embedded PG)
- psycopg 3 + asyncpg
- Textual (TUI)
- Typer (CLI)
- Pydantic 2 (models)

## Quy tắc
- async-first cho I/O
- type hints bắt buộc
- không print(), dùng logging hoặc Textual log
- Pydantic 2 cho data models
- ruff + mypy strict

## Module ownership
- Dev A: engine/, core/shadow_db.py
- Dev B: tui/, output/
- Dev C: build/, ai/ (Phase 3+)

## Đọc thêm
- @datawraith/engine/CLAUDE.md (nếu là Dev A)
- @datawraith/tui/CLAUDE.md (nếu là Dev B)
- Blueprint E2E: @docs/blueprint.md
```

### 14.2. `datawraith/engine/CLAUDE.md`

```markdown
# Engine Module — Dev A's Domain

## Responsibility
4 chaos test scenarios + shadow DB management + seeding + analysis.

## Files I own
- engine/runner.py
- engine/seeder.py
- engine/analyzer.py
- engine/schema_parser.py
- engine/scenarios/base.py
- engine/scenarios/concurrency.py (Phase 1)
- engine/scenarios/rw_heavy.py (Phase 2)
- engine/scenarios/migration.py (Phase 3)
- engine/scenarios/security.py (Phase 4)
- core/shadow_db.py

## API contracts (LOCK — không đổi)
Every Scenario MUST implement:
- name: str (class attr)
- display_name: str (class attr)
- validate_config() -> list[str]
- async run() -> AsyncIterator[ScenarioEvent]
- Last event MUST be EventType.COMPLETED with result attached

## Performance targets
- Concurrency: 1000+ workers chạy mượt
- Seeder: 100K rows/sec với COPY
- Shadow DB spinup: < 5 seconds

## Anti-patterns
- KHÔNG dùng SQLAlchemy ORM (chậm cho stress test)
- KHÔNG block event loop (mọi I/O phải async)
- KHÔNG print() trong scenario.run() (dùng yield event)
```

### 14.3. `datawraith/tui/CLAUDE.md`

```markdown
# TUI Module — Dev B's Domain

## Responsibility
Textual TUI app + lofi cyberpunk aesthetic + output rendering.

## Files I own
- tui/app.py
- tui/theme.py
- tui/screens/* (splash, init, seed, attack, report)
- tui/widgets/* (log_panel, metrics_chart, culprits_table, ascii_wraith)
- output/json_exporter.py
- output/ascii_renderer.py
- output/* (Phase 4: sarif, junit, pdf)

## Theme tokens (LOCK)
- Primary: #B26AFF (purple neon)
- Secondary: #00D4FF (cyan)
- Background: #0A0E27 (dark navy)

## Screen flow
splash → init → seed → attack → run → report

## API contracts với Engine
- Consume AsyncIterator[ScenarioEvent] từ scenario.run()
- Render real-time: log events → LogPanel, metric events → MetricsChart
- Final COMPLETED event → ReportScreen

## Anti-patterns
- KHÔNG block UI thread
- KHÔNG hardcode colors, dùng theme.py
- KHÔNG dùng print(), dùng self.log() trong Textual
```

### 14.4. `datawraith/ai/CLAUDE.md` (Phase 3+)

```markdown
# AI Module — Dev C's Domain (Phase 3+)

## Responsibility
Simple AI bridge for analyzing ScenarioResult. BYOK only.

## Philosophy
- KHÔNG over-engineer
- KHÔNG dùng LangChain, LiteLLM, multi-provider router
- 1 LLM call per analysis
- User chọn 1 provider, nhập 1 key, dùng

## Files I own
- ai/bridge.py (main entry: analyze())
- ai/prompts.py (prompt templates)
- ai/providers/* (claude, openai, gemini, ollama)

## Key storage
- Sử dụng `keyring` để lưu API key encrypted vào OS keyring
- KHÔNG lưu plaintext trong config file

## API contract
async def analyze(
    result: ScenarioResult,
    provider: str,
    api_key: str | None = None,
    ollama_url: str | None = None,
) -> AISuggestion

## Anti-patterns
- KHÔNG ship API key sẵn (BYOK 100%)
- KHÔNG cache LLM response giữa runs (privacy)
- KHÔNG log API key vào file
```

---

## 15. Error Handling Conventions

```python
# datawraith/core/exceptions.py
"""Custom exceptions hierarchy."""


class DataWraithError(Exception):
    """Base for all DataWraith errors."""


class ShadowDBError(DataWraithError):
    """pgserver / shadow DB issues."""


class SchemaError(DataWraithError):
    """Schema parsing/loading issues."""


class SeederError(DataWraithError):
    """Data generation issues."""


class ScenarioError(DataWraithError):
    """Scenario execution issues."""


class ConfigError(DataWraithError):
    """Invalid configuration."""
    
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


class AIBridgeError(DataWraithError):
    """AI provider issues (Phase 3+)."""
```

**Quy tắc**:
- KHÔNG catch `Exception` generic, catch specific
- Mọi exception phải có context message rõ ràng
- User-facing errors phải friendly (không stack trace) — UI layer handle

---

## 16. Logging & Telemetry

```python
# datawraith/core/logging.py
import logging
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: Path | None = None):
    """Setup logging với rich formatter."""
    from rich.logging import RichHandler
    
    handlers = [RichHandler(rich_tracebacks=True)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers,
    )
```

**Quy tắc telemetry**:
- KHÔNG gửi data về 100B Studio
- KHÔNG track user behavior
- Log file local only (`~/.datawraith/logs/`)
- User có thể `--no-log` để tắt hoàn toàn

---

## 17. Performance Targets

| Operation | Target | Phase |
|---|---|---|
| pgserver spinup | < 5s | Phase 1 |
| Seed 100K rows | < 10s | Phase 1 |
| Concurrency 1000 workers, 60s | Run without crash | Phase 1 |
| TUI render | 60 FPS smooth | Phase 1 |
| Wheel size | < 50MB | Phase 1 |
| Wheel + pgserver | < 200MB | Phase 1 |
| Cold start `sdb` | < 2s | Phase 1 |
| .exe size | < 200MB | Phase 2 |
| .exe cold start | < 5s | Phase 2 |

---

## 18. Security Considerations

### 18.1. Threat model

| Threat | Mitigation |
|---|---|
| User connect DataWraith vào production DB | `--prevent-prod` flag default ON, từ chối DB không có suffix `_shadow`/`_test` |
| API key leak vào log | Mask key trong logs, dùng keyring để store |
| Malicious SQL injection vào seeder | Use parameterized queries, validate schema before seed |
| Shadow DB exposed lên network | Bind chỉ localhost (127.0.0.1) hoặc Unix socket |
| pgserver binary có CVE | Auto-update khi pgserver release, subscribe security mailing list |
| User's data sent to LLM | PII redaction trước khi gửi (Phase 3+), opt-in only |

### 18.2. Privacy

- KHÔNG telemetry
- KHÔNG analytics
- KHÔNG send data về 100B Studio
- API keys lưu trong OS keyring (encrypted)
- Logs lưu local, có thể tắt

---

## 19. Future Phases Roadmap

### Phase 2 (v0.2): R/W Heavy + CLI Headless + .exe

- New scenario: `rw_heavy`
- Headless CLI mode: `sdb attack rw-heavy --no-tui --output result.json`
- Compare runs feature
- PyInstaller `.exe` build
- Rule-based index recommendation từ pg_qualstats

### Phase 3 (v0.3): Migration Lock + AI BYOK

- New scenario: `migration`
- AI Mode (BYOK): single LLM call analyzer
- Settings screen cho API key
- Popup nhắc user lần đầu

### Phase 4 (v1.0): Security + Multi-export

- New scenario: `security`
- SARIF / JUnit / PDF export
- v1.0 stable release
- Show HN + Product Hunt launch

### Phase 5+ (post-v1.0): Full Agentic + Multi-DB

- Full Agentic loop (PLAN → EXECUTE → OBSERVE → REFLECT → FIX → VERIFY)
- MCP server cho Claude Desktop / Cursor
- Multi-DB (MySQL, MongoDB, SQLite)
- Hosted CI runner (Pro tier)
- 100B Studio's fine-tuned model (Subscription tier)

---

## Phụ Lục — Quick Start cho Claude Code

Khi bắt đầu session Claude Code, đọc:

1. **Root `/CLAUDE.md`** — context tổng
2. **Module `CLAUDE.md`** của dev mình (engine/, tui/, hoặc build/)
3. **Blueprint này** (`docs/blueprint.md`) — kỹ thuật chi tiết
4. **Brief markdown** (`docs/brief.md`) — product context

### Câu lệnh khởi đầu cho Claude Code

**Dev A (Engine)**:
> Đọc `CLAUDE.md`, `datawraith/engine/CLAUDE.md`, và section 6 + 10 của blueprint. Tôi đang làm `engine/scenarios/concurrency.py`. Implement theo API contract section 4.1.

**Dev B (TUI)**:
> Đọc `CLAUDE.md`, `datawraith/tui/CLAUDE.md`, và section 7 của blueprint. Tôi đang làm `tui/screens/attack.py`. Theme tokens trong `theme.py`, consume events từ scenario theo API section 4.2.

**Dev C (Build)**:
> Đọc `CLAUDE.md`, section 3 + 8 + 12 của blueprint. Tôi đang setup CI/CD pipeline. pyproject.toml ở section 3, workflows ở section 12.

---

## Tổng Kết

Blueprint này là **single source of truth** cho engineering của DataWraith Phase 1. Mọi quyết định kỹ thuật đều có trong này. Khi anything ambiguous, hỏi trong daily sync trước khi guess.

**Quy tắc vàng**: 
- Module API contracts (Section 4) là **LOCK**, không tự ý đổi
- Performance targets (Section 17) là **REQUIREMENT**, không phải nice-to-have
- Anti-patterns trong từng CLAUDE.md là **HARD RULE**, vi phạm = revert PR

Built by 100B Studio with Claude Code. MIT License. Have fun.

---

*Tài liệu kỹ thuật · 100B Studio · DataWraith Engineering Blueprint v1.0*
