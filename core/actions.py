"""Actions = the tools agents can call. Everything that touches the outside world
either reads data or writes a DRAFT to outbox/. Nothing is sent automatically."""
import datetime as dt
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAIN = ROOT / "brain"
DATA = ROOT / "data"
OUTBOX = ROOT / "outbox"

REGISTRY: dict = {}


def action(name, description, params, required=()):
    def deco(fn):
        REGISTRY[name] = {
            "fn": fn,
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": {"type": "object", "properties": params, "required": list(required)},
                },
            },
        }
        return fn

    return deco


def schemas(names):
    return [REGISTRY[n]["schema"] for n in names]


def call(name, args):
    if name not in REGISTRY:
        return f"ERROR: unknown action {name}"
    try:
        return REGISTRY[name]["fn"](**args)
    except Exception as e:  # return errors to the model so it can recover
        return f"ERROR: {type(e).__name__}: {e}"


def _safe_brain_path(rel: str) -> Path:
    p = (BRAIN / rel).resolve()
    if BRAIN.resolve() not in p.parents and p != BRAIN.resolve():
        raise ValueError("path escapes brain/")
    return p


# ---------- Layer 6: second brain ----------
@action("brain_write", "File a note in the second brain (markdown). Use [[wiki-links]] to link to other notes.",
        {"path": {"type": "string", "description": "e.g. leads/acme.md"}, "content": {"type": "string"}},
        ["path", "content"])
def brain_write(path, content):
    p = _safe_brain_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"saved brain/{path}"


@action("brain_read", "Read a note from the second brain.", {"path": {"type": "string"}}, ["path"])
def brain_read(path):
    p = _safe_brain_path(path)
    return p.read_text(encoding="utf-8") if p.exists() else "not found"


@action("brain_search", "Keyword search across the second brain. Returns matching files with snippets.",
        {"query": {"type": "string"}}, ["query"])
def brain_search(query):
    terms = [t.lower() for t in query.split() if t]
    hits = []
    for f in BRAIN.rglob("*.md"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        low = text.lower()
        if terms and all(t in low for t in terms):
            i = low.find(terms[0])
            hits.append({"file": str(f.relative_to(BRAIN)), "snippet": text[max(0, i - 80): i + 200]})
    return json.dumps(hits[:10], indent=2) if hits else "no matches"


@action("brain_backlinks", "List notes that link to a given note via [[wiki-links]].",
        {"note": {"type": "string", "description": "note name without .md"}}, ["note"])
def brain_backlinks(note):
    pat = re.compile(r"\[\[" + re.escape(note) + r"(\|[^\]]*)?\]\]", re.I)
    out = [str(f.relative_to(BRAIN)) for f in BRAIN.rglob("*.md") if pat.search(f.read_text(encoding="utf-8", errors="ignore"))]
    return json.dumps(out)


# ---------- Leads ----------
@action("lead_add", "Save a qualified lead to data/leads.jsonl.",
        {"name": {"type": "string"}, "company": {"type": "string"}, "title": {"type": "string"},
         "email": {"type": "string"}, "linkedin": {"type": "string"},
         "fit_score": {"type": "integer", "description": "0-100"}, "reason": {"type": "string"}},
        ["name", "company", "fit_score", "reason"])
def lead_add(name, company, fit_score, reason, title="", email="", linkedin=""):
    DATA.mkdir(exist_ok=True)
    row = dict(name=name, company=company, title=title, email=email, linkedin=linkedin,
               fit_score=fit_score, reason=reason, added=dt.datetime.now(dt.timezone.utc).isoformat())
    with open(DATA / "leads.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return f"lead saved: {name} @ {company}"


@action("lead_list", "List saved leads at or above a minimum fit score.",
        {"min_score": {"type": "integer"}})
def lead_list(min_score=0):
    p = DATA / "leads.jsonl"
    if not p.exists():
        return "no leads yet"
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    return json.dumps([r for r in rows if r["fit_score"] >= min_score][:50], indent=2)


# ---------- Drafts (human approves and sends) ----------
@action("draft_message", "Write a draft (email, linkedin, x, whatsapp, call-script) to outbox/ for human approval. Never sends.",
        {"channel": {"type": "string"}, "to": {"type": "string"}, "subject": {"type": "string"},
         "body": {"type": "string"}}, ["channel", "to", "body"])
def draft_message(channel, to, body, subject=""):
    OUTBOX.mkdir(exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    safe = re.sub(r"[^a-z0-9]+", "-", to.lower())[:30]
    f = OUTBOX / f"{stamp}-{channel}-{safe}.md"
    f.write_text(f"channel: {channel}\nto: {to}\nsubject: {subject}\nstatus: DRAFT\n\n{body}\n", encoding="utf-8")
    return f"draft saved: outbox/{f.name} (needs human approval)"


# ---------- Apollo (optional, needs APOLLO_API_KEY) ----------
@action("apollo_people_search", "Search Apollo for people by job titles and optional company domains/locations.",
        {"titles": {"type": "array", "items": {"type": "string"}},
         "company_domains": {"type": "array", "items": {"type": "string"}},
         "locations": {"type": "array", "items": {"type": "string"}},
         "per_page": {"type": "integer"}}, ["titles"])
def apollo_people_search(titles, company_domains=None, locations=None, per_page=10):
    import requests

    key = os.environ.get("APOLLO_API_KEY")
    if not key:
        return "APOLLO_API_KEY not set; skipping. Use your own knowledge only for ideas, not for real contacts."
    body = {"person_titles": titles, "per_page": min(per_page, 25)}
    if company_domains:
        body["q_organization_domains_list"] = company_domains
    if locations:
        body["person_locations"] = locations
    r = requests.post("https://api.apollo.io/api/v1/mixed_people/api_search",
                      headers={"X-Api-Key": key, "Content-Type": "application/json"}, json=body, timeout=30)
    r.raise_for_status()
    people = r.json().get("people", [])
    keep = ("first_name", "last_name", "title", "linkedin_url", "organization")
    return json.dumps([{k: p.get(k) if k != "organization" else (p.get(k) or {}).get("name") for k in keep}
                       for p in people], indent=2)


# ---------- HubSpot (optional, needs HUBSPOT_TOKEN) ----------
@action("hubspot_create_contact", "Create a contact in HubSpot CRM.",
        {"email": {"type": "string"}, "firstname": {"type": "string"}, "lastname": {"type": "string"},
         "company": {"type": "string"}, "jobtitle": {"type": "string"}}, ["email"])
def hubspot_create_contact(email, firstname="", lastname="", company="", jobtitle=""):
    import requests

    tok = os.environ.get("HUBSPOT_TOKEN")
    if not tok:
        return "HUBSPOT_TOKEN not set; logged nothing. Save to data/leads.jsonl via lead_add instead."
    r = requests.post("https://api.hubapi.com/crm/v3/objects/contacts",
                      headers={"Authorization": f"Bearer {tok}"},
                      json={"properties": dict(email=email, firstname=firstname, lastname=lastname,
                                               company=company, jobtitle=jobtitle)}, timeout=30)
    if r.status_code == 409:
        return "contact already exists in HubSpot"
    r.raise_for_status()
    return f"HubSpot contact created: id {r.json().get('id')}"
