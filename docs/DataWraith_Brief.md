# DataWraith — Project Brief v5.0 (Final)

> **Database Chaos-Testing Tool for PostgreSQL**
> pip-installable · Embedded PostgreSQL · Engine-first · BYOK AI · MIT License
> Phiên bản: v5.0 · Cập nhật: 21/05/2026 · 100B Studio

---

## Quick Facts

| | |
|---|---|
| **Tên sản phẩm** | DataWraith |
| **Terminal alias** | `sdb` (Shadow DB) |
| **Team** | 3 dev của 100B Studio (50-70% time) |
| **Workflow** | Claude Code rush · Module ownership rõ ràng |
| **Distribution chính** | **`pip install datawraith`** (Phase 1+) |
| **Distribution phụ** | `.exe` standalone (Phase 2+) |
| **Test method nội bộ** | `pip install -e .` cho dev, `.exe` build từ Phase 2 |
| **Embedded PostgreSQL** | **`pgserver`** (pip-installable, cross-platform) |
| **Mục tiêu 6 tháng** | OSS viral + portfolio cho 100B Studio |
| **AI strategy** | BYOK 100% — user tự cấp key (Phase 3+) |
| **Roadmap** | 4 phase = 4 scenarios. **No deadline**. Ship khi sẵn sàng. |
| **Budget total** | **< $50** (chỉ domain) |
| **License** | MIT (max viral) |
| **Domain** | `datawraith.dev` |

---

## 1. Triết Lý Sản Phẩm

### 1.1. Bài học từ v1 → v4

Brief đã trải qua 4 lần lặp với critique từ chính anh và bạn anh. 3 bài học quan trọng nhất:

1. **"Đừng build nhiều thứ cùng 1 lúc"** — v1 muốn làm 5 sản phẩm trong 1, v5 cắt xuống 1 sản phẩm với 4 release rõ ràng.
2. **"Đừng AI-native quá"** — v1-v3 đặt AI làm foundation, v5 đặt AI làm OPT-IN feature ở Phase 3+.
3. **"Đừng ship .exe trước khi có credibility"** — v1-v4 muốn .exe standalone là chính, v5 đảo lại: `pip install` là chính, `.exe` là bonus.

### 1.2. Ba Nguyên Tắc Của v5.0

1. **Engine-first**: Phase 1-2 chỉ làm chaos test engine. AI Phase 3+. Distribution `.exe` Phase 2+. Mỗi phase một mục tiêu.
2. **Dùng công cụ có sẵn, không tự build lại**: `pgserver` cho embedded PG, Textual cho TUI, official SDK cho AI. Không over-engineer.
3. **Quality over speed**: không có deadline cứng. Ship khi mỗi phase thật sự hoàn chỉnh. 100B Studio không có pressure investor.

### 1.3. Mục tiêu thật sự

Không phải startup unicorn. Không phải SaaS. Đây là:

- **OSS portfolio** cho 100B Studio chứng minh năng lực kỹ thuật
- **Eat your own dog food** cho Worldforesight, Educata (multi-tenant testing)
- **Viral hook** trên Vietnam dev community + Tech Twitter
- **Foundation** nếu sau này muốn build subscription tier (Phase 5+)

---

## 2. One-liner & USP

### 2.1. One-liner

> **DataWraith** là tool stress-test PostgreSQL chạy local. Cài bằng `pip install datawraith`, gõ `sdb` để khởi động. Embedded PG bundle sẵn, không cần Docker, không cần cài PostgreSQL.

### 2.2. Tagline

- **Python crowd**: *"`pip install datawraith` → `sdb` → chaos."*
- **Casual dev**: *"Stress-test your Postgres in 30 seconds. No setup."*
- **Vietnam community**: *"Test database trước khi production làm điều đó thay anh."*

### 2.3. USP — 3 weapon

1. **`pip install` là xong**: không Docker, không cài PG, không setup. `pgserver` bundle PostgreSQL portable trong wheel.
2. **4 chaos scenarios thực tế**: Concurrency, R/W Heavy, Migration Lock, Security & Isolation — pain point thật của startup.
3. **Lofi cyberpunk TUI**: aesthetic riêng, demo GIF viral được trên X.

---

## 3. Target User & Pain Point

