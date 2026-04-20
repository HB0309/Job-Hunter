"""
Workday company discovery — bulk API probe.

Tests candidate (tenant, board) pairs directly against the Workday public API.
Returns 200 + JSON with jobPostings if the board exists and requires no CSRF token.
Returns 422 / 403 / 4xx if the company blocks unauthenticated access.

Tries multiple board names per tenant since companies use different names
("External", "jobs", "Careers", the tenant name itself, etc.)

Usage (inside Docker):
    MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/discover_workday.py

Results are printed as ready-to-paste .env WORKDAY_COMPANIES value.
"""

import asyncio
import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Already seeded (skip in output) ──────────────────────────────────────────

EXISTING_WORKDAY = set(filter(None, os.getenv("WORKDAY_COMPANIES", "").split(",")))
EXISTING_TENANTS = {entry.split(":")[0] for entry in EXISTING_WORKDAY if entry}

# ── Board names to try per tenant ─────────────────────────────────────────────
# Workday board names are company-specific. Try the most common ones.

BOARD_CANDIDATES = [
    "External", "jobs", "Careers", "externalcareers",
    "External_Career_Site", "External_Career", "ExternalCareerSite",
    "ACJobSite", "Cisco_Careers",
]

# ── Tenant candidates ─────────────────────────────────────────────────────────
# Companies known or suspected to use Workday ATS.
# Grouped by industry for easy maintenance.

