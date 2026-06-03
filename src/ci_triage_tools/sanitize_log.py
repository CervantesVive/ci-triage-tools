from __future__ import annotations
import re
from pathlib import Path

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_TS_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z ")

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

    sentinel_idx = next(
        (i for i, l in enumerate(lines) if _SENTINEL_RE.search(l)),
        None,
    )
    if sentinel_idx is not None:
        lines = lines[sentinel_idx:]

    cleanup_idx = next(
        (i for i, l in enumerate(lines) if _CLEANUP_RE.search(l)),
        None,
    )
    if cleanup_idx is not None:
        lines = lines[:cleanup_idx]

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