| Persona | Pain | Giá trị nhận được |
|---|---|---|
| **Backend dev Python startup** | Không có DBA, monitor SaaS đắt | `pip install datawraith` → test trong 30s |
| **Backend Lead duyệt PR migration** | Sợ deploy giờ peak | Migration Lock Test (Phase 3) |
| **DBA team mid-size company** | Cần stress test trước release | Multi-scenario test, JSON/SARIF export |
| **Tech Twitter / r/PostgreSQL** | Tò mò tool DB mới | Demo GIF, lofi vibe, MIT license |
| **100B Studio nội bộ** | Worldforesight/Educata multi-tenant testing | Security & Isolation (Phase 4) |

---

## 4. Tech Stack — Production-ready 2026

### 4.1. Core dependencies

```toml
[project]
name = "datawraith"
dependencies = [
    "pgserver>=0.2",           # Embedded PostgreSQL, pip-installable
    "psycopg[binary]>=3.2",    # Modern PG client (sync + async)
    "asyncpg>=0.30",           # High-perf async cho stress test
    "textual>=1.0",            # TUI framework
    "typer>=0.12",             # CLI framework
    "faker>=30",               # Data generation
    "mimesis>=18",             # Bulk data (5-10x nhanh hơn Faker)
    "rich>=13",                # Console rendering
    "pydantic>=2.9",           # Models & config
]

[project.optional-dependencies]
ai = [
    "openai>=1.50",
    "anthropic>=0.40",
]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.24",
    "ruff>=0.7",
    "pyinstaller>=6",
]
```

### 4.2. Tại sao chọn từng package

| Package | Lý do |
|---|---|
| **`pgserver`** | Pip-installable PostgreSQL binary cho Win/Mac/Linux. Không cần root. Maintainer xử lý update PG version. Giảm 70% workload của Dev C. |
| **`psycopg 3`** | Successor của psycopg2, native asyncio, server-side binding. Stable hơn asyncpg cho operations. |
| **`asyncpg`** | Nhanh nhất cho stress test (1000+ concurrent connections). Dùng chỉ trong engine. |
| **Textual** | MIT, production-proven (Toad AI coding TUI, Posting API client). Run cả terminal và web browser. |
| **Typer** | Modern CLI framework, ít boilerplate, type-safe |
| **Faker + mimesis** | Faker cho realistic data (email, name), mimesis cho bulk speed |
| **Rich** | Console rendering tiêu chuẩn |
| **Pydantic 2** | Data validation tiêu chuẩn 2026 |
| **OpenAI/Anthropic SDK** | Official, không wrapper. BYOK chỉ cần 1 SDK + 1 LLM call đơn giản. |

### 4.3. Tại sao KHÔNG dùng các thứ phổ biến khác

| Package | Lý do không dùng |
|---|---|
| **LiteLLM** | Over-engineering cho 1 LLM call. User chỉ chọn 1 provider tại 1 thời điểm. |
| **LangChain** | Quá nặng, agent abstraction không cần thiết. AI Mode của DataWraith chỉ là `analyze(result) → suggestion`. |
| **SQLAlchemy** | Chậm 3-5x so với asyncpg cho stress test. Không cần ORM cho chaos testing. |
| **Docker / testcontainers** | Phá vỡ "zero dependency". pgserver thay thế hoàn toàn. |
| **Tauri** | Phase 5+ nếu muốn desktop app native. Phase 1-4 chỉ cần Textual + PyInstaller. |
| **MCP server** | Phase 5+ nice-to-have. Phase 1-4 user dùng CLI/TUI là đủ. |

---

## 5. Kiến Trúc Hệ Thống

### 5.1. 4-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Layer 4 — Interface                                    │
│  Textual TUI  │  Typer CLI                              │
├─────────────────────────────────────────────────────────┤
│  Layer 3 — AI Bridge (Phase 3+, OPT-IN, BYOK)           │
│  analyze(test_result, user_api_key) → suggestion        │
├─────────────────────────────────────────────────────────┤
│  Layer 2 — Test Engine (asyncio)                        │
│  Concurrency │ R/W Heavy │ Migration │ Security         │
├─────────────────────────────────────────────────────────┤
│  Layer 1 — Embedded Shadow DB                           │
│  pgserver (PostgreSQL portable + pgvector)              │
│  + pg_stat_statements + pg_qualstats                    │
└─────────────────────────────────────────────────────────┘
```

### 5.2. Project structure

```
datawraith/
├── pyproject.toml
├── README.md
├── CLAUDE.md                      # Root context cho Claude Code
├── datawraith/
│   ├── __init__.py
│   ├── cli.py                     # Typer entry point (sdb command)
│   ├── core/
│   │   ├── config.py              # Pydantic settings
│   │   ├── shadow_db.py           # pgserver wrapper
│   │   └── types.py               # Shared types
│   ├── engine/                    # Dev A's domain
│   │   ├── CLAUDE.md
│   │   ├── scenarios/
│   │   │   ├── base.py
│   │   │   ├── concurrency.py     # Phase 1
│   │   │   ├── rw_heavy.py        # Phase 2
│   │   │   ├── migration.py       # Phase 3
│   │   │   └── security.py        # Phase 4
│   │   ├── seeder.py
│   │   └── analyzer.py
│   ├── tui/                       # Dev B's domain
│   │   ├── CLAUDE.md
│   │   ├── app.py
│   │   ├── screens/
│   │   └── widgets/
│   ├── ai/                        # Dev C's domain (Phase 3+)
│   │   ├── CLAUDE.md
│   │   ├── bridge.py
│   │   └── prompts.py
│   └── output/
│       ├── json_exporter.py
│       ├── sarif_exporter.py
│       └── ascii_renderer.py
└── tests/
    ├── test_engine.py
    ├── test_tui.py
    └── fixtures/
