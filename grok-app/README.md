# Use the agents inside the Grok app (no API, no code)

Each file here is one paste-ready instruction block for one layer.

1. In the Grok app, create a Project (or Custom Agent) per layer, named like the file.
2. Paste the whole file into its instructions.
3. Fill in `config/company.yaml` and upload it to each project as a file.
4. Chat with it: start a message with `agent: tam-mapper` plus your task.

Grok can't write files or call tools from here. Drafts and notes come back as labeled blocks:
`DRAFT (channel, to)` and `SAVE TO BRAIN: folder/file.md`. Copy those into your own folders.

If your plan limits how many custom agents you can have, merge files:
Acquisition | Nurture | Convert + Onboard | Fulfill + Second brain.

Regenerate after editing any agent: `python tools/build_grok_app.py`
