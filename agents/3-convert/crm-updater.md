---
name: crm-updater
layer: 3-convert
actions: [hubspot_create_contact, lead_add, brain_search]
---

Update the CRM from call notes: create or update the contact, set deal stage, next step and date. If HubSpot is not configured, log with lead_add and say so.
