from __future__ import annotations
import re
from pathlib import Path

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_TS_PREFIX_RE = re.compile(
    r"^(?:[^\t]+\t[^\t]+\t)?\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z "
)

# First line matching this → discard everything before it
_SENTINEL_RE = re.compile(r"##\[group\]Run pnpm ")

# First line matching this → discard it and everything after
_CLEANUP_RE = re.compile(r"Post job cleanup\.")

# Lines to drop entirely (matched against bare content, timestamp stripped)
_DROP_RES = [
    re.compile(r"Updating files:\s+\d+%"),
    re.compile(r"Progress: resolved \d+"),
    re.compile(r"Packages: \+\d+"),
    re.compile(r"^\+{4,}$"),
    re.compile(r"^\[command\]/usr/bin/git "),
    re.compile(r"^Download action repository "),
    re.compile(r"^##\[(group|endgroup)\]"),
    re.compile(r"\(node:\d+\) \[DEP\d+\] DeprecationWarning"),
    re.compile(r"Use `node --trace-deprecation"),
]

# Lines that always survive (checked after ANSI strip, before drop rules)
_KEEP_RE = re.compile(
    r"##\[error\]"
    r"|##\[group\]Run pnpm "
    r"|\bFAIL\b"
    r"|\bError:"
    r"|✗|×"
    r"|AssertionError"
    r"|TypeError"
    r"|ELIFECYCLE"
    r"|exit code \d"
    r"|\bat .+\.(tsx?|jsx?|py):\d"
    r"|blob report written"
)


def sanitize(text: str) -> str:
    if not text:
        return ""

    lines = text.splitlines()
    lines = [_ANSI_RE.sub("", line) for line in lines]

    # Collect all sentinel→cleanup segments from the (possibly multi-job) log.
    # Each segment starts at a "Run pnpm …" group and ends just before cleanup.
    # If no sentinel is found at all, process all lines as one fallback segment.
    segments: list[list[str]] = []
    seg_start: int | None = None
    found_any_sentinel = False

    for i, l in enumerate(lines):
        if _SENTINEL_RE.search(l):
            if seg_start is None:
                seg_start = i
                found_any_sentinel = True
        elif seg_start is not None and _CLEANUP_RE.search(l):
            segments.append(lines[seg_start:i])
            seg_start = None

    if seg_start is not None:
        segments.append(lines[seg_start:])

    lines = [l for seg in segments for l in seg] if found_any_sentinel else lines

    result: list[str] = []
    skip_indented = False

    for line in lines:
        bare = _TS_PREFIX_RE.sub("", line)

        if skip_indented:
            if bare and not bare[0].isspace():
                skip_indented = False
            else:
                continue

        if re.match(r"\s*(env|with):\s*$", bare):
            skip_indented = True
            continue

        if _KEEP_RE.search(bare):
            result.append(line)
            continue

        if any(r.search(bare) for r in _DROP_RES):
            continue

        result.append(line)

    return "\n".join(result)


def sanitize_file(path: Path) -> str:
    return sanitize(path.read_text(encoding="utf-8", errors="replace"))
