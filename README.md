# Bug Fixer Demo (Azure OpenAI / Microsoft Foundry)

A tiny Python project plus an AI agent that picks up a GitHub issue, reproduces the bug,
fixes it, verifies the fix, and opens a **draft pull request** for a human to review.
The agent runs on one of two backends, with the same tools and the same verification:

- **`azure-openai`** (default): the `AzureOpenAI` client from the `openai` SDK with function calling.
- **`foundry`**: a prompt agent hosted in Microsoft Foundry Agent Service. Function tools still run
  on your machine or runner; Foundry stores the agent definition and runs the model.

```
Issue labeled "agent-fix"
        │
        ▼
GitHub Actions ──► Bug Fixer agent (Azure OpenAI deployment  OR  Foundry agent, + tools)
                        │   list_files / read_file / write_file / run_tests
                        │   loop: reproduce → fix → re-run tests
                        ▼
              Pipeline re-verifies (tests + protected paths)
                        │
                        ▼
              Draft PR "Fixes #N"  +  comment on the issue
```

## Prerequisites

- An Azure OpenAI resource with a **chat model deployment that supports function calling**.
  You need its endpoint (`https://<resource>.openai.azure.com/`) and the **deployment name**
  (Azure takes the deployment name in the `model` parameter, not the base model name).
- The [GitHub CLI](https://cli.github.com), logged in with `gh auth login`.

## Quick start

1. From this folder run:
   ```bash
   bash scripts/setup_repo.sh bug-fixer-demo
   ```
   (On Windows, use Git Bash or WSL.) It creates the repo, pushes the code, creates the
   `agent-fix` label, allows Actions to open PRs, asks for your endpoint and deployment name
   (stored as repository variables) and your API key (stored as an Actions secret), and files
   the demo issue.
2. Open the new issue and add the **`agent-fix`** label. Watch the *Actions* tab; a draft PR appears.

You can also run it by hand: *Actions → Bug Fixer Agent → Run workflow → issue number*.

## Run locally (no push, no PR)

```bash
pip install -r requirements.txt -r agent/requirements.txt
export AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
export AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
export GITHUB_TOKEN=$(gh auth token)
export GITHUB_REPOSITORY=<owner>/<repo>

# Option A: API key
export AZURE_OPENAI_API_KEY=<key>
# Option B: keyless (Microsoft Entra ID). Run `az login` and leave AZURE_OPENAI_API_KEY unset.
#           Your identity needs the "Cognitive Services OpenAI User" role on the resource.

python agent/bug_fixer.py --issue 1 --dry-run
```

## Foundry backend

1. In the Foundry portal create (or pick) a project and deploy a chat model that supports function
   calling. Copy the **project endpoint** (project Overview) and the **deployment name**
   (Build > Deployments).
2. Give yourself the **Foundry User** role on the project (older docs call it *Azure AI User*).
   To check that your model deployment can do tool calling at all (no agent needed), run
   `python agent/check_model_tools.py` (it needs `FOUNDRY_MODEL_DEPLOYMENT_NAME` and
   `FOUNDRY_PROJECT_ENDPOINT`). A pass proves the model calls tools; whether a prompt agent accepts the
   model is a separate question (see the agent-supported filter in the Foundry model catalog).
3. Create the agent once (run `az login` first):
   ```bash
   export FOUNDRY_PROJECT_ENDPOINT=<project endpoint>
   export FOUNDRY_MODEL_DEPLOYMENT_NAME=<deployment name>
   python agent/create_foundry_agent.py        # prints the agent name and version
   ```
   To add the tools one at a time (each run publishes a new version), use `--tools`, e.g.
   `--tools list_files`, then `--tools list_files,read_file`, and so on. To add a version to an agent
   you created in the portal, set `FOUNDRY_AGENT_NAME` to that agent's exact name.
4. Try it locally (no push, no PR):
   ```bash
   export GITHUB_TOKEN=$(gh auth token) GITHUB_REPOSITORY=<owner>/<repo>
   python agent/bug_fixer.py --issue 1 --backend foundry --dry-run
   ```
5. For GitHub Actions, sign in with OIDC instead of a key: create an Entra app registration with a
   federated credential for this repo, give it the Foundry User role on the project, then add
   secrets `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` and variables
   `AGENT_BACKEND=foundry`, `FOUNDRY_PROJECT_ENDPOINT` (optionally `FOUNDRY_AGENT_NAME`).

Re-run `create_foundry_agent.py` whenever you change the instructions or tools; each run publishes a
new agent version. The function tools are defined in Foundry but executed by `bug_fixer.py`.
Function-tool runs expire 10 minutes after creation, so keep tool calls quick.

## Configuration

| Variable | Where | Purpose |
|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | repo variable | Your resource endpoint |
| `AZURE_OPENAI_DEPLOYMENT` | repo variable | Deployment name passed as `model` |
| `AZURE_OPENAI_API_KEY` | repo secret | Key auth (omit locally to use `az login` instead) |
| `AZURE_OPENAI_API_VERSION` | optional | Defaults to `2024-10-21` |
| `AGENT_MAX_STEPS` | optional | Step budget, default 20 |
| `AGENT_BACKEND` | repo variable | `azure-openai` (default) or `foundry` |
| `FOUNDRY_PROJECT_ENDPOINT` | repo variable | Foundry backend: project endpoint |
| `FOUNDRY_AGENT_NAME` | optional | Foundry agent name, default `bug-fixer` |
| `AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_SUBSCRIPTION_ID` | repo secrets | Foundry backend in Actions (OIDC login) |

With the `azure-openai` backend the Actions workflow uses key auth. The `foundry` backend uses
keyless Entra ID auth (`azure/login` with OIDC).

## Guardrails (good talking points)

| Guardrail | Where |
|---|---|
| A maintainer must add the label; issue authors alone cannot trigger it | workflow trigger |
| Draft PR only; a human reviews and merges | `open_pull_request` |
| Agent cannot edit `.github/` or `agent/`, or read outside the repo | tool layer |
| Pipeline re-runs the tests itself instead of trusting the agent | `main()` |
| Step budget and job timeout | `AGENT_MAX_STEPS`, `timeout-minutes` |
| Issue text is untrusted input: fetched via API, never interpolated into a shell | workflow + system prompt |
| On failure it comments on the issue instead of guessing; error details stay in the workflow log | `give_up` |
| Azure content filter blocks are surfaced as a clean failure | `run_agent` |

## Known limitations

- PRs created with the default `GITHUB_TOKEN` do not trigger the `CI` workflow. Use a GitHub App
  token or a PAT if you want CI to run on the agent's PR.
- The agent is only as good as the issue. Structured reports (see the issue template) work best.
- The deployment must support tool/function calling; the agent passes no `temperature` or
  `max_tokens`, so it also works with models that reject those parameters.
