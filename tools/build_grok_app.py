"""Builds paste-ready instructions for the Grok app (Projects / Custom Agents) from agents/*.md.
Run: python tools/build_grok_app.py  ->  writes grok-app/*.md"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "grok-app"
OUT.mkdir(exist_ok=True)

PREAMBLE = """You are the {layer} team of an AI-native firm. You contain these agents: {names}.
I will start a message with "agent: <name>" to pick one. If I don't, pick the best fit and say which.

Rules:
- Never invent data (names, emails, numbers, quotes). If you don't know, say so.
- You cannot send anything. Write every outbound message as a block starting with "DRAFT (channel, to)".
- You cannot save files. When something is worth keeping, output it as a block starting with "SAVE TO BRAIN: <folder/filename.md>" so I can save it myself. Link related notes with [[wiki-links]].
- Be concise and specific.

Company profile (I will keep this updated in the project files): see company.yaml.

Agents:
"""

n = 0
for layer_dir in sorted((ROOT / "agents").iterdir()):
    if not layer_dir.is_dir():
        continue
    specs = []
    for f in sorted(layer_dir.glob("*.md")):
        _, fm, body = f.read_text(encoding="utf-8").split("---", 2)
        meta = yaml.safe_load(fm)
        specs.append((meta["name"], body.strip()))
    layer = layer_dir.name.split("-", 1)[1].replace("-", " ").title()
    text = PREAMBLE.format(layer=layer, names=", ".join(s[0] for s in specs))
    for name, body in specs:
        # the app has no tools, so strip tool-specific wording
        body = body.replace("Save every message with draft_message.", "Write every message as a DRAFT block.")
        body = body.replace("Save leads scoring 60+ with lead_add.", "List leads scoring 60+ as a table I can copy.")
        body = body.replace("Use apollo_people_search when available; never make up contacts.",
                            "Never make up contacts; if I haven't given you real data, give search criteria instead.")
        body = body.replace("Update the CRM from call notes:", "Turn call notes into CRM updates as a table I can paste into my CRM:")
        body = body.replace("If HubSpot is not configured, log with lead_add and say so.", "Flag any field you could not fill.")
        text += f"\n### {name}\n{body}\n"
    (OUT / f"{layer_dir.name}.md").write_text(text, encoding="utf-8")
    print(f"{layer_dir.name}.md  {len(text)} chars")
    n += 1
print(n, "files")
