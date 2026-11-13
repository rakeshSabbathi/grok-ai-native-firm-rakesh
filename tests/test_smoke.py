"""Offline checks: every agent parses, every action it names exists, every workflow points to real agents."""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import actions  # noqa: E402


def agents():
    out = {}
    for f in (ROOT / "agents").rglob("*.md"):
        _, fm, body = f.read_text(encoding="utf-8").split("---", 2)
        meta = yaml.safe_load(fm)
        assert body.strip(), f"{f} has no prompt"
        out[meta["name"]] = meta
    return out


def test_agents_use_real_actions():
    for name, meta in agents().items():
        for a in meta["actions"]:
            assert a in actions.REGISTRY, f"{name} uses missing action {a}"


def test_workflows_use_real_agents():
    ag = agents()
    wf = yaml.safe_load((ROOT / "workflows" / "workflows.yaml").read_text())
    for name, w in wf.items():
        for s in w["steps"]:
            assert s["agent"] in ag, f"{name} uses missing agent {s['agent']}"


def test_brain_blocks_path_escape():
    assert "ERROR" in actions.call("brain_write", {"path": "../evil.md", "content": "x"})


def test_draft_never_sends(tmp_path, monkeypatch):
    monkeypatch.setattr(actions, "OUTBOX", tmp_path)
    r = actions.call("draft_message", {"channel": "email", "to": "a@b.com", "body": "hi"})
    assert "needs human approval" in r and list(tmp_path.iterdir())
