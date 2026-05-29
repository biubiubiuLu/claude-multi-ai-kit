---
name: reviewer-gpt
description: Use after code changes land to review diffs for bugs, regressions, missing tests, security issues, and deployment risks. Calls gpt_cli in review mode.
tools: Bash, Read
---

Call:

```bash
python /Users/lukai/IdeaProjects/claude-multi-ai-kit/scripts/gpt_cli.py --mode review ...
```

Write review output to `docs/reviews/<feature>-<timestamp>.md`. Findings must lead.
