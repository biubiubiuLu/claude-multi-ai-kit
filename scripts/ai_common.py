#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shlex
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Iterable

KIT_DIR = Path(__file__).resolve().parents[1]
HOME = Path.home()
DEFAULT_ENV_FILES = [
    HOME / ".claude" / ".env",
    KIT_DIR / ".env",
]


class AiKitError(RuntimeError):
    pass


def load_environment() -> None:
    for env_file in DEFAULT_ENV_FILES:
        if env_file.exists():
            load_env_file(env_file)


def load_env_file(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def slugify(value: str, fallback: str = "task") -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-").lower()
    return value[:80] or fallback


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def logs_dir() -> Path:
    path = HOME / ".claude" / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_log(tool: str, task: str, prompt: str, response: str, command: list[str]) -> Path:
    path = logs_dir() / f"{tool}-{slugify(task)}-{timestamp()}.log"
    debug = os.getenv("AI_DEBUG", "0") == "1"
    prompt_text = prompt if debug else f"<redacted prompt, {len(prompt)} chars; set AI_DEBUG=1 to log full prompt>"
    path.write_text(
        "\n".join(
            [
                f"tool={tool}",
                f"task={task}",
                f"command={shlex.join(command)}",
                "",
                "## Prompt",
                prompt_text,
                "",
                "## Response Preview",
                response[:4000],
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def build_model_prompt(
    role: str,
    mode: str,
    prompt_file: Path,
    files: Iterable[Path],
) -> str:
    prompt = prompt_file.read_text(encoding="utf-8")
    file_sections = []
    for file_path in files:
        if not file_path.exists() or not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8", errors="replace")
        file_sections.append(
            f"### File: {file_path}\n```text\n{text[:30000]}\n```"
        )

    output_contract = {
        "patch": "Return only a unified git diff. Do not include Markdown fences or explanation.",
        "review": "Return Markdown with sections: ## Findings, ## Suggested Tests, ## Residual Risk.",
        "freeform": "Return plain useful text for the requested task.",
    }[mode]

    return textwrap.dedent(
        f"""
        You are the {role} in a multi-agent software workflow.

        Output contract:
        {output_contract}

        User/task prompt:
        {prompt}

        Context files:
        {chr(10).join(file_sections) if file_sections else "(no files provided)"}
        """
    ).strip()


def run_cli(command: list[str], prompt: str, timeout: int) -> str:
    proc = subprocess.run(
        command,
        input=prompt,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise AiKitError(
            f"Command failed ({proc.returncode}): {shlex.join(command)}\n"
            f"STDERR:\n{proc.stderr[-4000:]}"
        )
    return proc.stdout.strip()


def common_cli_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--task", required=True)
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--files", nargs="*", default=[], type=Path)
    parser.add_argument("--mode", choices=["patch", "review", "freeform"], required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--model")
    parser.add_argument("--timeout", type=int, default=int(os.getenv("AI_TIMEOUT", "120")))
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    return parser


def write_output(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / "pom.xml").exists() or (candidate / "package.json").exists():
            return candidate
    return current


def load_project_config(root: Path) -> dict:
    config_file = root / "CLAUDE.md"
    if not config_file.exists():
        return {}
    raw = config_file.read_text(encoding="utf-8")
    lines = [line for line in raw.splitlines() if not line.strip().startswith("#")]
    return parse_simple_yaml("\n".join(lines))


def parse_simple_yaml(raw: str) -> dict:
    config: dict[str, object] = {}
    current_list_key: str | None = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - ") and current_list_key:
            config.setdefault(current_list_key, [])
            value = line[4:].strip()
            if isinstance(config[current_list_key], list):
                config[current_list_key].append(value)
            continue
        current_list_key = None
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            config[key] = []
            current_list_key = key
        elif value.lower() in {"true", "false"}:
            config[key] = value.lower() == "true"
        else:
            config[key] = value
    return config


def default_test_command(root: Path) -> str:
    config = load_project_config(root)
    if config.get("test_command"):
        return str(config["test_command"])
    if (root / "pom.xml").exists():
        return "mvn test"
    if (root / "package.json").exists():
        return "npm test"
    if (root / "pyproject.toml").exists():
        return "pytest"
    return ""


def run_shell(command: str, cwd: Path, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        shell=True,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=timeout,
        executable="/bin/zsh" if Path("/bin/zsh").exists() else None,
    )


def main_wrapper(fn) -> None:
    try:
        load_environment()
        fn()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
