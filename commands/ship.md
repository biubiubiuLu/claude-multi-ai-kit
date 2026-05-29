---
description: Run the multi-AI shipping workflow for a feature request.
argument-hint: <feature request>
---

Run:

```bash
python /Users/lukai/IdeaProjects/claude-multi-ai-kit/scripts/ship.py "$ARGUMENTS"
```

The workflow writes a plan under `docs/plans/`, asks the configured coder provider for a patch, runs project tests, and writes a review under `docs/reviews/`.
