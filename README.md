# grok-ai-native-firm

A Grok-powered agent team that runs the 6 layers of an AI-native firm: sell the outcome at an agency price, run it with software-like costs.

Based on the 6-layer setup Tim Scheuer shared, inspired by Sequoia's "next $1T idea is the AI-native firm."

![How it works](docs/demo.gif)

```
1 Acquisition -> 2 Nurture -> 3 Convert -> 4 Onboard -> 5 Fulfill
                         \________ 6 Second brain (everything filed + linked) ________/
```

## Agents (17)

| Layer | Agents | What they do |
|---|---|---|
| 1 Acquisition | tam-mapper, lead-qualifier, outbound-writer, content-planner, engagement-responder | Map TAM, build/qualify lead list (Apollo), multi-channel outbound, LinkedIn/X content, DM people who engage |
| 2 Nurture | lead-magnet-builder, webinar-planner, newsletter-writer, lead-reactivator | Lead magnets, bi-weekly webinars, newsletter, revive stale leads |
| 3 Convert | account-researcher, call-notes-summarizer, crm-updater | Pre-call brief, notetaker output to summary, CRM update (HubSpot) |
| 4 Onboard | kickoff-planner, contract-onboarding | Kickoff plan, contract outline + welcome flow |
| 5 Fulfill | sop-writer, service-delivery | Write SOPs, deliver the one productized service by them |
| 6 Second brain | brain-librarian | File, link ([[wiki-links]]) and index every post, lead, call, client and SOP |

## Actions (what agents can do)

`brain_write` `brain_read` `brain_search` `brain_backlinks` `lead_add` `lead_list` `draft_message` `apollo_people_search` `hubspot_create_contact`

Safety by design: agents **never send anything**. Messages are saved to `outbox/` as drafts for you to approve. Every run is filed in `brain/runs/`.

## Setup

```bash
git clone https://github.com/rakeshSabbathi/grok-ai-native-firm-rakesh.git
cd grok-ai-native-firm-rakesh
pip install -r requirements.txt
cp .env.example .env        # add XAI_API_KEY (console.x.ai); Apollo/HubSpot keys optional
```

Edit `config/company.yaml` with your offer, ICP and voice. Every agent reads it.

## Use

```bash
python run.py list
python run.py agent tam-mapper "AI-native RevOps agency for D2C brands in India"
python run.py workflow acquisition "AI-native RevOps agency for D2C brands in India"
python run.py workflow convert "Acme Pvt Ltd, call notes: ..."
pytest -q                   # offline sanity checks
```

Workflows live in `workflows/workflows.yaml`. Add a step or a new workflow by editing YAML. Add an agent by dropping a markdown file in `agents/<layer>/` with `name`, `actions` and a prompt.

## Structure

```
agents/      one markdown spec per agent, grouped by layer
core/        grok.py (xAI client), agent.py (runner), actions.py (tools)
workflows/   YAML pipelines per layer
brain/       second brain: leads, calls, clients, sops, content, runs
config/      company.yaml
outbox/      drafts waiting for your approval
```

## Notes

- Grok runs through xAI's OpenAI-compatible API (`https://api.x.ai/v1`). Change the model with `GROK_MODEL`.
- Only the Apollo and HubSpot actions call outside services, and only if you set their keys.
- Notetakers (Granola, Fathom, Fireflies), Zoom/Meet and contract/payment tools aren't wired in yet. Paste their output into the `convert` and `onboard` workflows.

MIT License
