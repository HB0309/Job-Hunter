"""
One-time company slug discovery — bulk API probe.

Tests a large list of known tech company slug candidates directly against
Greenhouse / Lever / Ashby APIs (no search engines, no API keys, free).

Each ATS API returns 200 if the company board exists, 404 if not.
Results printed as ready-to-paste .env values.

Usage (inside Docker):
    MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/discover_companies.py
"""

import asyncio
import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Existing slugs (skip in output) ──────────────────────────────────────────

EXISTING_GREENHOUSE = set(filter(None, os.getenv("GREENHOUSE_BOARD_TOKENS", "").split(",")))
EXISTING_LEVER      = set(filter(None, os.getenv("LEVER_COMPANY_SLUGS", "").split(",")))
EXISTING_ASHBY      = set(filter(None, os.getenv("ASHBY_COMPANY_SLUGS", "").split(",")))

# ── Candidate slug lists ──────────────────────────────────────────────────────
# Covers: fintech, cybersecurity, cloud/infra, AI/ML, dev tools, SaaS, gaming,
# autonomous, health tech, consumer tech. Slugs are typically lowercase company
# names with hyphens. We test against all 3 ATSs — costs nothing, ~3 min.

CANDIDATES = [
    # Cybersecurity
    "crowdstrike", "sentinelone", "panw", "paloaltonetworks", "fortinet",
    "rapid7", "qualys", "tenable", "darktrace", "cyberark", "sailpoint",
    "beyondtrust", "exabeam", "secureworks", "vectra", "illumio",
    "lacework", "aquasecurity", "sysdig", "orca", "noname",
    "synack", "intigriti", "cobalt", "immunefi", "detectify",
    "drata", "vanta", "secureframe", "tugboat-logic", "hyperproof",
    "hatica", "anvilogic", "cymulate", "safebreach", "attacker",
    "abnormalsecuritycorp", "armorblox", "tessian", "ironscales",
    "proofpoint", "mimecast", "avanan", "material-security",
    "stairwell", "recordedfuturesinc", "threatconnect", "anomali",
    "flashpoint", "zerofox", "digitalshadows", "reliaquest",
    "expelco", "huntresslabs", "redcanary", "cybereason", "morphisec",
    "deepinstinct", "malwarebytes", "bitdefender", "eset", "sophos",
    "trellix", "mcafee-enterprise", "carbonblack", "cylance",
    "securly", "menlosecurity", "zscaler-inc",
    # Cloud / Infrastructure / DevOps
    "hashicorp", "chef", "puppet", "saltstack", "ansible",
    "grafana", "grafanalabs", "sumologic", "logdna", "papertrail",
    "dynatrace-inc", "appdynamics", "instana", "lightstep", "honeycomb",
    "last9", "groundcover", "highlight", "baselime",
    "cloudsmith", "jfrog", "sonatype", "snyk-inc", "aqua",
    "lacework-inc", "wiz-io", "orca-security",
    "hashicorp-inc", "pulumi", "env0", "spacelift", "scalr",
    "codefresh", "harness", "buildkite", "circleci", "semaphore",
    "launchdarkly", "split", "statsig", "eppo", "growthbook",
    "sentry", "rollbar", "bugsnag", "logrocket", "fullstory",
    "heap", "mixpanel", "amplitude-inc", "posthog",
    "segment-inc", "rudderstack", "mparticle", "tealium",
    "contentstack", "sanity", "storyblok", "prismic",
    "algolia", "typesense", "meilisearch",
    # AI / ML
    "huggingface", "weights-and-biases", "wandb", "neptune-ai",
    "scale", "labelbox", "scale-ai-inc", "datasaur", "snorkel-ai",
    "together", "groq-inc", "cerebras", "sambanova", "graphcore",
    "inflection-ai", "adept", "character-ai", "imbue", "mosaic",
    "mosaicml", "dbrx", "together-ai", "fireworks-ai",
    "deepmind", "openai-inc", "anthropic-inc",
    "cohere-inc", "ai21labs", "aleph-alpha", "stability",
    "midjourney", "runway", "pika", "kling", "invideo",
    "jasper", "writesonic", "copy-ai", "anyword",
    "glean", "guru", "notion-inc", "coda", "slite",
    "mem", "roam-research", "obsidian", "capacities",
    # Developer tools / Databases
    "cockroachdb", "cockroachlabs", "neon", "planetscale-inc",
    "fauna", "convex", "xata", "turso", "tidbcloud",
    "prisma", "hasura", "fauna-inc", "appwrite",
    "supabase-inc", "pocketbase", "directus",
    "postman", "insomnia", "hoppscotch", "bruno",
    "stoplight", "readme", "bump-sh", "redocly",
    "browserstack", "lambdatest", "sauce-labs",
    "percy", "chromatic", "applitools",
    "nx", "turborepo", "bazel", "pants",
    "buf", "connectrpc", "grpc-inc",
    # Fintech
    "affirm", "klarna", "afterpay", "sezzle", "zip",
    "marqeta", "chime", "current", "dave", "varo",
    "nerdwallet", "credit-karma", "experian", "equifax",
    "betterment", "wealthfront", "acorns", "stash",
    "robinhood-inc", "webull", "public-com",
    "coinbase-inc", "kraken", "gemini", "ftx-inc",
    "checkout-com", "adyen", "worldpay", "nuvei",
    "payoneer", "wise", "remitly", "xe", "western-union",
    "tipalti", "bill", "stampli", "airbase",
    "expensify", "brex-inc", "ramp-inc", "divvy",
    "mercury-bank", "relay", "found", "lili",
    "stripe-inc", "square-inc", "toast", "lightspeed",
    "clover", "olo", "tillster", "omnivore",
    "greenlight", "famzoo", "copper-banking",
    # SaaS / B2B
    "salesforce", "hubspot-inc", "freshworks", "zendesk-inc",
    "intercom-inc", "drift", "qualified", "conversica",
    "outreach", "salesloft", "gong", "clari", "chorus",
    "seismic", "highspot", "showpad", "bigtincan",
    "workato", "tray-io", "boomi", "mulesoft", "apiant",
    "zapier-inc", "make-com", "n8n-inc",
    "ironclad", "docusign", "pandadoc", "proposify",
    "contractbook", "juro", "leiga",
    "lattice", "15five", "culture-amp", "leapsome",
    "betterup", "noom", "headspace", "calm",
    "rippling-inc", "gusto-inc", "justworks", "deel",
    "remote", "papaya-global", "oyster-hr",
    "ashby-inc", "lever-inc", "greenhouse-inc",
    "jobvite", "icims", "smartrecruiters",
    # Gaming / Consumer / Media
    "epicgames", "riotgames", "unity", "unrealengine",
    "gameloft", "zynga", "ea", "activision", "blizzard",
    "ubisoft", "warnerbros-games", "2k", "take-two",
    "doubledown-interactive", "scopely", "jam-city",
    "duolingo-inc", "kahoot", "quizlet", "coursera",
    "udemy", "pluralsight", "linkedin-learning",
    "figma-inc", "canva", "miro", "whimsical", "lucid",
    "loom", "mmhmm", "descript", "riverside",
    "discord-inc", "reddit-inc", "tumblr", "snap-inc",
    "pinterest-inc", "tiktok", "bytedance",
    "spotify-inc", "soundcloud", "bandcamp", "audiomack",
    # E-commerce / Marketplace
    "shopify-inc", "bigcommerce", "woocommerce",
    "etsy", "depop", "poshmark", "thredup",
    "wayfair", "overstock", "houzz", "chairish",
    "chewy", "petco", "petsmart", "rover",
    "instacart-inc", "doordash-inc", "ubereats",
    "grubhub", "seamless", "caviar",
    # Autonomous / Robotics / Hardware
    "waymo", "cruise", "aurora", "nuro", "zoox",
    "argo-ai", "mobileye", "comma-ai",
    "boston-dynamics", "agility-robotics", "figure",
    "1x-technologies", "apptronik", "unitree",
    "zipline", "wing", "joby", "lilium", "archer",
    # Health Tech
    "oscarhealth", "oscar-health", "hims", "ro-health",
    "tempus", "flatiron", "veeva", "medidata",
    "devoted-health", "bright-health", "alignment",
    "transcarent", "included-health", "accolade",
    "livongo", "omada", "noom-health", "peloton",
    "headspace-health", "cerebral", "talkspace",
    "doxy-me", "doximity", "healthgrades",
    # Climate / Energy
    "climateai", "watershed", "planet", "tomorrow-io",
    "energy-vault", "form-energy", "ambri",
    "samsara-inc", "sense", "arcadia", "volterra",
    "charm-industrial", "heirloom", "climeworks",
    # Real estate / PropTech
    "opendoor", "offerpad", "orchard", "homeward",
    "ribbon-home", "knock", "homelight", "clever",
    "compass", "side", "real-brokerage",
    "loansnap", "better", "guaranteed-rate",
    "qualia", "snapdocs", "stavvy",
    # Other notable tech
    "palantir-inc", "anduril", "shield-ai", "primer",
    "scale-military", "sarcos", "exodyne",
    "nuro-inc", "starship", "coco",
    "alchemy", "infura", "moralis", "thirdweb",
    "opensea", "coinbase-nft", "magic-eden",
    "worldcoin", "ethereum", "polygon-technology",
]

