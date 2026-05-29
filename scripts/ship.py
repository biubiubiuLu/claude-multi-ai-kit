#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from ai_common import (
    KIT_DIR,
    default_test_command,
    ensure_parent,
    load_environment,
    load_project_config,
    project_root,
    run_shell,
    slugify,
    timestamp,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the multi-AI ship workflow")
    parser.add_argument("feature", nargs="+", help="Feature or task description")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--no-frontend", action="store_true")
    parser.add_argument("--frontend", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--skip-coder", action="store_true")
    parser.add_argument("--skip-review", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Do not call external AI CLIs; write placeholder artifacts")
    parser.add_argument("--allow-kit-repo", action="store_true", help="Allow running against the kit repository itself")
    parser.add_argument("--timeout", type=int, default=int(os.getenv("AI_TIMEOUT", "120")))
    return parser.parse_args()


def script(name: str) -> Path:
    return KIT_DIR / "scripts" / name


def write_prompt(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def run_wrapper(
    wrapper: str,
    task: str,
    prompt_file: Path,
    mode: str,
    out: Path,
    cwd: Path,
    files: list[Path] | None = None,
    timeout: int = 120,
) -> None:
    command = [
        sys.executable,
        str(script(wrapper)),
        "--task",
        task,
        "--prompt-file",
        str(prompt_file),
        "--mode",
        mode,
        "--out",
        str(out),
        "--cwd",
        str(cwd),
        "--timeout",
        str(timeout),
    ]
    if files:
        command += ["--files", *[str(path) for path in files]]
    proc = subprocess.run(command, cwd=str(cwd), text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{wrapper} failed with exit code {proc.returncode}")


def write_dry_run_artifact(path: Path, title: str, body: str = "") -> None:
    ensure_parent(path)
    path.write_text(
        f"# {title}\n\n"
        f"> dry-run: external AI CLI was not called.\n\n"
        f"{body.strip()}\n",
        encoding="utf-8",
    )


def project_files_for_context(root: Path, config: dict) -> list[Path]:
    candidates = [
        root / "CLAUDE.md",
        root / "AGENTS.md",
        root / "README.md",
        root / "pom.xml",
        root / "package.json",
        root / "pyproject.toml",
    ]
    plan_doc = root / "docs" / "historical-mail-automation-plan.md"
    if plan_doc.exists():
        candidates.append(plan_doc)
    return [path for path in candidates if path.exists()]


def git_diff(root: Path) -> str:
    proc = run_shell("git diff --stat && git diff -- src/main src/test docs pom.xml package.json pyproject.toml", root)
    return (proc.stdout or "")[-60000:]


def normalize_patch_file(patch_file: Path) -> None:
    raw = patch_file.read_text(encoding="utf-8")
    lines = raw.splitlines()
    start = next((idx for idx, line in enumerate(lines) if line.startswith("diff --git ")), None)
    if start is None:
        return
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx] == "```":
            end = idx
            break
    patch = "\n".join(lines[start:end]).rstrip() + "\n"
    if patch != raw:
        raw_file = patch_file.with_suffix(patch_file.suffix + ".raw")
        raw_file.write_text(raw, encoding="utf-8")
        patch_file.write_text(patch, encoding="utf-8")


def apply_patch_file(root: Path, patch_file: Path) -> bool:
    if not patch_file.exists() or not patch_file.read_text(encoding="utf-8").strip():
        return False
    normalize_patch_file(patch_file)
    check = subprocess.run(
        ["git", "apply", "--check", str(patch_file)],
        cwd=str(root),
        text=True,
        capture_output=True,
    )
    if check.returncode != 0:
        reverse_check = subprocess.run(
            ["git", "apply", "--reverse", "--check", str(patch_file)],
            cwd=str(root),
            text=True,
            capture_output=True,
        )
        if reverse_check.returncode == 0:
            print("Patch already appears to be applied:", patch_file)
            return True
        print("Patch check failed; leaving patch file for manual review:", patch_file)
        print(check.stderr)
        return False
    apply = subprocess.run(["git", "apply", str(patch_file)], cwd=str(root), text=True)
    if apply.returncode != 0:
        raise RuntimeError(f"git apply failed for {patch_file}")
    return True


def main() -> None:
    load_environment()
    args = parse_args()
    root = project_root(args.repo)
    if root == KIT_DIR and not args.allow_kit_repo:
        raise RuntimeError(
            "Refusing to run against claude-multi-ai-kit itself. "
            "Run from the target project directory or pass --repo /path/to/project. "
            "Use --allow-kit-repo only when developing the kit."
        )
    config = load_project_config(root)
    feature = " ".join(args.feature)
    task = slugify(feature)
    stamp = timestamp()
    plans_dir = root / "docs" / "plans"
    reviews_dir = root / "docs" / "reviews"
    work_dir = root / "docs" / "multi-ai-runs" / f"{stamp}-{task}"
    plans_dir.mkdir(parents=True, exist_ok=True)
    reviews_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    plan_prompt = work_dir / "planner-prompt.md"
    plan_file = plans_dir / f"{stamp}-{task}.md"
    context_files = project_files_for_context(root, config)
    write_prompt(
        plan_prompt,
        f"""
        Create an implementation plan for this project.

        Feature:
        {feature}

        Project root:
        {root}

        Requirements:
        - Respect existing project patterns and tests.
        - If frontend is involved, include detailed frontend steps.
        - Include files likely to change, test plan, risks, and rollback.
        - Output Markdown only.
        """,
    )
    if args.dry_run:
        write_dry_run_artifact(
            plan_file,
            f"{feature} 开发计划",
            "## 1. 需求摘要\n- dry-run 验证计划产物路径。\n\n## 2. 测试计划\n- 验证 ship.py 本地编排。"
        )
    else:
        run_wrapper(
            wrapper="planner_cli.py",
            task=f"plan-{task}",
            prompt_file=plan_prompt,
            mode="freeform",
            out=plan_file,
            cwd=root,
            files=context_files,
            timeout=args.timeout,
        )
    print(f"Plan written: {plan_file}")
    if args.plan_only:
        return

    patch_file = work_dir / "coder.patch"
    if not args.skip_coder:
        coder_prompt = work_dir / "coder-prompt.md"
        write_prompt(
            coder_prompt,
            f"""
            Implement the approved plan for this feature:
            {feature}

            Plan file:
            {plan_file}

            Return a unified git diff only.
            Keep edits scoped and update/add tests when appropriate.
            """,
        )
        if args.dry_run:
            patch_file.write_text("", encoding="utf-8")
            print(f"Dry-run coder skipped: {patch_file}")
            return
        diff_before_coder = git_diff(root)
        run_wrapper(
            wrapper="opencode_cli.py",
            task=f"code-{task}",
            prompt_file=coder_prompt,
            mode="patch",
            out=patch_file,
            cwd=root,
            files=[plan_file, *context_files],
            timeout=args.timeout,
        )
        diff_after_coder = git_diff(root)
        if diff_after_coder and diff_after_coder != diff_before_coder:
            print(f"Coder changed working tree directly: {patch_file} applied=True")
            applied = True
        else:
            applied = apply_patch_file(root, patch_file)
            print(f"Coder patch: {patch_file} applied={applied}")
        if not applied:
            return

    if not args.skip_tests:
        test_command = default_test_command(root)
        if test_command:
            print(f"Running tests: {test_command}")
            proc = run_shell(test_command, root, timeout=1200)
            test_log = work_dir / "test.log"
            test_log.write_text((proc.stdout or "") + "\n" + (proc.stderr or ""), encoding="utf-8")
            print(f"Test log: {test_log}")
            if proc.returncode != 0:
                raise RuntimeError(f"Tests failed: {test_command}")

    if not args.skip_review:
        review_prompt = work_dir / "review-prompt.md"
        diff_file = work_dir / "diff.txt"
        diff_file.write_text(git_diff(root), encoding="utf-8")
        review_file = reviews_dir / f"{stamp}-{task}.md"
        write_prompt(
            review_prompt,
            f"""
            Review the implementation for this feature:
            {feature}

            Focus on bugs, regressions, missing tests, security, and deployment risk.
            Output Markdown with findings first.
            """,
        )
        if args.dry_run:
            write_dry_run_artifact(
                review_file,
                f"{feature} 审查记录",
                "## Findings\n- dry-run 未执行真实审查。\n\n## Suggested Tests\n- 使用非 dry-run 模式前确认允许外部 CLI 读取项目上下文。"
            )
        else:
            run_wrapper(
                wrapper="gpt_cli.py",
                task=f"review-{task}",
                prompt_file=review_prompt,
                mode="review",
                out=review_file,
                cwd=root,
                files=[plan_file, diff_file],
                timeout=args.timeout,
            )
        print(f"Review written: {review_file}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
