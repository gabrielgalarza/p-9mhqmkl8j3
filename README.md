# OTT Sponsor Pipeline

Team dashboard for OTT sponsorship. It has three views:

- **Tracker**: closed won for the year and current quarter, plus open and weighted pipeline, with a stage filter.
- **Deal pipeline**: HubSpot deals laid out by stage.
- **Prospecting**: funnel conversion against the Sponsorship Collective benchmarks, using the OTT measurement rule.

## How it works

1. `.github/workflows/sync.yml` runs every morning at 7am Pacific, on every push to `main`, and whenever you click **Run workflow**.
2. `scripts/sync_hubspot.py` pulls deals and prospect counts from HubSpot into `site/data.json`.
3. The workflow publishes `site/` to GitHub Pages. HubSpot data is never committed to this repo.

The site has no login. It's unlisted: the name is random, and `robots.txt` plus a `noindex` tag keep search engines out. Anyone who has the link can open it. Prospect names, emails and companies are not synced.

## Setup

1. In HubSpot, create a service key with the `crm.objects.deals.read` and `crm.objects.contacts.read` scopes.
2. Add it as a repository secret named `HUBSPOT_TOKEN` (Settings → Secrets and variables → Actions).
3. Go to Actions → **Sync HubSpot** → Run workflow.

## Changing things

- **Refresh schedule**: edit the `cron` line in `.github/workflows/sync.yml`.
- **Owners in the filter**: edit `OWNERS` in `site/index.html`, and the `<select id="owner">` options there.
- **Benchmarks**: edit the `F` array in `renderProspecting()` in `site/index.html`.
