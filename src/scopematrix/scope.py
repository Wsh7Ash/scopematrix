"""Scope parsing: turn a program scope file into structured asset decisions.

Scope file format (line based, '#' comments):
    + *.example.com          # include (wildcard domain)
    - admin.example.com      # exclude (always wins)
    + https://api.example.com/v1
    + 10.0.0.0/24            # CIDR include

Asset types: domain, wildcard, url, cidr, email.
Matching rules: an asset is in scope when it matches at least one include
and no exclude. Excludes always win.
"""
from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

WILDCARD_RE = re.compile(r"^\*\.(?P<base>[A-Za-z0-9.-]+)$")
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


class ScopeError(ValueError):
    """Raised for malformed scope files or assets."""


@dataclass
class ScopeEntry:
    action: str  # "include" | "exclude"
    raw: str
    kind: str
    pattern: object = None


@dataclass
class Scope:
    entries: list[ScopeEntry] = field(default_factory=list)

    @classmethod
    def parse(cls, text: str) -> "Scope":
        entries: list[ScopeEntry] = []
        for lineno, line in enumerate(text.splitlines(), 1):
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            action = None
            if line[0] in "+-":
                action, line = ("include" if line[0] == "+" else "exclude"), line[1:].strip()
            elif line.lower().startswith("include ") or line.lower().startswith("exclude "):
                head, _, line = line.partition(" ")
                action = "include" if head.lower() == "include" else "exclude"
                line = line.strip()
            if action is None or not line:
                raise ScopeError(f"line {lineno}: expected '+ pattern' or '- pattern'")
            entries.append(ScopeEntry(action, line, *_classify(line)))
        if not entries:
            raise ScopeError("scope file contains no entries")
        return cls(entries)


def _classify(raw: str) -> tuple[str, object]:
    """Return (kind, compiled matcher) for a scope pattern."""
    m = WILDCARD_RE.match(raw)
    if m:
        return "wildcard", m.group("base").lower()
    if raw.startswith("http://") or raw.startswith("https://"):
        parts = urlsplit(raw)
        if not parts.hostname:
            raise ScopeError(f"url has no host: {raw}")
        return "url", (parts.scheme.lower(), parts.hostname.lower(), parts.path)
    try:
        return "cidr", ipaddress.ip_network(raw, strict=False)
    except ValueError:
        pass
    if EMAIL_RE.match(raw):
        return "email", raw.lower()
    if DOMAIN_RE.match(raw):
        return "domain", raw.lower()
    raise ScopeError(f"cannot classify scope pattern: {raw!r}")


def _host_of(asset: str) -> str | None:
    if asset.startswith(("http://", "https://")):
        return (urlsplit(asset).hostname or "").lower() or None
    return asset.lower()


def check(scope: Scope, asset: str) -> dict:
    """Decide whether `asset` (domain, url, IP, email, or CIDR) is in scope."""
    asset = asset.strip()
    host = _host_of(asset)
    if host is None:
        raise ScopeError(f"cannot extract host from asset: {asset!r}")

    matched_include = None
    for entry in scope.entries:
        if entry.action == "include" and _matches(entry, asset, host):
            matched_include = entry
            break
    excluded_by = next(
        (e for e in scope.entries if e.action == "exclude" and _matches(e, asset, host)),
        None,
    )

    if excluded_by:
        verdict, reason = "out-of-scope", f"matched exclude {excluded_by.raw!r}"
    elif matched_include:
        verdict, reason = "in-scope", f"matched include {matched_include.raw!r}"
    else:
        verdict, reason = "out-of-scope", "no include entry matched"

    return {"asset": asset, "host": host, "verdict": verdict, "reason": reason}


def _matches(entry: ScopeEntry, asset: str, host: str) -> bool:
    kind, pat = entry.kind, entry.pattern
    if kind == "wildcard":
        return host == pat or host.endswith("." + pat)
    if kind == "domain":
        return host == pat
    if kind == "url":
        scheme, pat_host, path = pat
        if not (asset.startswith(scheme + "://") and host == pat_host):
            return False
        return path in ("/", "") or urlsplit(asset).path.startswith(path)
    if kind == "cidr":
        try:
            return ipaddress.ip_address(host) in pat
        except ValueError:
            return False  # hostname, not an IP
    if kind == "email":
        return asset.lower() == pat
    return False


def summary(scope: Scope) -> dict:
    counts: dict[str, int] = {}
    for entry in scope.entries:
        counts[entry.kind] = counts.get(entry.kind, 0) + 1
    return {
        "total": len(scope.entries),
        "includes": sum(1 for e in scope.entries if e.action == "include"),
        "excludes": sum(1 for e in scope.entries if e.action == "exclude"),
        "by_kind": counts,
    }