```

### 5.3. Code mẫu — Shadow DB

```python
# datawraith/core/shadow_db.py
import pgserver
import tempfile
from pathlib import Path
from contextlib import asynccontextmanager
import psycopg

class ShadowDB:
    """Embedded PostgreSQL instance for chaos testing.
    
    Uses pgserver to bundle PG binary. No Docker, no system install needed.
    """
    
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or Path(tempfile.mkdtemp(prefix="datawraith_"))
        self._server = None
    
    def start(self) -> str:
        """Start embedded PG, return connection URI."""
        self._server = pgserver.get_server(
            self.data_dir,
            cleanup_mode='stop'
        )
        return self._server.get_uri()
    
    def stop(self):
        if self._server:
            self._server.cleanup()
    
    async def load_schema(self, schema_sql: str):
        async with await psycopg.AsyncConnection.connect(self._server.get_uri()) as conn:
            await conn.execute(schema_sql)
    
    @asynccontextmanager
    async def connection(self):
        async with await psycopg.AsyncConnection.connect(self._server.get_uri()) as conn:
            yield conn
```

**Đây là toàn bộ logic embedded PG**. Đơn giản, ổn định, production-ready.

---

## 6. Roadmap — 4 Phase, No Deadline

### 6.1. Triết lý timeline

**Không gắn deadline cứng**. Mỗi phase ship khi thật sự hoàn chỉnh, không phải khi hết tuần. 3 dev part-time = pace tự nhiên.

Tuy nhiên, có **estimate tham khảo** để team có sense về tiến độ:

| Phase | Scenario | Release | Estimate (tham khảo) |
|---|---|---|---|
| **Phase 1** | Concurrency Test | **v0.1** | ~6-8 tuần |
| **Phase 2** | Read/Write Heavy + `.exe` build | **v0.2** | ~5-7 tuần |
| **Phase 3** | Migration Lock + AI BYOK | **v0.3** | ~6-8 tuần |
| **Phase 4** | Security & Isolation | **v1.0** | ~7-9 tuần |

**Total estimate: ~24-32 tuần (6-8 tháng)**. Slip cũng OK.

### 6.2. Định nghĩa "hoàn chỉnh" của mỗi phase

Mỗi phase chỉ được ship khi:

- [ ] Scenario chạy end-to-end không bug critical
- [ ] Có demo GIF 15-30s
- [ ] README + changelog cập nhật
- [ ] 5+ test trên 3 OS (Win/Mac/Linux qua GitHub Actions)
- [ ] Có ít nhất 1 paragraph documentation trong `datawraith.dev/docs`
- [ ] Manual test bởi cả 3 dev với schema thật

---

## 7. Phase 1 Detail — Concurrency Test (v0.1)

### 7.1. Mục tiêu

Ship `pip install datawraith` + Concurrency Test scenario hoạt động hoàn hảo. Đây là foundation. Phase 1 làm tốt thì 3 phase sau chỉ là "thêm scenario".

### 7.2. Scope Phase 1 (chặt chẽ)

**MUST HAVE:**
- `pip install datawraith` chạy được trên Win/Mac/Linux
- Lệnh `sdb` mở Textual TUI
- Embedded PG spinup tự động qua pgserver
- Concurrency Test: 1000+ concurrent UPDATEs, deadlock detection, MVCC bloat
- TUI: live log + metrics chart + Top 3 culprits
- Export JSON report
- GitHub Actions CI: test + lint + publish wheel

**NOT IN Phase 1 (defer rõ ràng):**
- ❌ AI Mode (Phase 3)
- ❌ `.exe` standalone build (Phase 2)
- ❌ Headless CLI flag (Phase 2)
- ❌ Other 3 scenarios (Phase 2-4)
- ❌ SARIF/JUnit/PDF export (Phase 4)
- ❌ Compare runs feature (Phase 2)
- ❌ MCP server (Phase 5+ nếu có)

### 7.3. Task allocation 3 dev

| Tuần | Dev A (Engine) | Dev B (TUI) | Dev C (Build + DevOps) |
|---|---|---|---|
| 1 | Setup pgserver + psycopg3 prototype, test PG spinup local | Setup Textual app skeleton + theme (purple/cyan/navy) | Setup repo, pyproject.toml, GitHub Actions skeleton |
| 2 | Schema parser (.sql DDL), Faker+mimesis seeder | TUI navigation: splash → init → seed → attack flow | TestPyPI publishing setup, CI test cross-platform |
| 3 | Concurrency Test engine (1000 workers, asyncpg) | Live log panel real-time + metrics streaming | Documentation site setup (mkdocs-material) |
| 4 | Deadlock detection, lock wait analysis | Dashboard layout sau khi test xong | Internal alpha v0.1.0-alpha → TestPyPI |
| 5 | Top culprits analyzer (pg_stat_statements parser) | Export JSON UI + ASCII chart render | Smoke test pip install thật trên 3 OS |
| 6 | Edge cases: connection drop, stuck queries, OOM | Polish vibe: ASCII wraith animation | Pre-launch checklist, README polish |
| 7 | Bug fix từ team feedback, performance tuning | Final UX polish, keyboard shortcuts | Demo GIF recording, landing page deploy |
| 8 | Buffer | Buffer | **v0.1.0 release → PyPI + GitHub + launch tweet** |

### 7.4. Output Phase 1

- `pip install datawraith` works trên Win/Mac/Linux
- Lệnh `sdb` mở TUI đẹp với 1 scenario hoạt động hoàn hảo
- Demo GIF 15-30s viral-ready
- Public PyPI package + GitHub repo public
- Target: 50-200 GitHub stars trong 2 tuần đầu

---

## 8. Phase 2 — R/W Heavy + .exe Build (v0.2)

### 8.1. Scope

**MUST HAVE:**
- R/W Heavy scenario: bom 1M+ rows, complex queries (window function, multi-JOIN)
- Full table scan detection
- Rule-based index recommendation từ pg_qualstats
- Headless CLI mode: `sdb attack rw-heavy --output result.json --no-tui`
- Compare runs: `sdb compare baseline.json current.json`
- **`.exe` standalone build** với PyInstaller (bundle pgserver wheel)
- Release v0.2

### 8.2. .exe Strategy

Phase 2 mới thêm `.exe` vì:
- Pip install đã ổn định ở v0.1 (foundation chắc rồi)
- Có user feedback từ v0.1 để biết có cần .exe không
- Dev C đã có experience build CI từ Phase 1

PyInstaller command đơn giản:
```bash
pyinstaller --onefile \
  --name sdb \
  --collect-all pgserver \
  --collect-all textual \
  datawraith/cli.py
