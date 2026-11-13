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

# ---- Grok Bots: 5 bots (Chief of Staff + 4 workers) from the same agents ----
BOTS_OUT = ROOT / "grok-bots"
BOTS_OUT.mkdir(exist_ok=True)
GROUPS = [
    ("1-acquisition", "Acquisition", ["1-acquisition", "2-nurture"]),
    ("2-convert-onboard", "Convert and Onboard", ["3-convert", "4-onboard"]),
    ("3-fulfill", "Fulfill", ["5-fulfill"]),
    ("4-second-brain", "Second Brain", ["6-second-brain"]),
]
RULES = """Rules:
- Never invent data (names, emails, numbers, quotes). If you don't know, say so and give search criteria instead.
- Never send anything without my explicit approval. Write every outbound message as a block starting with "DRAFT (channel, to)".
- When something is worth keeping, output a block starting with "SAVE TO BRAIN: <folder/file.md>". Link related notes with [[wiki-links]].
- Be concise and specific. Mark anything unverified.

Company profile: (paste your company.yaml here)
"""
bot_names = []
for fname, title, layers_ in GROUPS:
    names, body_all = [], ""
    for ld in layers_:
        part = (OUT / f"{ld}.md").read_text(encoding="utf-8")
        agents_part = part.split("Agents:\n", 1)[1]
        body_all += agents_part
        names += [l[4:].strip() for l in agents_part.splitlines() if l.startswith("### ")]
    bot_names.append((title, names))
    text = (f"You are the {title} bot of an AI-native firm. Your agents: {', '.join(names)}.\n"
            "I start a message with \"agent: <name>\" to pick one. If I don't, pick the best fit and say which.\n\n"
            + RULES + "\nAgents:\n" + body_all)
    (BOTS_OUT / f"{fname}.md").write_text(text, encoding="utf-8")
    print("bot", fname, len(text), "chars")

team = "; ".join(f"{t} ({', '.join(nm)})" for t, nm in bot_names)
cos = ("You are the Chief of Staff of an AI-native firm. I talk to you first, every time. You do not do the work yourself. You decide who does it.\n\n"
       f"My team is 4 other bots: {team}. When they exist as bots, hand work to them directly. Otherwise tell me what to send them.\n\n"
       "When I give you a goal:\n"
       "1. Reply with the plan in order: Bot > agent, one line each on why.\n"
       "2. For the first step, write the exact message to send, starting with \"agent: <name>\", including every detail that agent needs.\n"
       "3. If something essential is missing, ask at most 2 questions before the plan.\n"
       "4. After I paste back a result, tell me the next step.\n\n"
       "When I say \"weekly plan\", ask for my pipeline numbers and give me the 3 priorities for the week. "
       "When I say \"what next\", say the single next action.\n\n" + RULES)
(BOTS_OUT / "0-chief-of-staff.md").write_text(cos, encoding="utf-8")
print("bot 0-chief-of-staff", len(cos), "chars")
