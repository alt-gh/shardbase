# Contributing to Shardbase

This guide is for people changing the **Shardbase framework repository**. Contributors use a Git clone or fork of the public framework and work on a focused branch.

Contributing to Shardbase and using Shardbase privately are intentionally different workflows. For a private instance, download the repository ZIP and follow [Get Started](README.md#get-started) and the [runtime setup guide](app/Scripts/README.md#runtime-setup). Contributor cloning and development checks are not prerequisites for private use.

## Read the relevant authorities

Start with the [System Specification](app/Docs/Shard%20System%20Specification.md), the highest framework authority. Its [authority order](app/Docs/Shard%20System%20Specification.md#11-authority-order) governs structural and canonical decisions. For database-specific changes, read the target database's root `Database.md`, which owns its local semantics. For blueprint work, read the blueprint's manifest, such as the [Games blueprint contract](app/Blueprints/Games/Database.md); it does not replace a live database's own contract.

Supporting documents have separate roles:

- [AGENTS.md](AGENTS.md) owns repository-agent operating guidance.
- [Scripts/README.md](app/Scripts/README.md) describes current tooling setup, behavior, and validation limits.
- [Architectural Decision Records](app/Docs/ADR/) preserve architectural rationale and historical context; they do not supersede current normative rules.

This contributor guide describes the contribution process. It does not establish another architectural authority.

## Protect private knowledge

`app/Knowledge/` is private by default. It combines Shardbase-managed live database package files with user-owned Inbox, Data, and Views; `.obsidian/` is also user-owned local state. Do not use private-instance content as a source for public contributions.

Use synthetic subjects and values in tests, fixtures, documentation, examples, screenshots, CLI help, blueprints, Registry resources, framework scripts, and issue or PR descriptions. Do not copy private material into those surfaces. Even a publicly known title or name selected from a private instance is user-derived context: replace it and its related filenames, links, aliases, and assertions with a consistent synthetic example.

Local access does not authorize transmitting private knowledge to external services. External exposure requires the user's deliberate choice or an already-authorized workflow. Review the complete diff and any attachments for private content before sharing them. See [AGENTS.md](AGENTS.md#user-owned-data-and-privacy) for the repository's privacy guidance.

For undisclosed vulnerabilities, follow [SECURITY.md](SECURITY.md); do not open a public Issue containing sensitive details.

## Set up development

Development requires **Python 3.10 or newer**, as recorded in [pyproject.toml](pyproject.toml). The [CI workflow](.github/workflows/ci.yml) runs Ruff on Ubuntu with Python 3.10 and the full tests plus CLI smoke check on Ubuntu with Python 3.10 and 3.14, and Windows with Python 3.14. A separate macOS/Python 3.14 bootstrap smoke job exercises disposable ZIP-style copies, actual dependency installation, the native launcher, reruns, retargeting, collision refusal, and instance preservation. Native Windows launcher argument forwarding is exercised in the Windows tests. These are selected verification environments, not an exhaustive list of supported intermediate Python versions.

Keep virtual environments, installed dependencies, bytecode, caches, temporary test instances, and other generated runtime/build state outside the repository and every knowledge vault. Do not create a repository-local `.venv/`. See the [runtime guide](app/Scripts/README.md#runtime-setup) for platform-specific details.

From the repository root, create an external environment with a Python 3.10+ interpreter. Replace `<external-venv>` with an actual external path:

```sh
python -B -m venv "<external-venv>"
```

Activate that environment so `python` refers to its interpreter. Alternatively, use its full interpreter path for each command (`bin/python` on macOS/Linux or `Scripts/python.exe` on Windows).

Before running development commands, set `PYTHONDONTWRITEBYTECODE=1`, `PIP_NO_CACHE_DIR=1`, and `PIP_NO_COMPILE=1`. For example, in a POSIX shell:

```sh
export PYTHONDONTWRITEBYTECODE=1
export PIP_NO_CACHE_DIR=1
export PIP_NO_COMPILE=1
```

Use your shell's equivalent environment-variable syntax on Windows. Keep `TMPDIR` or its platform equivalent external if you customize it. Run Python with `-B` or `PYTHONDONTWRITEBYTECODE=1` whenever it touches the repository.

Ruff defaults to `~/.cache/shardbase/ruff`, outside the repository, through `pyproject.toml`. To select another external location, use `--cache-dir`; the configured path takes precedence over `RUFF_CACHE_DIR`. Use `--no-cache` to disable caching entirely.

Install runtime and development dependencies separately:

```sh
python -m pip install -r app/Scripts/requirements.txt
python -m pip install -r requirements-dev.txt
```

[Runtime requirements](app/Scripts/requirements.txt) supply the CLI dependencies; [development requirements](requirements-dev.txt) pin Ruff. Keep development-only dependencies separate. The scripts run directly from `app/Scripts/`; Shardbase is not configured as an installable Python package.

## Run the local quality gate

Before opening a PR, run the complete applicable gate from the repository root using the external environment and settings above:

```sh
python -m ruff check .
python -B -m unittest discover -s tests -p "test_*.py" -v
python -B app/Scripts/shardbase.py commands
git diff --check
```

Report any check you could not run and why. Ruff is configured for fundamental errors, Pyflakes checks, and import ordering (`E4`, `E7`, `E9`, `F`, `I`); no formatter is configured. Tests live in [tests/](tests/) with synthetic data in [tests/fixtures/](tests/fixtures/). A passing validator proves only its [documented checks](app/Scripts/README.md#read-only-validator), not complete database-semantic validity or Foundation compliance.

## Keep changes focused

Solve the requested problem with the smallest coherent change. Avoid unrelated cleanup, refactoring, or mass reformatting. Preserve existing valid representations unless the intended change explicitly modifies them.

Add regression tests for refactors or behavioral fixes. When externally visible behavior changes, update the relevant documentation in the same commit. Put normative changes in their owning authority and reference them from supporting documents.

Use focused commit subjects:

```text
<scope>: <imperative summary>
```

For example:

```text
docs: clarify contributor validation
validate: improve collision diagnostics
cli: clarify command help
```

For substantial commits, include a concise body capturing meaningful design, compatibility, preservation, privacy, or migration context and deliberately deferred behavior.

Keep PRs focused too. Describe what changed, why it is needed, validation performed, tests added or updated, and documentation changes. Include privacy, compatibility, and migration implications, known limitations, and intentionally deferred work when applicable. Routine changes do not need empty checklist sections.

CI must be green before merge unless a maintainer explicitly decides to handle an infrastructure failure separately.

## Propose architectural changes before implementation

Small bug fixes, tests, documentation corrections, refactors that preserve behavior, and true clarifications may proceed directly to a focused PR.

Begin with a [GitHub Issue](https://github.com/shardbase-md/shardbase/issues) for proposed changes to universal architecture, canonical structural schema, compatibility/versioning boundaries, migration behavior, privacy or ownership boundaries, structural invariants, breaking behavior, or similarly durable contracts spanning the framework. Describe the problem, proposed outcome, alternatives, and tradeoffs so they can be discussed before implementation or changes to normative text.

An Issue does not establish architecture. Accepted universal normative behavior belongs in the System Specification and must follow its [compatibility and versioning rules](app/Docs/Shard%20System%20Specification.md#14-architectural-change-versioning-and-migration). Database-local semantics belong in the affected `Database.md`.

### When to write an ADR

Use an ADR selectively for a durable architectural direction, a choice among credible alternatives with meaningful tradeoffs, a compatibility or migration boundary, or rationale that would be difficult to reconstruct from the final specification alone.

An ADR is normally unnecessary for routine bug fixes, straightforward implementation details, ordinary documentation cleanup, small behavior-preserving refactors, or true clarifications that leave the normative contract unchanged.

ADRs record rationale and historical decision context. Current normative rules remain in the System Specification. When an ADR is warranted, follow the existing numbered filenames and record conventions in [app/Docs/ADR/](app/Docs/ADR/).
