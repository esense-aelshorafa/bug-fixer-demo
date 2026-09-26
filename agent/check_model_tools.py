"""Check whether a Foundry model deployment can do tool (function) calling.

It sends one request with a dummy `get_weather` function and reports whether the model answers
with a tool call. Two routes are probed, because they answer different questions:

    responses   Responses API on your PROJECT endpoint (the route Foundry agents use)
    chat        Chat Completions on your resource's /openai/v1 endpoint (works without an agent)

    python agent/check_model_tools.py                    # both probes
    python agent/check_model_tools.py --probe chat

Environment:
    FOUNDRY_MODEL_DEPLOYMENT_NAME   your deployment name (portal: Build > Deployments)
    FOUNDRY_PROJECT_ENDPOINT        project endpoint (used by the responses probe, and to find the resource)
    AZURE_OPENAI_ENDPOINT           optional override for the chat probe: https://<resource>.openai.azure.com/
    AZURE_OPENAI_API_KEY            optional key; without it, Microsoft Entra ID is used (`az login`)

A pass proves the MODEL can call tools. It does not prove that a Foundry prompt agent accepts the
model; check the agent-supported filter in the Foundry model catalog for that.
"""
import argparse
import json
import os
import sys
from urllib.parse import urlparse

import bug_fixer as bf

PROMPT = "What is the weather in Cairo right now? Use the get_weather tool."
PARAMS = {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}


def probe_responses(deployment: str) -> str:
    openai = bf.foundry_project().get_openai_client()
    tool = {"type": "function", "name": "get_weather", "description": "Get the current weather for a city",
            "parameters": PARAMS}
    response = openai.responses.create(model=deployment, input=PROMPT, tools=[tool])
    calls = [item for item in response.output if item.type == "function_call"]
    if not calls:
        raise AssertionError(f"no function_call in the output; the model said: {(response.output_text or '')[:120]!r}")
    return f"{calls[0].name}({json.loads(calls[0].arguments)})"


def resource_endpoint() -> str:
    override = os.getenv("AZURE_OPENAI_ENDPOINT")
    if override:
        return override.rstrip("/")
    host = urlparse(os.environ["FOUNDRY_PROJECT_ENDPOINT"]).hostname or ""
    return f"https://{host.split('.')[0]}.openai.azure.com"


def probe_chat(deployment: str) -> str:
    from openai import OpenAI

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not api_key:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        api_key = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    client = OpenAI(base_url=f"{resource_endpoint()}/openai/v1/", api_key=api_key)
    tool = {"type": "function", "function": {"name": "get_weather",
            "description": "Get the current weather for a city", "parameters": PARAMS}}
    response = client.chat.completions.create(
        model=deployment, messages=[{"role": "user", "content": PROMPT}], tools=[tool], tool_choice="auto",
    )
    message = response.choices[0].message
    if not message.tool_calls:
        raise AssertionError(f"no tool_calls in the message; the model said: {(message.content or '')[:120]!r}")
    call = message.tool_calls[0].function
    return f"{call.name}({json.loads(call.arguments)})"


PROBES = {"responses": probe_responses, "chat": probe_chat}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", choices=["both", *PROBES], default="both")
    args = parser.parse_args()
    bf.require_env("FOUNDRY_MODEL_DEPLOYMENT_NAME", "FOUNDRY_PROJECT_ENDPOINT")
    deployment = os.environ["FOUNDRY_MODEL_DEPLOYMENT_NAME"]

    failed = False
    for name in (PROBES if args.probe == "both" else [args.probe]):
        try:
            print(f"PASS  {name:<9} model called the tool: {PROBES[name](deployment)}")
        except Exception as exc:
            failed = True
            print(f"FAIL  {name:<9} {type(exc).__name__}: {str(exc)[:220]}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
