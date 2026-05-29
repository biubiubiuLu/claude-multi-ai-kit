#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess

from ai_common import (
    build_model_prompt,
    common_cli_parser,
    main_wrapper,
    run_cli,
    write_log,
    write_output,
)


def main() -> None:
    parser = common_cli_parser("GPT/Codex CLI wrapper")
    args = parser.parse_args()

    cli_path = os.getenv("GPT_CLI_PATH") or shutil.which("codex")
    if not cli_path:
        raise RuntimeError("GPT_CLI_PATH is empty and codex was not found")

    model = args.model or os.getenv("GPT_MODEL", "")
    prompt = build_model_prompt(
        role="planner/reviewer GPT agent",
        mode=args.mode,
        prompt_file=args.prompt_file,
        files=args.files,
    )

    command = [
        cli_path,
        "exec",
        "-C",
        str(args.cwd),
        "--ephemeral",
        "--skip-git-repo-check",
        "--sandbox",
        "workspace-write",
        "-",
    ]
    if model:
        command[command.index("--sandbox"):command.index("--sandbox")] = ["-m", model]
    response = run_cli(command, prompt=prompt, timeout=args.timeout)
    write_log("gpt", args.task, prompt, response, command)
    write_output(args.out, response)


if __name__ == "__main__":
    main_wrapper(main)
