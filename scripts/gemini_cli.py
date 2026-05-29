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
    parser = common_cli_parser("Gemini/agy CLI wrapper")
    args = parser.parse_args()

    cli_path = os.getenv("GEMINI_CLI_PATH") or shutil.which("agy")
    if not cli_path:
        raise RuntimeError("GEMINI_CLI_PATH is empty and agy was not found")

    prompt = build_model_prompt(
        role="frontend optimization agent using Gemini through agy",
        mode=args.mode,
        prompt_file=args.prompt_file,
        files=args.files,
    )

    command = [
        cli_path,
        "--print",
        "--print-timeout",
        f"{args.timeout}s",
        "--add-dir",
        str(args.cwd),
        "--prompt",
        prompt,
    ]
    response = run_cli(command, prompt="", timeout=args.timeout + 30)
    write_log("gemini", args.task, prompt, response, command)
    write_output(args.out, response)


if __name__ == "__main__":
    main_wrapper(main)
