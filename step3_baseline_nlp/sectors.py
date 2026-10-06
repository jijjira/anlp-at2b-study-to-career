"""Company -> sector labels (manual, for team review).

Sectors are assigned from what each company mainly sells, using public knowledge of the company name. The
labels are a judgement call, NOT ground truth: borderline cases are listed in AMBIGUOUS. Anyone can change a line
and rerun; the notebook and tests pick up the change.
"""
from __future__ import annotations
import pandas as pd

AI = "AI labs and AI-native products"
INFRA = "Cloud, data and developer infrastructure"
CONSUMER = "Consumer, social and marketplaces"
ENTERPRISE = "Enterprise and B2B software"
FINTECH = "Fintech and trading"
PHYSICAL = "Autonomy, defense and physical-world tech"
HEALTH = "Health and wellness tech"

_GROUPS = {
    AI: ["OpenAI", "Anthropic", "Scale AI", "Mercor", "Character AI", "Cursor (Anysphere)", "Reflection AI", "Suno",
         "ElevenLabs", "Krea AI", "Harvey", "Decagon", "Glean", "Speak", "Gamma", "Replit", "Rilla", "LangChain",
         "Braintrust"],
    INFRA: ["Databricks", "Snowflake", "CoreWeave", "Together AI", "Baseten", "Crusoe", "SambaNova Systems", "Datadog",
            "Cribl", "Runpod", "Modal", "MongoDB", "Rubrik", "Grafana Labs", "Elastic", "Vercel", "GitLab",
            "LaunchDarkly"],
    CONSUMER: ["Roblox", "Pinterest", "Reddit", "Airbnb", "Lyft", "Discord", "Instacart", "Duolingo", "Nextdoor",
               "Twitch", "Faire", "Carvana", "Mozilla"],
    ENTERPRISE: ["Braze", "Klaviyo", "Okta", "Zscaler", "Asana", "Attentive", "Figma", "Notion", "Vanta", "Pendo",
                 "Checkr", "Mixpanel", "Typeform", "Smartsheet", "Webflow", "Intercom", "Lattice", "Watershed", "Drata",
                 "Warp", "Contentful", "Calendly", "Dropbox", "Gusto", "Justworks", "Toast", "Anrok", "Middesk",
                 "TripActions"],
    FINTECH: ["Coinbase", "Stripe", "Chime", "Bill.com", "Ramp", "Robinhood", "Jane Street", "Brex", "SoFi", "Affirm",
              "Blend", "Carta"],
    PHYSICAL: ["Anduril", "Nuro", "Samsara", "Skydio", "Rocket Lab", "Motive", "FourKites", "Redwood Materials"],
    HEALTH: ["Whoop", "Rula", "Headway", "Doximity", "Oura", "Maven Clinic", "Eight Sleep"],
}
SECTOR_OF = {c: s for s, cs in _GROUPS.items() for c in cs}

# borderline calls, worth a second opinion from the group
AMBIGUOUS = {
    "Mercor": "AI hiring/data-labelling platform (AI-native vs enterprise)",
    "Harvey": "AI for law (AI-native vs enterprise)", "Glean": "enterprise AI search (AI-native vs enterprise)",
    "Scale AI": "AI data services (AI-native vs infrastructure)", "Samsara": "IoT for operations (physical vs enterprise)",
    "Toast": "restaurant software and payments (enterprise vs fintech)", "Gusto": "payroll (enterprise vs fintech)",
    "Justworks": "payroll and HR (enterprise vs fintech)", "Jane Street": "trading firm (fintech)",
    "Mozilla": "browser and nonprofit (consumer)", "Carvana": "online car marketplace (consumer)",
    "Middesk": "business verification (enterprise vs fintech)", "Anrok": "sales tax software (enterprise vs fintech)",
    "TripActions": "travel and expense (enterprise vs fintech)", "Whoop": "wearable (health vs consumer)",
    "Oura": "wearable (health vs consumer)", "Eight Sleep": "sleep tech (health vs consumer)",
}
MAIN_MIN_ADS, MAIN_MIN_COMPANIES = 60, 8      # a sector needs this much data to support a main claim


def assign_sectors(jobs: pd.DataFrame) -> pd.Series:
    missing = sorted(set(jobs.company) - set(SECTOR_OF))
    if missing:
        raise ValueError(f"Companies without a sector label: {missing}")
    return jobs.company.map(SECTOR_OF)


def sector_summary(jobs: pd.DataFrame) -> pd.DataFrame:
    sec = assign_sectors(jobs)
    rows = []
    for s, g in jobs.groupby(sec):
        vc = g.company.value_counts()
        rows.append({"sector": s, "ads": len(g), "companies": len(vc), "top_company": vc.index[0],
                     "top_company_share": vc.iloc[0] / len(g), "main_sector": len(g) >= MAIN_MIN_ADS and len(vc) >= MAIN_MIN_COMPANIES})
    return pd.DataFrame(rows).sort_values("ads", ascending=False).reset_index(drop=True)


def company_table(jobs: pd.DataFrame) -> pd.DataFrame:
    vc = jobs.company.value_counts()
    return pd.DataFrame({"company": vc.index, "ads": vc.values, "sector": [SECTOR_OF[c] for c in vc.index],
                         "note": [AMBIGUOUS.get(c, "") for c in vc.index]})