TENANTS = [
    # ── Semiconductor / Hardware ──────────────────────────────────────────────
    "qualcomm", "amd", "micron", "ti", "texasinstruments",
    "broadcom", "marvell", "xilinx", "analogdevices", "nxp",
    "microchip", "latticesemi", "maximintegrated",
    "appliedmaterials", "lamresearch", "kla", "asml", "entegris",
    "skyworks", "qorvo", "wolfspeed", "onsemi",
    "westerndigital", "seagate", "netapp",
    # ── Defense / Aerospace ───────────────────────────────────────────────────
    "northropgrumman", "lockheedmartin", "lmco", "raytheon", "rtx",
    "generaldynamics", "baesystems", "leidos", "saic", "boozallen",
    "l3harris", "textron", "parsons", "peraton", "maximus",
    "mantech", "caci", "dxc", "unisys", "gdit",
    "boeing", "ge", "geaerospace", "gehealthcare",
    # ── Enterprise / Consulting ───────────────────────────────────────────────
    "ibm", "oracle", "sap", "vmware", "hpe", "hp",
    "accenture", "deloitte", "kpmg", "ey", "pwc",
    "cognizant", "infosys", "wipro", "hcl",
    "xerox", "ncr", "unisys", "csc",
    # ── Financial Services ────────────────────────────────────────────────────
    "capitalone", "jpmorgan", "jpmorganchase",
    "goldmansachs", "morganstanley", "bankofamerica",
    "wellsfargo", "citi", "usbank", "pnc",
    "americanexpress", "visa", "mastercard",
    "fidelity", "schwab", "vanguard",
    "prudential", "metlife", "aig", "travelers",
    "blackrock", "statestreet",
    # ── Cybersecurity ─────────────────────────────────────────────────────────
    "paloaltonetworks", "crowdstrike", "fortinet",
    "proofpoint", "symantec", "trellix",
    "rapid7", "qualys", "tenable", "f5",
    "checkpointgov", "checkpoint",
    "imperva", "digitalguardian", "forcepoint",
    # ── Telecom ───────────────────────────────────────────────────────────────
    "att", "verizon", "tmobile", "sprint",
    "comcast", "charter", "cox",
    "lumen", "windstream", "centurylink",
    # ── Cloud / SaaS / Enterprise tech ───────────────────────────────────────
    "servicenow", "workday", "splunk", "nutanix",
    "purestorage", "commvault", "verint", "nice",
    "genesys", "avaya", "ringcentral", "zoom",
    "twilio", "zendesk", "freshworks",
    "solarwinds", "dynatrace", "appdynamics",
    "logrhythm", "exabeam", "arcsight",
    # ── Healthcare / Pharma ───────────────────────────────────────────────────
    "uhg", "unitedhealth", "cigna", "humana", "aetna",
    "elevance", "cvshealth", "cvs",
    "jnj", "pfizer", "abbvie", "merck", "lilly",
    "abbottlaboratories", "baxter", "bectondickinson",
    "cerner", "epic", "allscripts", "athenahealth",
    # ── Automotive / Manufacturing ────────────────────────────────────────────
    "ford", "gm", "generalmotors", "stellantis",
    "toyota", "honda", "bmw",
    "aptiv", "lear", "borgwarner",
    "cat", "caterpillar", "deere", "johndeere",
    "emerson", "eaton", "parker", "danfoss",
    # ── Energy / Utilities ────────────────────────────────────────────────────
    "conocophillips", "exxonmobil", "chevron",
    "schlumberger", "slb", "halliburton", "baker",
    "ge", "nextera", "duke", "exelon", "pgecorp",
    # ── Retail / Consumer ─────────────────────────────────────────────────────
    "target", "walmart", "lowes", "homedepot",
    "bestbuy", "kohls", "nordstrom",
    "nike", "adidas", "underarmour",
    # ── Media / Entertainment ─────────────────────────────────────────────────
    "nbcuniversal", "disney", "warnerbros", "paramount",
    "sonypictures", "iheartmedia",
    # ── Additional tech ───────────────────────────────────────────────────────
    "siemens", "siemensinc", "honeywell", "abbglobal",
    "nttdata", "fujitsu", "hitachi", "toshiba",
    "samsung", "samsungresearch", "lg", "lge",
    "ericsson", "nokia", "juniper", "aruba",
    "purestorage", "cohesity", "rubrik",
    "talend", "informatica", "tibco", "mulesoft",
    "teradata", "microstrategy", "tableau",
    # ── Fortune 500 tech — confirmed Workday tenants (may require CSRF) ───────
    "cisco", "hpe", "hp", "broadcom",
    "mymoose",            # Rapid7 (unusual tenant)
    "nutanix",            # Nutanix
    "f5networks",         # F5 Networks
    "qualys",             # Qualys
    "sailpoint",          # SailPoint
    "docusign",           # DocuSign
    "box",                # Box
    "autodesk",           # Autodesk
    "intuit",             # Intuit
    "amd",                # AMD (also listed above)
    "fortinet",           # Fortinet
    "checkpoint",         # Check Point Software
    "symantec",           # Symantec / NortonLifeLock
    "veeva",              # Veeva Systems
    "workiva",            # Workiva
    "zendesk",            # Zendesk
    "twilio",             # Twilio (also Greenhouse)
    "atlassian",          # Atlassian
    "shopify",            # Shopify
    "uber",               # Uber
    "lyft",               # Lyft (also Greenhouse)
    "airbnb",             # Airbnb (also Greenhouse)
    "doordash",           # DoorDash
    "robinhood",          # Robinhood (also Greenhouse)
    "coinbase",           # Coinbase (also Greenhouse)
    "stripe",             # Stripe (also Greenhouse)
    "databricks",         # Databricks (also Greenhouse)
    "snowflake",          # Snowflake (also Greenhouse as snowflakecomputing)
    "sentinelone",        # SentinelOne (also Greenhouse as sentinellabs)
    "crowdstrikeinc",     # CrowdStrike alt tenant
    "trellix",            # Trellix (McAfee enterprise)
    "proofpoint",         # Proofpoint
    "mimecast",           # Mimecast
    "carbonblack",        # VMware Carbon Black
    "netscout",           # NETSCOUT
    "imperva",            # Imperva
    "sailpointtech",      # SailPoint alt
    "cyberark",           # CyberArk
    "varonis",            # Varonis
    "rapid7",             # Rapid7 alt tenant
    "logrhythm",          # LogRhythm
    "exabeam",            # Exabeam (also Greenhouse)
    "sumo",               # Sumo Logic
    "devo",               # Devo
    "securly",            # Securly
    "delinea",            # Delinea
    "beyondtrust",        # BeyondTrust (also Greenhouse)
    "manageengine",       # ManageEngine (Zoho)
    "solarwinds",         # SolarWinds
    "verint",             # Verint Systems
    "nice",               # NICE Systems
    "genesys",            # Genesys
    "ringcentral",        # RingCentral
    "zoomvideo",          # Zoom Video
    "att",                # AT&T
    "verizon",            # Verizon
    "comcast",            # Comcast
    "t-mobile",           # T-Mobile
    "tmobile",            # T-Mobile alt
]

