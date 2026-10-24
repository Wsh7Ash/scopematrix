# PROJECT SPEC — scopematrix

| Field | Value |
|---|---|
| Name | `scopematrix` |
| Category | bug-bounty-tooling |
| Target user | Bug-bounty hunters deciding whether an asset is in scope |
| Problem | Program scopes are prose with wildcards and exceptions; manual re-reading is slow and error-prone. |
| Solution | Parse a scope file into structured include/exclude entries and answer in-scope/out-of-scope verdicts for any asset, offline. |
| Core workflow | write scope file -> parse to verify -> check one asset or batch a list -> pipe JSON downstream |
| Stack | Python >=3.10, click, rich |
| Test strategy | tests/test_m.py covers counts/kinds, wildcard subdomains, exclude precedence, URL scheme+path rules, CIDR vs hostname, malformed files, and CLI exit codes 0/1/2. |
| Demo strategy | `logs/2026-10-24/run_demos.py` runs the real workflow and captures `results/demo-output.txt` with asserted exit codes |
| Safety | Entirely file-based. No target is contacted; verdicts are advisory and the program's published policy remains authoritative. |
| Definition of done | install + pytest + CLI smoke + demo transcript + secret scan all pass; docs (README, ARCHITECTURE, USAGE, CHANGELOG, CONTRIBUTING, SECURITY) present; pushed with green CI |

## Must-have features

- scopematrix parse examples/program-scope.txt
- scopematrix check examples/program-scope.txt shop.example.com
- Exit-code contract (0/1/2) usable from CI
- `--json-out` machine-readable output

## Nice-to-have (deferred)

- See README Roadmap.
