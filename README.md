# scopematrix

**Turn a bug-bounty program's scope definition into machine-checkable in/out verdicts.**

`scopematrix` parses a program scope file (wildcards, exclusions, URLs, CIDRs, inbox
addresses) and answers *is this asset in scope?* for any candidate — a domain, URL,
IP, or list of them — entirely offline, from files you provide.

## Problem

Scope rules live in prose and marketing pages: "all of `*.example.com` except
`admin.example.com`, plus the API at `https://api.other.org/v1`." Manually re-reading
that per asset wastes time and mistakes out-of-scope targets for in-scope ones, which
is both an authorization problem and a wasted-report problem.

## Features

- **`parse`** — summarize a scope file: counts by action and asset kind, with a table.
- **`check`** — verdict per asset: `in-scope`/`out-of-scope` plus *which entry* decided it.
- **`batch`** — check a whole asset list (one per line) at once; exits 1 if any is out.
- Excludes always beat includes; matching covers wildcard subdomains, scheme+host+path
  URLs, CIDR ranges for IPs, and exact domains/emails.
- `--json-out` everywhere for piping into other tooling.

## Example output

```
$ scopematrix check examples/program-scope.txt www.example.com admin.example.com
in-scope      www.example.com      (matched include '*.example.com')
out-of-scope  admin.example.com    (matched exclude 'admin.example.com')
```

Full transcripts: [`results/demo-output.txt`](results/demo-output.txt).

## Architecture summary

A pure `scope.py` module (parse → `Scope` dataclass, `check()` → verdict dict) with all
file I/O and terminal rendering kept in `cli.py`. No network access anywhere.
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Requirements

- Python ≥ 3.10
- `click`, `rich` (installed automatically)

## Installation

```shell
pip install -e .
```

## Quick start

```shell
scopematrix parse examples/program-scope.txt
scopematrix check examples/program-scope.txt shop.example.com
scopematrix batch examples/program-scope.txt examples/assets.txt
```

## Usage examples

Scope file format (see [docs/USAGE.md](docs/USAGE.md) for the full grammar):

```
+ *.example.com          # wildcard: apex + all subdomains
- admin.example.com      # exclude — always wins
+ https://api.other.org/v1
+ 203.0.113.0/24
+ reports@bugzilla.example.org
```

Pipe verdicts into other tools:

```shell
scopematrix batch scope.txt candidates.txt --json-out | jq '.verdicts[] | select(.verdict=="in-scope")'
```

## Configuration

No config file. The scope file *is* the configuration; flags are `--json-out` only.

## Testing

```shell
pip install -e . pytest
pytest -q          # 11 tests: parsing, wildcard/exclude precedence, CIDR, CLI exit codes
```

## Project structure

```
scopematrix/
├─ src/scopematrix/{__init__,cli,scope}.py
├─ tests/test_m.py
├─ examples/{program-scope.txt,assets.txt}
├─ docs/{ARCHITECTURE,USAGE,PROJECT_SPEC}.md
├─ results/demo-output.txt
├─ RESULTS.md
└─ .github/workflows/ci.yml
```

## Limitations

- Grammar is the line format documented above, not a HackerOne/Bugcrowd export
  importer (roadmap item).
- CIDR entries match literal IPs only; hostnames are never resolved to IPs.
- Wildcard matching is textual (`host == base` or `host.endswith("." + base)`);
  it does not implement full PSL-aware registrable-domain logic.

## Roadmap

- Importers for HackerOne/Bugcrowd/Intigriti scope exports.
- Diff two scope snapshots (program scope drift).
- CSV/JSON output columns for recon pipelines.

## Security notes

This tool decides *what you are allowed to touch* — treat its output as advisory and
the program's published policy as authoritative. It performs no network requests and
contacts no targets. See [SECURITY.md](SECURITY.md).

## License

MIT — see [LICENSE](LICENSE).