# Usage — scopematrix

## Install

```shell
pip install -e .
```

## Commands

```shell
scopematrix --help
```

## Examples

### Summarize a scope file

```shell
scopematrix parse examples/program-scope.txt
```

### Single verdict

```shell
scopematrix check examples/program-scope.txt shop.example.com
```

### Batch a candidate list

```shell
scopematrix batch examples/program-scope.txt examples/assets.txt
```

### JSON filtered by jq

```shell
scopematrix batch scope.txt candidates.txt --json-out | jq '.verdicts[] | select(.verdict=="in-scope")'
```

## Scope file grammar

One entry per line; `#` starts a comment; blank lines ignored.

```
+ pattern        # include
- pattern        # exclude (always wins over includes)
```

Patterns classify as: `*.example.com` (wildcard), `example.com` (domain),
`https://host/path` (URL — scheme, host and path prefix must match),
`203.0.113.0/24` (CIDR — matches IPs only), `user@example.org` (email).

An asset is in scope iff it matches at least one include and no exclude.
Assets may be hostnames, URLs, IPs, or emails.

## Validation gates

- **install**: `pip install -e . (fresh venv)`
- **unit tests**: `pytest -q`
- **CLI smoke**: `scopematrix --help; scopematrix parse examples/program-scope.txt`
- **demo run**: `logs/2026-10-24/run_demos.py -> results/demo-output.txt`
- **secret scan**: `no tokens/keys/.env in tree`

## Exit codes

- `0` — success / no findings at or above threshold
- `1` — findings present, or validation cases failed
- `2` — usage error, unreadable input, or rejected target