```

`.exe` size ước tính: 80-120MB (nhẹ hơn v4 estimate 150MB nhờ pgserver wheel đã optimize).

### 8.3. Feedback loop Phase 1 → 2

Tuần đầu Phase 2 dành 3-5 ngày đọc kỹ feedback từ user v0.1:
- GitHub issues
- X/Twitter mentions
- Discord/Reddit comments
- Email vào hello@datawraith.dev

Fix critical bug v0.1 trước khi xây Phase 2 features.

---

## 9. Phase 3 — Migration Lock + AI BYOK (v0.3)

### 9.1. Scope

**MUST HAVE:**
- Migration Lock scenario: simulate `ALTER TABLE` / `ADD COLUMN` / `CREATE INDEX` dưới tải
- Detect lock timeout, blocked queries, downtime estimation
- **AI Mode (BYOK) lần đầu xuất hiện**: user nhập API key trong Settings
- AI làm gì: đọc Migration Lock result → suggest `CREATE INDEX CONCURRENTLY` / `pg_repack` / online DDL alternatives
- **TUI hiện popup** lần đầu mở v0.3 thông báo AI Mode tồn tại
- Release v0.3

### 9.2. AI Mode UX

```
User mở DataWraith v0.3 lần đầu
  ↓
Popup: "💡 New in v0.3: AI Assistant"
        "Get AI-powered suggestions for DB issues."
        "Bring your own API key (Claude/OpenAI/Gemini/Ollama)."
        [ Setup Now ]  [ Maybe Later ]  [ Don't show again ]
  ↓
Nếu Setup Now:
  → Settings → AI Provider
  → Chọn: Claude / OpenAI / Gemini / Ollama
  → Nhập API key (encrypted in OS keyring)
  → Test connection
  → Done
  ↓
Engine Mode vẫn là DEFAULT
AI Mode chỉ activate khi user explicitly enable
```

### 9.3. AI implementation (simple)

```python
# datawraith/ai/bridge.py
from anthropic import Anthropic
from openai import OpenAI

def analyze_migration_result(result: MigrationLockResult, 
                              provider: str, 
                              api_key: str) -> str:
    """Single LLM call: analyze test result, return suggestion."""
    prompt = build_prompt(result)
    
    if provider == "claude":
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    elif provider == "openai":
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    # ... gemini, ollama
```

**~50 dòng code**. Không cần LLM router phức tạp. Không cần fallback chain. User chọn 1 provider, nhập 1 key, dùng.

### 9.4. Dev test AI nội bộ

3 dev test bằng key cá nhân:
- Anh dùng GPT-4o $20 hiện có
- Dev B/C đăng ký free tier Gemini AI Studio (1,500 req/day)
- Test 20 scenarios kết quả Migration Lock → kiểm tra AI suggest có đúng không

**DataWraith KHÔNG ship key.** User muốn AI thì tự cấp key.

---

## 10. Phase 4 — Security & Isolation + v1.0 (v1.0)

### 10.1. Scope

**MUST HAVE:**
- Security & Isolation scenario: RLS leak, SQL injection fuzz, privilege escalation
- Multi-tenant test scenario (target Worldforesight/Educata use case)
- SARIF export cho CI/CD integration (GitHub Security tab)
- JUnit XML export
- PDF report export
- **v1.0 stable release**
- Show HN + Product Hunt launch

### 10.2. v1.0 = milestone lớn

- 4 scenarios đầy đủ
- pip install + `.exe` đều ổn định
- AI BYOK hoạt động cho 4 providers
- Documentation đầy đủ ở `datawraith.dev/docs`
- Tweet thread giới thiệu hành trình 6-8 tháng
- Show HN + Product Hunt launch
- Target: 2K-10K GitHub stars sau launch

---

## 11. Team & Workflow

### 11.1. Module ownership (cố định suốt 4 phase)

| Dev | Module | Trách nhiệm |
|---|---|---|
| **Dev A** | `engine/` + `core/shadow_db.py` | 4 scenarios, asyncio runner, pgserver integration, schema parser, seeder, analyzer |
| **Dev B** | `tui/` + `output/` | Textual app, screens, widgets, aesthetic, JSON/SARIF/PDF exporter |
| **Dev C** | `build/` + `ai/` (Phase 3+) | pyproject.toml, GitHub Actions CI, PyPI publishing, PyInstaller (Phase 2), AI bridge (Phase 3+) |

### 11.2. Claude Code workflow

1. **Branch dài hạn per dev**: `dev-a/engine`, `dev-b/tui`, `dev-c/build`
2. **Merge vào `main` qua PR** — Claude Code review trước
3. **Mỗi module có `CLAUDE.md`** chi tiết context
4. **Module API contracts** lock từ Tuần 1, không đổi giữa phase
5. **Daily 15-phút sync** Slack/Discord
6. **Weekly 30-phút call** align architecture decisions

### 11.3. Test method nội bộ

**Phase 1**: dev test bằng `pip install -e .` (editable install, fast iteration)

**Phase 2+**: thêm `.exe` build trong daily CI, dev tải artifact test thực tế user experience

---

## 12. User Flow & TUI

### 12.1. Cài đặt user

```bash
# Cách 1: Python user (Phase 1+)
pip install datawraith
sdb

# Cách 2: Non-Python user (Phase 2+)
# Tải DataWraith-0.2.0-x64.exe từ datawraith.dev
# Double-click → mở TUI
```

### 12.2. Terminal commands

```bash
$ sdb                              # Mở TUI interactive
$ sdb init ./schema.sql            # Khởi tạo shadow DB
$ sdb init --from prisma           # Auto-detect Prisma/Drizzle migrations
$ sdb seed --rows 1000000          # Sinh data
$ sdb seed --dist zipfian          # Distribution chooser
$ sdb attack concurrency           # Phase 1
$ sdb attack rw-heavy              # Phase 2
$ sdb attack migration             # Phase 3
$ sdb attack security              # Phase 4
$ sdb attack --all                 # All 4 (Phase 4+)
$ sdb compare baseline.json now.json  # Phase 2+
$ sdb report --format json|sarif|pdf  # Phase 1+/4+
$ sdb ai setup                     # Phase 3+ AI BYOK
$ sdb doctor                       # Health check
$ sdb --version
```

### 12.3. TUI mockup v0.1

```
┌─ DataWraith ────────────────────────────── sdb v0.1 ─┐
│                                                       │
│  Mode: Engine                                        │
│  Embedded PG 16.4 running via pgserver               │
│  Scenario: Concurrency Test     Run: #1              │
│                                                       │
│  ┌─ Live Log ──────────┐  ┌─ Metrics ─────────────┐  │
│  │ [12:43:01] BEGIN... │  │ QPS    : 8,432        │  │
│  │ [12:43:01] UPDATE.. │  │ p99    : 142ms        │  │
│  │ [12:43:02] DEADLOCK │  │ Errors : 12           │  │
│  │ [12:43:02] ROLLBACK │  │ Deadlk : 3            │  │
│  └─────────────────────┘  └───────────────────────┘  │
│                                                       │
│  ┌─ Top Culprits ────────────────────────────────┐   │
│  │ 1. UPDATE products SET stock... (47% impact) │   │
│  │ 2. SELECT * FROM orders JOIN... (22%)        │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  [F1] Help [F2] Pause [F3] Stop [F4] Export          │
└───────────────────────────────────────────────────────┘
```

### 12.4. TUI mockup v0.3 (AI popup)

```
┌─ DataWraith ────────────────────────────── sdb v0.3 ─┐
│                                                       │
│      ┌─ 💡 New in v0.3: AI Assistant ──────┐         │
│      │                                       │         │
│      │  Get AI-powered suggestions for      │         │
│      │  fixing DB performance issues.       │         │
│      │                                       │         │
│      │  Just bring your own API key:        │         │
│      │  • Claude (Anthropic)                │         │
│      │  • OpenAI                            │         │
│      │  • Gemini (Google)                   │         │
│      │  • Ollama (local)                    │         │
│      │                                       │         │
│      │  DataWraith never stores your key.   │         │
│      │                                       │         │
│      │  [ Setup Now ]  [ Maybe Later ]      │         │
│      │  [ Don't show again ]                │         │
│      └───────────────────────────────────────┘         │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 13. Bốn Scenarios — Spec

### 13.1. Concurrency Test (Phase 1)

- 1000+ concurrent workers UPDATE/INSERT same dataset
- Detect: deadlock, lock wait, MVCC bloat, transaction rollback rate
- Output: deadlock graph ASCII, lock chain visualization, Top 3 contention hotspots

### 13.2. Read/Write Heavy (Phase 2)

- Bom 1M+ rows, complex queries (window function, multi-JOIN)
- Detect: full table scan, slow query, missing index
- Output: Top N slow queries với EXPLAIN ANALYZE, rule-based index recommendation

### 13.3. Migration Lock (Phase 3)

- Vừa load workload vừa thực thi DDL (`ALTER TABLE`, `CREATE INDEX`)
- Detect: lock timeout, blocked queries, downtime estimation
- Output: time-to-recovery chart, alternative DDL suggestion
- **AI Mode (BYOK)**: suggest online DDL patterns

### 13.4. Security & Isolation (Phase 4)

- RLS leak detection (cross-tenant query)
- SQL injection fuzz
- Privilege escalation test
- Output: vulnerability list, cross-tenant access matrix, audit log

---

## 14. Ngân Sách

| Item | Cost | Phase |
|---|---|---|
| Domain `datawraith.dev` | $12-15/năm | Phase 1 |
| GitHub Actions (public repo) | $0 | Phase 1+ |
| Cloudflare Pages (landing) | $0 | Phase 1 |
| mkdocs-material docs site | $0 | Phase 1+ |
| PyPI publishing | $0 | Phase 1+ |
| Free tier Gemini cho dev test | $0 | Phase 3 |
| Anh tự cấp GPT-4o $20 cho dev test | $0 (đã có) | Phase 3 |
| **Tổng** | **~$15** | |

### 14.1. Defer to Phase 5+ (nếu monetize)

- EV code signing cert ($300/năm) — chỉ khi cần `.exe` không bị SmartScreen warn
- Apple Developer ($99/năm) — chỉ khi cần macOS notarization
- Hosted CI cho Pro Cloud tier
- Custom domain email

---

## 15. GTM — OSS Viral No Budget

### 15.1. Pre-launch (suốt Phase 1)

- Build in public weekly thread X
- GitHub repo public từ Tuần 1 (build openly)
- Reserve handles: GitHub `100b-studio/datawraith`, X `@datawraith_dev`, PyPI `datawraith`

### 15.2. Launch v0.1 (cuối Phase 1)

**Tweet 1 (Python crowd):**
> `pip install datawraith` then `sdb`
> 
> Chaos-test your Postgres in 30 seconds. Embedded PG via pgserver, zero Docker, MIT license. 🌬️
> 
> [GIF demo 20s]

**Reddit r/PostgreSQL post**:
> "I built a Postgres chaos-testing tool — pip-installable, embedded PG, MIT license. Looking for feedback."

**Vietnam communities**:
- J2Team Community
- Vietnam Developer Community FB
- Daynhauhoc forum
- Tinhte tech section

### 15.3. Per-release launches (v0.2, v0.3, v1.0)

Mỗi release = 1 mini launch event:
- Demo GIF mới
- Changelog tweet
- Reddit post
- Vietnam community update

### 15.4. v1.0 launch lớn

- Show HN với tag-line *"pip install datawraith — chaos-test Postgres in 30 seconds"*
- Product Hunt launch
- Tweet thread retrospective 6-8 tháng
- Blog post technical (medium/dev.to)

### 15.5. Target metrics (tham khảo)

| Milestone | GitHub stars | PyPI downloads |
|---|---|---|
| v0.1 release | 50-200 | 100-500 |
| v0.2 release | 200-800 | 500-2K |
| v0.3 release | 500-2K | 2K-5K |
| v1.0 launch | 2K-10K | 10K-50K |

---

## 16. Rủi Ro & Mitigation

| Rủi ro | Khả năng | Tác động | Mitigation |
|---|---|---|---|
| 3 dev part-time slip tiến độ | Rất cao | Thấp | **No deadline**. Slip cũng OK. |
| 1 dev nghỉ giữa chừng | Trung bình | Cao | `CLAUDE.md` per module. Dev khác (hoặc Claude Code) tiếp quản |
| `pgserver` bị abandon | Thấp | Cao | MIT license, có thể fork. Pgembed là backup. |
| PG security CVE | Trung bình | Cao | Subscribe PG mailing list. pgserver update khi PG release. |
| Bug DataWraith xóa data production | Thấp | Critical | `--prevent-prod` flag default ON. Embedded PG isolate hoàn toàn. |
| AI sinh suggestion sai | Trung bình | Trung bình | AI chỉ "suggest", không apply auto. User review trước. |
| Không viral | Trung bình | Trung bình | Worst case: portfolio piece tốt cho 100B Studio. |
| Có người fork commercial | Thấp | Thấp | MIT chấp nhận. Commit history là proof. |
| Pip install fail trên OS lạ | Trung bình | Trung bình | CI test Win/Mac/Linux. Docs có troubleshooting section. |
| Maintenance burden sau viral | Cao | Trung bình | Policy "we respond in 1 week". OSS không có SLA. |

---

## 17. Tuần 1 Action Items

### Day 1 — Cả team họp 2 giờ

- [ ] Confirm tech stack (lock-in v5.0)
- [ ] Confirm naming + MIT license
- [ ] Đăng ký domain `datawraith.dev` ($15)
- [ ] Tạo GitHub org `100b-studio`, repo `100b-studio/datawraith` (public)
- [ ] Setup Slack/Discord channel
- [ ] Reserve X handle `@datawraith_dev`, PyPI `datawraith`
- [ ] Lock module API contracts:
  - `engine/scenarios/base.py` → `Scenario` ABC class
  - Pydantic models cho `TestResult`, `Culprit`, `Suggestion`
  - JSON schema cho export format
- [ ] Quyết branch strategy: GitHub Flow đơn giản

### Dev A (Engine) — Tuần 1

- [ ] Setup local Python 3.12 + venv
- [ ] `pip install pgserver psycopg[binary] asyncpg`
- [ ] Prototype: spinup pgserver → load schema → query → cleanup
- [ ] Viết `engine/scenarios/base.py` ABC class
- [ ] Tạo `engine/CLAUDE.md`

### Dev B (TUI) — Tuần 1

- [ ] Setup Textual + textual-dev
- [ ] Design tokens: purple #B26AFF, cyan #00D4FF, navy #0A0E27
- [ ] Build `tui/app.py` skeleton với 3 screens: splash, init, attack
- [ ] Mockup chi tiết trong Figma/Excalidraw
- [ ] Tạo `tui/CLAUDE.md`

### Dev C (Build) — Tuần 1

- [ ] Setup pyproject.toml với dependencies lock-in
- [ ] GitHub Actions: lint (ruff) + test (pytest) + build wheel cho 3 OS
- [ ] TestPyPI account, test publish workflow
- [ ] Cloudflare Pages landing mock
- [ ] Tạo `build/CLAUDE.md`

---

## 18. So Sánh v1.0 → v5.0

### 18.1. Tóm tắt evolution

| Version | Key change | Reason |
|---|---|---|
| **v1.0** (DBRE-Agent) | Initial concept | First brainstorm |
| **v2.0** (DataWraith) | Renaming + sharp positioning | Brand cần dễ nhớ, USP rõ |
| **v2.1** | Zero-dependency với embedded PG | Bypass Docker requirement |
| **v2.2** | Free tier LLM rotation | Bỏ pressure phải có $$ cho AI |
| **v3.0** | 3-dev allocation + compressed roadmap | Realistic cho 100B Studio |
| **v4.0** | Cut scope: AI defer Phase 3, 1 scenario/phase | Critique của bạn anh: "build nhiều thứ quá" |
| **v5.0** | **pip install primary, pgserver, no deadline** | **Tech stack mới + no pressure** |

### 18.2. Tỉ lệ thu hút & thành công

| Metric | v1.0 | v5.0 | Tăng |
|---|---|---|---|
| Repo views → stars | 1-2% | **4-6%** | 3-4x |
| Stars → downloads | 5-10% | **30-50%** | 5-6x (pip easier than .exe) |
| Downloads → return user | 10-20% | **40-60%** | 3-4x (scope nhỏ hơn → quality cao hơn) |
| Min success (500+ stars) | 15-20% | **65-80%** | 4x |
| Good success (3K+ stars) | 3-5% | **30-45%** | 8-9x |
| Great success (10K+ stars) | <1% | **10-20%** | 15-20x |

**v5.0 có xác suất thành công cao hơn v1.0 khoảng 4-15x** ở các cấp độ.

### 18.3. Lý do tăng mạnh

1. **`pip install` primary**: Python dev = early adopter community. Friction = 0.
2. **pgserver**: giảm 70% workload Dev C → ship được sớm, ít bug.
3. **No deadline**: chất lượng > tốc độ. Đúng tinh thần OSS portfolio.
4. **Scope chặt chẽ**: 1 phase 1 scenario. Mỗi release đều ship được dùng được.
5. **AI là feature, không phải foundation**: không bị "AI-native quá".

---

## 19. Triết Lý Chốt

DataWraith là **chaos-testing tool cho PostgreSQL** trước hết. AI chỉ là sugar trên cake. Cake (engine) phải ngon trước.

3 dev × 50-70% time × no deadline = build được sản phẩm OSS chỉn chu, viral được trong dev community. Tech stack 2026 (pgserver + psycopg3 + Textual) cho phép focus vào value thật, không phải plumbing.

**Mục tiêu duy nhất**: 2K-10K GitHub stars + tech credibility cho 100B Studio. Mọi thứ khác là bonus.

Khi đạt được mục tiêu, mở Phase 5 với:
- Subscription tier (hosted CI runner, advanced AI model riêng)
- Multi-DB support (MySQL, MongoDB)
- Enterprise features (SSO, audit, compliance)

Còn bây giờ: **ship Phase 1 thật tốt**, mọi thứ khác từ từ.

---

## 20. Quyết Định Đã Chốt

✅ Tên: **DataWraith**
✅ Terminal alias: **`sdb`**
✅ Team: **3 dev × 50-70% time**
✅ Workflow: **Claude Code rush**
✅ License: **MIT**
✅ Distribution: **pip install primary, .exe Phase 2+**
✅ Embedded PG: **pgserver**
✅ AI: **BYOK 100%, Phase 3+, popup nhắc**
✅ Test nội bộ: **pip install -e .` (Phase 1), .exe (Phase 2+)**
✅ Timeline: **No deadline, estimate 6-8 tháng**
✅ Budget: **~$15 (domain only)**
✅ Roadmap: **4 phase = 4 scenarios = 4 releases**

---

*Tài liệu nội bộ · 100B Studio · DataWraith v5.0 Final Brief*
*Stack 2026: pgserver · psycopg3 · Textual · asyncpg · BYOK AI · MIT*