# Deduplicate and sort
CANDIDATES = sorted(set(CANDIDATES))

# ── ATS API check functions ───────────────────────────────────────────────────

async def check_greenhouse(slug: str, client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(
            f"https://api.greenhouse.io/v1/boards/{slug}/jobs",
            params={"limit": 1}, timeout=6,
        )
        return r.status_code == 200
    except Exception:
        return False


async def check_lever(slug: str, client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(
            f"https://api.lever.co/v0/postings/{slug}",
            params={"mode": "json", "limit": 1}, timeout=6,
        )
        return r.status_code == 200
    except Exception:
        return False


async def check_ashby(slug: str, client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(
            f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
            timeout=6,
        )
        return r.status_code == 200
    except Exception:
        return False


# ── Async batch checker ───────────────────────────────────────────────────────

async def probe_all(candidates: list[str]) -> dict[str, list[str]]:
    """
    Test every candidate slug against all 3 ATSs concurrently.
    Uses a semaphore to cap concurrent requests and avoid rate limits.
    """
    results = {"greenhouse": [], "lever": [], "ashby": []}
    sem = asyncio.Semaphore(15)  # max 15 concurrent requests

    async def probe_one(slug: str, client: httpx.AsyncClient):
        async with sem:
            gh, lv, ash = await asyncio.gather(
                check_greenhouse(slug, client),
                check_lever(slug, client),
                check_ashby(slug, client),
            )
        if gh and slug not in EXISTING_GREENHOUSE:
            results["greenhouse"].append(slug)
            print(f"  ✓ greenhouse  {slug}")
        if lv and slug not in EXISTING_LEVER:
            results["lever"].append(slug)
            print(f"  ✓ lever       {slug}")
        if ash and slug not in EXISTING_ASHBY:
            results["ashby"].append(slug)
            print(f"  ✓ ashby       {slug}")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [probe_one(slug, client) for slug in candidates]
        total = len(tasks)
        done = 0
        for coro in asyncio.as_completed(tasks):
            await coro
            done += 1
            if done % 50 == 0:
                print(f"  ... {done}/{total} checked")

    return results


# ── Report ────────────────────────────────────────────────────────────────────

def print_report(verified: dict[str, list[str]]) -> None:
    ENV_KEYS = {
        "greenhouse": "GREENHOUSE_BOARD_TOKENS",
        "lever":      "LEVER_COMPANY_SLUGS",
        "ashby":      "ASHBY_COMPANY_SLUGS",
    }
    EXISTING = {
        "greenhouse": EXISTING_GREENHOUSE,
        "lever":      EXISTING_LEVER,
        "ashby":      EXISTING_ASHBY,
    }

    total = sum(len(v) for v in verified.values())
    print("\n" + "═" * 60)
    print("RESULTS — paste into .env")
    print("═" * 60)
    print(f"\nFound {total} new verified companies\n")

    for ats, new_slugs in verified.items():
        if not new_slugs:
            print(f"{ats.upper()}: nothing new found\n")
            continue
        new_slugs = sorted(new_slugs)
        all_slugs = sorted(EXISTING[ats] | set(new_slugs) - {""})
        print(f"── {ats.upper()} (+{len(new_slugs)} new) ──")
        print(f"New: {', '.join(new_slugs)}\n")
        print(f"{ENV_KEYS[ats]}={','.join(all_slugs)}")
        print()

    if total > 0:
        print("Next steps:")
        print("  1. Paste updated vars into .env")
        print("  2. docker compose up -d --build")
        print("  3. MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/seed_sources.py")
        print("  4. MSYS_NO_PATHCONV=1 docker compose exec backend python -m app.workers.run_ingestion")


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    new_candidates = [
        s for s in CANDIDATES
        if s not in EXISTING_GREENHOUSE
        and s not in EXISTING_LEVER
        and s not in EXISTING_ASHBY
    ]
    print(f"Job Hunter — Company Discovery")
    print(f"Testing {len(new_candidates)} slug candidates against 3 ATSs")
    print(f"(skipping {len(CANDIDATES) - len(new_candidates)} already seeded)\n")
    print("Hits:")

    verified = await probe_all(new_candidates)
    print_report(verified)


if __name__ == "__main__":
    asyncio.run(main())
