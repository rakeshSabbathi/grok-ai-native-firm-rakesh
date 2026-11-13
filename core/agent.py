"""Agent runner: loads an agent spec (agents/**/<name>.md), runs it on Grok with
tool-calling over the actions it is allowed to use, and files the result in the brain."""
import datetime as dt
import json
from pathlib import Path

import yaml

from . import actions
from .grok import client, model

ROOT = Path(__file__).resolve().parent.parent

GLOBAL_RULES = """Global rules for every agent:
- Never invent data (names, emails, numbers, quotes). If you don't know, say so or use a tool.
- You never send anything. Outbound messages go through draft_message for human approval.
- Be concise and specific. Output only what the next step or the human needs.
- When you create something worth keeping, file it with brain_write and link related notes with [[wiki-links]].
"""


def load_agent(name: str) -> dict:
    matches = list((ROOT / "agents").rglob(f"{name}.md"))
    if not matches:
        raise SystemExit(f"Unknown agent: {name}")
    raw = matches[0].read_text(encoding="utf-8")
    _, fm, body = raw.split("---", 2)
    meta = yaml.safe_load(fm)
    meta["prompt"] = body.strip()
    return meta


def company_context() -> str:
    p = ROOT / "config" / "company.yaml"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def run_agent(name: str, task: str, max_steps: int = 8) -> str:
    spec = load_agent(name)
    allowed = spec.get("actions", [])
    system = f"{GLOBAL_RULES}\nCompany profile:\n{company_context()}\n\nYou are the {spec['name']} agent.\n{spec['prompt']}"
    messages = [{"role": "system", "content": system}, {"role": "user", "content": task}]
    c = client()
    final = ""
    for _ in range(max_steps):
        kwargs = {"model": model(), "messages": messages}
        if allowed:
            kwargs["tools"] = actions.schemas(allowed)
        msg = c.chat.completions.create(**kwargs).choices[0].message
        if not msg.tool_calls:
            final = msg.content or ""
            break
        messages.append(msg)
        for tc in msg.tool_calls:
            result = actions.call(tc.function.name, json.loads(tc.function.arguments or "{}")) \
                if tc.function.name in allowed else f"ERROR: {tc.function.name} not allowed for this agent"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    actions.brain_write(f"runs/{stamp}-{name}.md", f"# {name} run\n\nTask: {task}\n\n{final}\n")
    return final
