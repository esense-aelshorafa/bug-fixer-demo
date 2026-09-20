# Bug Fixer Demo

A tiny Python project plus an AI agent that picks up a GitHub issue, reproduces the bug,
fixes it, verifies the fix, and opens a **draft pull request** for a human to review.

```
Issue labeled "agent-fix"
        │
        ▼
GitHub Actions ──► Bug Fixer agent (Claude + tools)
                        │   list_files / read_file / write_file / run_tests
                        │   loop: reproduce → fix → re-run tests
                        ▼
              Pipeline re-verifies (tests + protected paths)
                        │
                        ▼
              Draft PR "Fixes #N"  +  comment on the issue
```

## Quick start

1. Install the [GitHub CLI](https://cli.github.com) and run `gh auth login`.
2. From this folder run:
   ```bash
   bash scripts/setup_repo.sh bug-fixer-demo
   ```
   (On Windows, use Git Bash or WSL.)
   It creates the repo, pushes the code, creates the `agent-fix` label, allows Actions to open
   PRs, asks for your `ANTHROPIC_API_KEY` (stored as an Actions secret), and files the demo issue.
3. Open the new issue and add the **`agent-fix`** label. Watch the *Actions* tab; a draft PR appears.

You can also run it by hand: *Actions → Bug Fixer Agent → Run workflow → issue number*.

## Run locally (no push, no PR)

```bash
pip install -r requirements.txt -r agent/requirements.txt
export ANTHROPIC_API_KEY=...            # your key
export GITHUB_TOKEN=$(gh auth token)
export GITHUB_REPOSITORY=<owner>/<repo>
python agent/bug_fixer.py --issue 1 --dry-run
```

## Guardrails (good talking points)

| Guardrail | Where |
|---|---|
| A maintainer must add the label; issue authors alone cannot trigger it | workflow trigger |
| Draft PR only; a human reviews and merges | `open_pull_request` |
| Agent cannot edit `.github/` or `agent/`, or read outside the repo | tool layer |
| Pipeline re-runs the tests itself instead of trusting the agent | `main()` |
| Step budget and job timeout | `AGENT_MAX_STEPS`, `timeout-minutes` |
| Issue text is untrusted input: fetched via API, never interpolated into a shell | workflow + system prompt |
| On failure it comments on the issue instead of guessing | `give_up` |

## Known limitations

- PRs created with the default `GITHUB_TOKEN` do not trigger the `CI` workflow. Use a GitHub App
  token or a PAT if you want CI to run on the agent's PR.
- The agent is only as good as the issue. Structured reports (see the issue template) work best.
- Set `ANTHROPIC_MODEL` to change the model.
