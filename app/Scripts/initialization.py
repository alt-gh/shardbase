"""Guided, preservation-oriented initialization for a Shardbase instance."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class HealthAssessment:
    """Path-specific interpretation of structured doctor results."""

    blockers: tuple
    warnings: tuple


COMMON_BLOCKERS = {
    "framework.root",
    "framework.files",
    "framework.spec",
    "runtime.python",
    "runtime.location",
    "runtime.requirements",
}


def classify_health(results, workflow: str, *, post_operation: bool = False) -> HealthAssessment:
    """Classify doctor findings for one workflow without parsing rendered text.

    New-database creation requires readable, structurally sound existing
    knowledge. Restore deliberately does not: authenticated additive restore can
    be the operation that completes partial knowledge. After restore, remaining
    knowledge failures are verification failures and therefore block success.
    """
    if workflow not in {"new", "restore", "setup"}:
        raise ValueError(f"Unknown initialization workflow: {workflow}")
    blockers = []
    warnings = []
    for result in results:
        if result.severity == "WARN":
            warnings.append(result)
            continue
        if result.severity != "FAIL":
            continue
        blocks = result.code in COMMON_BLOCKERS
        if workflow == "new":
            blocks = blocks or result.code in {"framework.blueprints", "runtime.pyyaml"}
            blocks = blocks or result.category == "Knowledge"
        elif workflow == "restore":
            blocks = blocks or result.code in {"runtime.cryptography", "runtime.pyyaml"}
            blocks = blocks or (post_operation and result.category == "Knowledge")
        else:
            blocks = blocks or result.category in {"Framework", "Runtime"}
        (blockers if blocks else warnings).append(result)
    return HealthAssessment(tuple(blockers), tuple(warnings))


def summarize_health(results, ui, workflow: str, *, post_operation: bool = False) -> HealthAssessment:
    """Render only actionable findings plus a concise doctor summary."""
    assessment = classify_health(results, workflow, post_operation=post_operation)
    ui.section("Health")
    visible = [result for result in results if result.severity in {"WARN", "FAIL"}]
    if not visible:
        print("  No blocking issues or warnings found.")
    else:
        blocking_ids = {id(result) for result in assessment.blockers}
        for result in visible:
            if id(result) in blocking_ids:
                label = "BLOCK"
            elif result.severity == "FAIL":
                label = "REVIEW"
            else:
                label = result.severity
            print(f"  {label:<5} {result.code}: {result.summary}")
            if result.detail:
                print(f"        {result.detail}")
        print(
            f"  {len(assessment.blockers)} blocking issue"
            f"{'s' if len(assessment.blockers) != 1 else ''}; "
            f"{len(assessment.warnings)} non-blocking finding"
            f"{'s' if len(assessment.warnings) != 1 else ''}."
        )
    return assessment


def preflight(root: Path, ui, workflow: str) -> bool:
    from doctor import diagnose

    assessment = summarize_health(diagnose(root), ui, workflow)
    if assessment.blockers:
        print("\n  Guided setup cannot safely continue with this choice.")
        print("  Review the findings above and run shardbase doctor for the full report.")
        return False
    return True


def guided_restore(
    root: Path,
    *,
    archive: Path | None = None,
    password_file: Path | None = None,
    staging_dir: Path | None = None,
    dry_run: bool = False,
    ui=None,
):
    """Shared interactive restore presentation for `restore` and `init`."""
    from backup_restore import external, instance, read_password, restore

    root = instance(root)
    if password_file is not None:
        password_file = external(password_file, root, "Password file")
    source = archive or Path(input("Backup file: ").strip()).expanduser()
    password = read_password(password_file, confirm=False)
    result = restore(root, source, password, staging_dir, dry_run=dry_run)
    verb = "Restore checked" if dry_run else "Restore complete"
    action = "to add" if dry_run else "added"
    print(
        f"{verb}: {result['files_added']} files {action}, "
        f"{result['files_unchanged']} identical files preserved, "
        f"{result['git_files']} excluded Git-backed files verified."
    )
    if dry_run:
        print("No knowledge was written. This check does not certify database-semantic or structural validity.")
    else:
        print("Knowledge transferred unchanged. This does not certify database-semantic or structural validity.")
    return result


def structural_issues(root: Path, databases: Iterable[Path] | None = None):
    """Run the authoritative validator over selected or discovered live roots."""
    from validate_shardbase import discover_databases, validate_database

    issues = []
    selected = list(databases) if databases is not None else discover_databases(root / "app", issues)
    for database in selected:
        issues.extend(validate_database(database))
    return selected, issues


def render_structural_verification(root: Path, databases: list[Path], issues, ui) -> bool:
    ui.section("Structural verification")
    if not issues:
        count = len(databases)
        print(f"  Structural checks passed for {count} live database{'s' if count != 1 else ''}.")
        print("  Database-semantic validity is not fully automated.")
        return True
    print(f"  Structural validation found {len(issues)} blocking issue{'s' if len(issues) != 1 else ''}.")
    for issue in issues:
        print(f"  {issue.render(root)}")
    print("  Run shardbase validate and inspect the affected database(s).")
    return False


def initialize_new_instance(root: Path, ui) -> int:
    from database_creation import available_blueprints, create_database
    from database_preparation import database_sources
    from doctor import diagnose

    if not preflight(root, ui, "new"):
        return 1
    existing = database_sources(root, live_only=True)
    ui.section("Existing live databases")
    if existing:
        for source in existing:
            name = source.metadata.get("database_name", source.metadata["database_id"])
            print(f"  {name} ({source.metadata['database_id']})")
    else:
        print("  None found.")
    existing_ids = {source.metadata["database_id"] for source in existing}
    choices = [item for item in available_blueprints(root) if item.database_id not in existing_ids]
    if not choices:
        print("\n  No additional supplied blueprint is currently available to create.")
        print("  Existing knowledge was not changed.")
        return 0
    selected = ui.choose("Choose a database blueprint", [
        (item.database_id, item.database_name, "Create a new private live database from this supplied blueprint.")
        for item in choices
    ])
    blueprint = next(item for item in choices if item.database_id == selected)
    destination = create_database(root, selected)
    print(f"\n  Database creation completed: {destination.relative_to(root)}")
    try:
        databases, issues = structural_issues(root, [destination])
        valid = render_structural_verification(root, databases, issues, ui)
        health = summarize_health(diagnose(root), ui, "new", post_operation=True)
    except KeyboardInterrupt:
        print("\n  Post-creation verification was cancelled.")
        print("  The new database was preserved for inspection.")
        raise
    except (ValueError, OSError, UnicodeError, RuntimeError) as error:
        print(f"\n  Post-creation verification could not complete: {error}")
        print("  The new database was preserved for inspection.")
        return 1
    if not valid or health.blockers:
        print("\n  Database creation completed, but post-creation verification found a blocking issue.")
        print("  The new database was preserved for inspection.")
        return 1
    print("\nShardbase is ready.")
    print("  External runtime ready")
    git = root / ".git"
    print("  Git-managed/development-style instance" if git.exists() or git.is_symlink()
          else "  Private ZIP-style instance")
    print("  Knowledge boundary ready")
    print(f"  {blueprint.database_name} database created")
    print("  Structural validation passed")
    print(f"\nOpen this folder in Obsidian:\n  {root}")
    print("\nNext:\n  shardbase create new")
    return 0


def initialize_from_backup(root: Path, ui) -> int:
    from doctor import diagnose

    if not preflight(root, ui, "restore"):
        return 1
    guided_restore(root, ui=ui)
    try:
        databases, issues = structural_issues(root)
        valid = render_structural_verification(root, databases, issues, ui)
        health = summarize_health(diagnose(root), ui, "restore", post_operation=True)
    except KeyboardInterrupt:
        print("\n  Post-restore verification was cancelled.")
        print("  Restored files were preserved.")
        raise
    except (ValueError, OSError, UnicodeError, RuntimeError) as error:
        print(f"\n  Post-restore verification could not complete: {error}")
        print("  Restored files were preserved.")
        return 1
    if not valid or health.blockers:
        print("\n  Restore completed successfully, but post-restore verification found a blocking issue.")
        print("  Restored files were preserved.")
        return 1
    print("\nShardbase is ready.")
    print("  Encrypted backup restored")
    print("  Structural validation passed")
    print("  Database-semantic validity is not fully automated.")
    print(f"\nOpen this folder in Obsidian:\n  {root}")
    return 0


def finish_setup(root: Path, ui) -> int:
    from doctor import diagnose

    assessment = summarize_health(diagnose(root), ui, "setup")
    if assessment.blockers:
        print("\n  Tooling setup has blocking health issues. No knowledge was created.")
        return 1
    print("\nShardbase tooling is ready.")
    print("  No knowledge was created.")
    print("  Run shardbase init again whenever you want to create or restore knowledge.")
    return 0


def initialize(root: Path, ui) -> int:
    root = root.expanduser().resolve(strict=True)
    print("Shardbase setup\n")
    workflow = ui.choose("What would you like to do?", [
        ("new", "Start a new private instance", "Choose one available database blueprint."),
        ("restore", "Restore an encrypted backup", "Authenticate and add compatible saved knowledge."),
        ("setup", "Finish setup without creating knowledge", "Check tooling and leave knowledge untouched."),
    ])
    if workflow == "new":
        return initialize_new_instance(root, ui)
    if workflow == "restore":
        return initialize_from_backup(root, ui)
    return finish_setup(root, ui)
