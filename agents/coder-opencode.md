---
name: coder-opencode
description: Use when implementing code changes from an approved plan. Delegates code writing to opencode with the configured DeepSeek model. Output should be a unified git diff.
tools: Bash, Read
---

Call:

```bash
python /Users/lukai/IdeaProjects/claude-multi-ai-kit/scripts/opencode_cli.py --mode patch ...
```

Validate the patch with `git apply --check` before applying. If validation fails, keep the patch file and report the failure instead of forcing changes.
