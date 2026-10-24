# Security Policy

## Authorized use

`scopematrix` is a **defensive tool for systems you own or are explicitly authorized to
test**. Do not point it at third-party infrastructure without written permission;
unauthorized security testing violates computer-misuse laws in most jurisdictions.

`scopematrix` is entirely offline: it reads local scope and asset files and contacts no hosts. Its verdicts are advisory — the program's published scope policy is always authoritative.

## Reporting a vulnerability

If you find a vulnerability or unsafe default in `scopematrix` itself, please open a
private security advisory on the GitHub repository (or open an issue describing the
problem at a high level if you cannot use advisories). We will acknowledge within
72 hours and coordinate a fix before public disclosure.

## Secrets

`scopematrix` stores no credentials and requires none. Do not commit real tokens, cookies
or keys to the spec/example files in this repository; `.gitignore` excludes `.env`
and common key material.
