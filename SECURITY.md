# Security policy

## Reporting a vulnerability privately

Report undisclosed vulnerabilities through [GitHub Private Vulnerability Reporting](https://github.com/shardbase-md/shardbase/security/advisories/new). Sign in to GitHub and use **Report a vulnerability** on the repository's **Security → Advisories** page to submit a private report.

Do **not** open a public GitHub Issue for an undisclosed vulnerability or publish exploit details before coordinated handling. Do not send real private knowledge, passwords, backup passphrases, tokens, secrets, or unnecessary personal data as proof-of-concept material. Use the smallest synthetic reproduction that demonstrates the issue whenever possible.

Ordinary correctness bugs may use [public Issues](https://github.com/shardbase-md/shardbase/issues) when they do not expose sensitive details or create a security or privacy risk.

## Security-support scope

During Foundation, the currently maintained development codebase is the security-support target. Historical commits and branches are not promised security support, and backports are not currently promised.

A formal supported-release matrix will be introduced when Shardbase has versioned releases that warrant one. This policy does not establish long-term-support branches or production response guarantees.

## Security-sensitive areas

Reports are especially relevant in these areas:

- **Private-data exposure:** accidental inclusion or publication of private live knowledge or `.obsidian/`; leakage of user-owned state through logs, tests, fixtures, examples, diagnostics, backup handling, or framework artifacts; unexpected external transmission of local knowledge.
- **Backup and restore:** authentication bypass, encryption misuse, loss of confidentiality or integrity, unsafe passphrase handling, unsafe backup inventory/path handling, restore conflict or overwrite flaws, plaintext exposure, or publication of unauthenticated data.
- **Filesystem and path safety:** path traversal, symlink or containment escapes, writes outside authorized boundaries, unsafe file replacement or deletion, or filename/path handling that targets unintended files.
- **Knowledge preservation with security impact:** unintended destructive overwrite of canonical user knowledge or bypass of collision/refusal safeguards that creates a confidentiality or integrity risk. Not every ordinary data-correctness bug is a security vulnerability.
- **Dependencies:** vulnerabilities that meaningfully affect Shardbase's actual threat surface or supported tooling. Explain the relevant usage and impact; an upstream CVE does not by itself demonstrate exploitability in Shardbase.

The [tooling guide](app/Scripts/README.md), including its [backup and restore behavior and limits](app/Scripts/README.md#encrypted-backup-and-restore), and the [backup format contract](app/Scripts/BACKUP_FORMAT.md) describe the current implementation. This policy does not replace those contracts or extend their guarantees.

## What to include

Provide concise, non-sensitive information:

- affected component, path, or command;
- security or privacy impact;
- minimal reproduction using synthetic data;
- relevant platform and Python version;
- observed behavior and expected safe behavior;
- known prerequisites or limitations.

Do not attach personal vaults, real databases, real encrypted backups, real passphrases, or unrelated secrets. Synthetic files and sanitized diagnostics should be sufficient to explain the issue without exposing user-owned knowledge.

## Response and disclosure

Reports will be reviewed based on severity, reproducibility, and maintainer availability. The project aims to communicate material findings and remediation status through the private reporting channel. Response and remediation timing may vary during Foundation; no fixed acknowledgment or remediation window is promised.

When a valid issue is confirmed, coordinate disclosure through the private report so remediation and public details can be handled together.
