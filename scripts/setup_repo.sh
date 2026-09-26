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

# Azure OpenAI backend (default). Leave the endpoint blank to skip if you only use the Foundry backend.
read -r -p "Azure OpenAI endpoint (https://<resource>.openai.azure.com/, blank to skip): " AOAI_ENDPOINT
if [ -n "$AOAI_ENDPOINT" ]; then
  read -r -p "Azure OpenAI deployment name (your chat-model deployment): " AOAI_DEPLOYMENT
  gh variable set AZURE_OPENAI_ENDPOINT --body "$AOAI_ENDPOINT"
  gh variable set AZURE_OPENAI_DEPLOYMENT --body "$AOAI_DEPLOYMENT"
  echo "Paste your Azure OpenAI API key when prompted (it is stored as a GitHub Actions secret):"
  gh secret set AZURE_OPENAI_API_KEY
fi
# Foundry backend: see README ("Foundry backend") for the variables and OIDC secrets to add later.

gh issue create --title "Percentage discount returns a negative total" \
  --label bug --body-file demo/issue_body.md

echo
echo "Done. To start the agent, add the 'agent-fix' label to the new issue."
