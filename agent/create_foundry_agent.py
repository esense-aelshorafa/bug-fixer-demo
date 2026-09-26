"""Create (or update) the Bug Fixer prompt agent in Microsoft Foundry.

Run it once, and again whenever you change the instructions, the tools or the model.
Every run publishes a new agent VERSION, so you can compare versions in the Foundry portal.

    python agent/create_foundry_agent.py                          # all four tools
    python agent/create_foundry_agent.py --tools list_files       # add tools one at a time:
    python agent/create_foundry_agent.py --tools list_files,read_file
    python agent/create_foundry_agent.py --tools list_files,read_file,write_file,run_tests

Environment:
    FOUNDRY_PROJECT_ENDPOINT         from the Foundry portal: project Overview
    FOUNDRY_MODEL_DEPLOYMENT_NAME    from the portal: Build > Deployments
    FOUNDRY_AGENT_NAME               the agent's name (default "bug-fixer"); use the name of the agent
                                     you created in the portal to add a new version to it
Sign in first with `az login` (your identity needs the "Foundry User" role on the project).
"""
import argparse
import os

import bug_fixer as bf
from azure.ai.projects.models import FunctionTool, PromptAgentDefinition


def build_definition(model_deployment: str, tool_names: list[str] | None = None) -> PromptAgentDefinition:
    # Same tools as the Azure OpenAI backend. Foundry only stores the definitions;
    # the functions themselves are executed by bug_fixer.py at run time.
    available = {t["function"]["name"]: t["function"] for t in bf.TOOLS}
    names = tool_names or list(available)
    unknown = [n for n in names if n not in available]
    if unknown:
        raise SystemExit(f"Unknown tool(s): {', '.join(unknown)}. Available: {', '.join(available)}")
    tools = [
        FunctionTool(
            name=n,
            description=available[n]["description"],
            parameters=available[n]["parameters"],
            strict=False,
        )
        for n in names
    ]
    return PromptAgentDefinition(model=model_deployment, instructions=bf.SYSTEM_PROMPT, tools=tools)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tools", help="comma-separated tool names to attach (default: all four)")
    args = parser.parse_args()
    names = [n.strip() for n in args.tools.split(",") if n.strip()] if args.tools else None

    bf.require_env("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL_DEPLOYMENT_NAME")
    definition = build_definition(os.environ["FOUNDRY_MODEL_DEPLOYMENT_NAME"], names)
    agent = bf.foundry_project().agents.create_version(agent_name=bf.FOUNDRY_AGENT_NAME, definition=definition)
    print(f"Created agent '{agent.name}', version {agent.version}, tools: {[t.name for t in definition.tools]}")
    print("Open it in the Foundry portal under Build > Agents.")


if __name__ == "__main__":
    main()
