"""Built-in file batch rename commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from uuid import uuid4

import typer
from rich.console import Console
from rich.table import Table

from nexuscli.core.plugin_contract import CliPluginBase, CommandMetadata


console = Console()
app = typer.Typer(help="File operation commands.")


@dataclass(slots=True, frozen=True)
class RenameItem:
    """A single rename operation."""

    source: Path
    target: Path


def collect_candidates(
    directory: Path,
    recursive: bool,
    include_files: bool,
    include_dirs: bool,
) -> list[Path]:
    """Collect candidate paths for rename."""
    iterator = directory.rglob("*") if recursive else directory.iterdir()
    candidates: list[Path] = []

    for path in iterator:
        if path.is_file() and include_files:
            candidates.append(path)
        elif path.is_dir() and include_dirs:
            candidates.append(path)

    # Rename deeper paths first so parent directory rename does not break child paths.
    return sorted(candidates, key=lambda p: len(p.parts), reverse=True)


def build_rename_plan(
    candidates: list[Path],
    pattern: str,
    replacement: str,
    ignore_case: bool,
) -> list[RenameItem]:
    """Build source->target plan from regex replacement."""
    flags = re.IGNORECASE if ignore_case else 0
    compiled = re.compile(pattern, flags=flags)

    plan: list[RenameItem] = []
    for source in candidates:
        new_name = compiled.sub(replacement, source.name)
        if new_name == source.name:
            continue
        plan.append(RenameItem(source=source, target=source.with_name(new_name)))

    return plan


def detect_plan_conflicts(plan: list[RenameItem]) -> list[str]:
    """Detect target collisions before applying renames."""
    errors: list[str] = []
    targets: dict[Path, Path] = {}
    sources = {item.source for item in plan}

    for item in plan:
        owner = targets.get(item.target)
        if owner is not None and owner != item.source:
            errors.append(
                f"Target collision: '{owner}' and '{item.source}' both map to '{item.target}'"
            )
            continue
        targets[item.target] = item.source

        if item.target.exists() and item.target not in sources:
            errors.append(
                f"Target already exists and is not part of rename set: '{item.target}'"
            )

    return errors


def apply_rename_plan(plan: list[RenameItem]) -> None:
    """Apply rename plan in two phases to avoid path collisions."""
    temp_map: dict[Path, Path] = {}

    try:
        for item in plan:
            temp_path = item.source.with_name(f"{item.source.name}.nexuscli_tmp_{uuid4().hex}")
            item.source.rename(temp_path)
            temp_map[temp_path] = item.target

        for temp_path, target_path in temp_map.items():
            temp_path.rename(target_path)
    except Exception:
        # Best-effort rollback to reduce risk of leaving temporary names.
        for temp_path, target_path in temp_map.items():
            if temp_path.exists():
                original = Path(str(temp_path).split(".nexuscli_tmp_")[0])
                try:
                    temp_path.rename(original)
                except Exception:
                    pass
            elif target_path.exists():
                original = Path(str(temp_path).split(".nexuscli_tmp_")[0])
                try:
                    target_path.rename(original)
                except Exception:
                    pass
        raise


def render_preview(plan: list[RenameItem], limit: int) -> None:
    """Render a preview table for planned renames."""
    table = Table(title="Rename Preview")
    table.add_column("Source")
    table.add_column("Target")

    for item in plan[:limit]:
        table.add_row(str(item.source), str(item.target))

    console.print(table)

    if len(plan) > limit:
        typer.echo(f"... {len(plan) - limit} more items not shown")


@app.command("rename")
def batch_rename(
    directory: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        help="Directory containing files or folders to rename.",
    ),
    pattern: str = typer.Option(..., "--pattern", "-p", help="Regex pattern to match."),
    replacement: str = typer.Option(
        ...,
        "--replacement",
        "-r",
        help="Regex replacement string.",
    ),
    recursive: bool = typer.Option(False, "--recursive", help="Scan subdirectories."),
    include_files: bool = typer.Option(True, "--files/--no-files", help="Include files."),
    include_dirs: bool = typer.Option(False, "--dirs/--no-dirs", help="Include directories."),
    ignore_case: bool = typer.Option(False, "--ignore-case", help="Case-insensitive regex."),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Preview by default."),
    preview_limit: int = typer.Option(50, "--preview-limit", min=1, max=1000),
) -> None:
    """Batch rename file or directory names with regex replace."""
    if not include_files and not include_dirs:
        raise typer.BadParameter("At least one of --files or --dirs must be enabled")

    candidates = collect_candidates(
        directory=directory,
        recursive=recursive,
        include_files=include_files,
        include_dirs=include_dirs,
    )
    plan = build_rename_plan(
        candidates=candidates,
        pattern=pattern,
        replacement=replacement,
        ignore_case=ignore_case,
    )

    if not plan:
        typer.echo("No matching names found. Nothing to rename.")
        return

    conflicts = detect_plan_conflicts(plan)
    if conflicts:
        typer.echo("Conflict detected. Rename aborted:")
        for issue in conflicts:
            typer.echo(f"- {issue}")
        raise typer.Exit(code=2)

    render_preview(plan, preview_limit)

    if dry_run:
        typer.echo("Dry-run mode. No file has been modified.")
        return

    apply_rename_plan(plan)
    typer.echo(f"Applied {len(plan)} rename operations.")


class FileCommandsPlugin(CliPluginBase):
    """Expose file command module."""

    @property
    def metadata(self) -> CommandMetadata:
        return CommandMetadata(
            plugin_id="builtin.file",
            command_name="file",
            help_text="File operation commands",
            version="0.1.0",
            min_cli_version=">=0.1.0",
        )

    @property
    def typer_app(self) -> typer.Typer:
        return app
