#!/usr/bin/env bash
# One-shot setup: creates the GitHub repo, pushes the code, configures the agent, files the demo bug.
# Requires the GitHub CLI (https://cli.github.com) logged in via `gh auth login`.
set -euo pipefail
cd "$(dirname "$0")/.."

REPO_NAME="${1:-bug-fixer-demo}"

command -v gh >/dev/null || { echo "Install the GitHub CLI first: https://cli.github.com"; exit 1; }
gh auth status >/dev/null

[ -d .git ] || git init -b main
git add -A
git commit -m "Initial commit: shop cart demo + Bug Fixer agent" || true
gh repo create "$REPO_NAME" --public --source=. --remote=origin --push

gh label create agent-fix --color 5319e7 \
  --description "Let the Bug Fixer agent handle this issue" --force

# Let Actions open pull requests (you can also set this in Settings > Actions > General).
gh api -X PUT "repos/{owner}/{repo}/actions/permissions/workflow" \
  -f default_workflow_permissions=write -F can_approve_pull_request_reviews=true \
  || echo "Could not set workflow permissions automatically; enable them in Settings > Actions > General."

echo "Paste your Anthropic API key when prompted (it is stored as a GitHub Actions secret):"
gh secret set ANTHROPIC_API_KEY

gh issue create --title "Percentage discount returns a negative total" \
  --label bug --body-file demo/issue_body.md

echo
echo "Done. To start the agent, add the 'agent-fix' label to the new issue."
