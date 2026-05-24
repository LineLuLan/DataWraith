"""pgserver availability checks for integration tests."""

from __future__ import annotations

import importlib.util
import os
import sys


def pgserver_available() -> bool:
    """Return whether embedded pgserver tests should run.

    pgserver can install on Windows Python 3.12, but its bundled initdb is
    currently flaky on GitHub Windows runners. The Linux/macOS matrix and the
    PostgreSQL fallback E2E job cover real database execution; Windows keeps
    package, CLI, build, and dry-run coverage unless explicitly enabled.
    """
    if sys.platform == "win32" and os.getenv("DATAWRAITH_ENABLE_WINDOWS_PGSERVER") != "1":
        return False
    return importlib.util.find_spec("pgserver") is not None
