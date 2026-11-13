#!/usr/bin/env python3
"""CLI.
  python run.py list
  python run.py agent <name> "task"
  python run.py workflow <name> "input"
"""
import argparse
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def workflows():
    return yaml.safe_load((ROOT / "workflows" / "workflows.yaml").read_text())


def run_workflow(name, user_input):
    from core.agent import run_agent

    wf = workflows()[name]
    prev = ""
    for i, step in enumerate(wf["steps"], 1):
        task = step["task"].replace("{input}", user_input).replace("{previous}", prev)
        print(f"\n=== [{i}/{len(wf['steps'])}] {step['agent']} ===")
        prev = run_agent(step["agent"], task)
        print(prev)
    return prev


def main():
    load_env()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    a = sub.add_parser("agent"); a.add_argument("name"); a.add_argument("task")
    w = sub.add_parser("workflow"); w.add_argument("name"); w.add_argument("input")
    args = ap.parse_args()

    if args.cmd == "list":
        print("AGENTS")
        for f in sorted((ROOT / "agents").rglob("*.md")):
            print(f"  {f.parent.name}/{f.stem}")
        print("\nWORKFLOWS")
        for k, v in workflows().items():
            print(f"  {k}: {v['description']}")
    elif args.cmd == "agent":
        from core.agent import run_agent
        print(run_agent(args.name, args.task))
    else:
        run_workflow(args.name, args.input)


if __name__ == "__main__":
    main()
