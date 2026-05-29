#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil

from ai_common import (
    build_model_prompt,
    common_cli_parser,
    main_wrapper,
    run_cli,
    write_log,
    write_output,
)


def main() -> None:
    parser = common_cli_parser("opencode CLI wrapper, usually backed by DeepSeek")
    args = parser.parse_args()

    cli_path = os.getenv("OPENCODE_CLI_PATH") or os.getenv("DEEPSEEK_CLI_PATH") or shutil.which("opencode")
    if not cli_path:
        raise RuntimeError("OPENCODE_CLI_PATH is empty and opencode was not found")

    model = args.model or os.getenv("OPENCODE_MODEL") or os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-chat")
    prompt = build_model_prompt(
        role="coder agent using opencode with DeepSeek",
        mode=args.mode,
        prompt_file=args.prompt_file,
        files=args.files,
    )

    command = [
        cli_path,
        "run",
        "--dir",
        str(args.cwd),
        "-m",
        model,
        prompt,
    ]
    response = run_cli(command, prompt="", timeout=args.timeout)
    write_log("opencode", args.task, prompt, response, command)
    write_output(args.out, response)


if __name__ == "__main__":
    main_wrapper(main)