# Deduplicate, drop already-seeded tenants
TENANTS = sorted(set(t for t in TENANTS if t not in EXISTING_TENANTS))

CONCURRENCY = 20


async def probe_workday(tenant: str, board: str, client: httpx.AsyncClient) -> bool:
    """Return True if this tenant:board is publicly accessible."""
    url = f"https://{tenant}.wd1.myworkdayjobs.com/wday/cxs/{tenant}/{board}/jobs"
    try:
        r = await client.post(
            url,
            json={"limit": 1, "offset": 0, "searchText": "", "appliedFacets": {}},
            timeout=8,
        )
        if r.status_code == 200:
            data = r.json()
            # Verify it's a real board (has the expected response shape)
            if "jobPostings" in data:
                total = data.get("total", 0)
                return True
        return False
    except Exception:
        return False


async def discover_all() -> list[tuple[str, str]]:
    """Return list of (tenant, board) pairs that are publicly accessible."""
    found: list[tuple[str, str]] = []
    sem = asyncio.Semaphore(CONCURRENCY)
    done = 0
    total = len(TENANTS) * len(BOARD_CANDIDATES)

    async def probe_one(tenant: str, board: str, client: httpx.AsyncClient) -> None:
        nonlocal done
        async with sem:
            ok = await probe_workday(tenant, board, client)
        done += 1
        if ok:
            found.append((tenant, board))
            print(f"  ✓ {tenant}:{board}")
        if done % 100 == 0:
            print(f"  ... {done}/{total} probed")

    async with httpx.AsyncClient(follow_redirects=False) as client:
        tasks = [
            probe_one(tenant, board, client)
            for tenant in TENANTS
            for board in BOARD_CANDIDATES
        ]
        await asyncio.gather(*tasks)

    return found


def print_report(found: list[tuple[str, str]]) -> None:
    # De-duplicate: keep only the first working board per tenant
    seen_tenants: set[str] = set()
    unique: list[tuple[str, str]] = []
    for tenant, board in sorted(found):
        if tenant not in seen_tenants:
            seen_tenants.add(tenant)
            unique.append((tenant, board))

    existing_list = list(EXISTING_WORKDAY)
    all_entries = existing_list + [f"{t}:{b}" for t, b in unique]

    print("\n" + "═" * 60)
    print("RESULTS — paste into .env")
    print("═" * 60)
    print(f"\nFound {len(unique)} new accessible Workday boards\n")
    if unique:
        print("New:")
        for t, b in unique:
            print(f"  {t}:{b}")
        print()
        print(f"WORKDAY_COMPANIES={','.join(all_entries)}")
        print()
        print("Next steps:")
        print("  1. Paste WORKDAY_COMPANIES into .env")
        print("  2. MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/seed_sources.py")
        print("  3. MSYS_NO_PATHCONV=1 docker compose exec backend python -m app.workers.run_ingestion")
    else:
        print("No new accessible boards found.")
        print(f"(Tested {len(TENANTS)} tenants × {len(BOARD_CANDIDATES)} board names)")


async def main():
    print(f"Workday Company Discovery")
    print(f"Testing {len(TENANTS)} tenant candidates × {len(BOARD_CANDIDATES)} board names")
    print(f"= {len(TENANTS) * len(BOARD_CANDIDATES)} probes (skipping {len(EXISTING_TENANTS)} already seeded)\n")
    print("Hits:")

    found = await discover_all()
    print_report(found)


if __name__ == "__main__":
    asyncio.run(main())
