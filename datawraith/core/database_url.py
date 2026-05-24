"""Safe PostgreSQL URL handling for local-only execution."""

from __future__ import annotations

from urllib.parse import urlparse

from datawraith.core.exceptions import ShadowDBError

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
POSTGRES_SCHEMES = {"postgres", "postgresql"}


def validate_local_database_url(database_url: str) -> str:
    """Validate a PostgreSQL URL and reject non-local TCP hosts.

    DataWraith is intentionally local-first. A user-supplied PostgreSQL URL is
    allowed only when it targets localhost/loopback or a Unix-socket style URL.
    This gives Python 3.13+ users a practical fallback without making it easy to
    point chaos scenarios at production infrastructure by accident.
    """
    normalized_url = database_url.strip()
    if not normalized_url:
        raise ShadowDBError("database URL cannot be empty")

    parsed = urlparse(normalized_url)
    if parsed.scheme not in POSTGRES_SCHEMES:
        raise ShadowDBError("database URL must use postgres:// or postgresql://")

    host = parsed.hostname
    if host is None:
        return normalized_url
    if host in LOCAL_HOSTS:
        return normalized_url

    raise ShadowDBError(
        "DataWraith only accepts local PostgreSQL URLs by default "
        "(localhost, 127.0.0.1, ::1, or a local socket URL)."
    )
