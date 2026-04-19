from __future__ import annotations

from pathlib import Path

from share_cli.commands.file_batch_rename import (
    build_rename_plan,
    collect_candidates,
    detect_plan_conflicts,
)


def test_build_rename_plan_and_conflict_detection(tmp_path: Path) -> None:
    (tmp_path / "report_01.txt").write_text("x", encoding="utf-8")
    (tmp_path / "report_02.txt").write_text("x", encoding="utf-8")

    candidates = collect_candidates(
        directory=tmp_path,
        recursive=False,
        include_files=True,
        include_dirs=False,
    )
    plan = build_rename_plan(
        candidates=candidates,
        pattern=r"report_(\d+)",
        replacement=r"doc_\1",
        ignore_case=False,
    )

    assert len(plan) == 2
    assert not detect_plan_conflicts(plan)


def test_detect_target_collision(tmp_path: Path) -> None:
    (tmp_path / "a_1.txt").write_text("x", encoding="utf-8")
    (tmp_path / "a_2.txt").write_text("x", encoding="utf-8")

    candidates = collect_candidates(
        directory=tmp_path,
        recursive=False,
        include_files=True,
        include_dirs=False,
    )
    plan = build_rename_plan(
        candidates=candidates,
        pattern=r"a_\d",
        replacement="same",
        ignore_case=False,
    )

    conflicts = detect_plan_conflicts(plan)
    assert conflicts
