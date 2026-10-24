# Architecture — scopematrix

## Overview

`scopematrix` (bug-bounty-tooling) is a single-package Python CLI: a `src/scopematrix/` package
with a pure logic module and a Click command layer, console-script entry point
`scopematrix = scopematrix.cli:main`, and no runtime services.

### `src/scopematrix/scope.py`

Parser and matcher. Classifies each pattern (wildcard, url, cidr, email, domain) at parse time, then matches assets by host/IP equality, suffix, scheme+path prefix, or network containment. Excludes always win.

### `src/scopematrix/cli.py`

Click group: `parse` (summary table), `check` (per-asset verdict + deciding entry), `batch` (file of assets, aggregate exit code), all with --json-out.


## Design decisions

- **Logic/rendering separation.** Every decision (parse, match, lint, plan, score)
  lives in a pure module with no console output, so tests assert on data rather than
  on terminal formatting.
- **Exit codes as the CI contract.** 0 = clean/success, 1 = findings or failed
  validation, 2 = usage or read error. `--json-out` switches stdout to machine-readable
  JSON without changing exit codes.
- **Small dependency surface.** Only `click` (CLI) and `rich` (tables); everything
  else is the Python standard library. Fewer dependencies, fewer surprises.

## Data flow

```
input (token / file / URL + flags)
   -> Click command validates arguments
   -> pure module computes findings/verdicts/summary
   -> renderer prints table or JSON
   -> process exits 0 / 1 / 2
```

## Testing strategy

tests/test_m.py covers counts/kinds, wildcard subdomains, exclude precedence, URL scheme+path rules, CIDR vs hostname, malformed files, and CLI exit codes 0/1/2.
