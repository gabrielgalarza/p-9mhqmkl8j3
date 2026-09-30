"""Pull deals and prospect contacts from HubSpot and write site/data.json.

Runs daily in GitHub Actions. Needs a HubSpot private app token in the
HUBSPOT_TOKEN environment variable with these scopes:
  crm.objects.deals.read, crm.objects.contacts.read
Uses only the Python standard library.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.hubapi.com"
PORTAL_ID = os.environ.get("HUBSPOT_PORTAL_ID", "245486488")
OUT = Path(__file__).resolve().parent.parent / "site" / "data.json"

DEAL_PROPS = ["dealname", "dealstage", "amount", "closedate",
              "hs_deal_stage_probability", "hubspot_owner_id", "createdate"]
# Only what the funnel needs: no names, emails or companies for prospects.
CONTACT_PROPS = ["prospect_status", "outreach_step", "hubspot_owner_id", "createdate"]


def post(path, body, token, attempt=0):
    req = urllib.request.Request(
        API + path, data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        # HubSpot search is rate limited (~5 req/s); back off and retry.
        if e.code in (429, 500, 502, 503, 504) and attempt < 5:
            time.sleep(2 ** attempt)
            return post(path, body, token, attempt + 1)
        detail = e.read().decode(errors="replace")[:500]
        sys.exit(f"HubSpot {path} failed with {e.code}: {detail}")


def search_all(object_type, properties, token, filter_groups=None):
    rows, after = [], None
    while True:
        body = {"limit": 100, "properties": properties}
        if filter_groups:
            body["filterGroups"] = filter_groups
        if after:
            body["after"] = after
        page = post(f"/crm/v3/objects/{object_type}/search", body, token)
        rows += [{"id": r["id"], "properties": {k: r["properties"].get(k) for k in properties}}
                 for r in page.get("results", [])]
        after = page.get("paging", {}).get("next", {}).get("after")
        if not after:
            return rows
        time.sleep(0.25)


def main():
    token = os.environ.get("HUBSPOT_TOKEN")
    if not token:
        sys.exit("HUBSPOT_TOKEN is not set. Add it as a repository secret in GitHub.")
    deals = search_all("deals", DEAL_PROPS, token)
    contacts = search_all("contacts", CONTACT_PROPS, token, [
        {"filters": [{"propertyName": "prospect_status", "operator": "HAS_PROPERTY"}]}])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "portalId": PORTAL_ID,
        "deals": deals,
        "contacts": contacts,
    }, ensure_ascii=False, separators=(",", ":")))
    print(f"Wrote {len(deals)} deals and {len(contacts)} prospect contacts to {OUT}")


if __name__ == "__main__":
    main()
