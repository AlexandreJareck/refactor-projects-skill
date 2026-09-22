from datetime import UTC, datetime


def utc_now():
    """Return naive UTC for compatibility with the existing SQLite columns."""
    return datetime.now(UTC).replace(tzinfo=None)

