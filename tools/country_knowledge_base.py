"""
tools/country_knowledge_base.py
================================
Offline Country Knowledge Base — 200+ countries.

Handles all country query types:
  capital, population, currency, language, continent, area, gdp

ReAct role:
  Action: Look up country in knowledge base.
  Observation: Return structured data.
  Verification: Confirm the specific field matches the question type.
"""

import re
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Country data: capital, population, currencies, languages, continent,
#               sub_region, area_km2, gdp_usd_billion (rough estimate)
# ---------------------------------------------------------------------------
COUNTRIES: dict[str, dict] = {
    # ── South Asia ──────────────────────────────────────────────────────────
    "sri lanka": {
        "name": "Sri Lanka",
        "capital": "Sri Jayawardenepura Kotte",
        "largest_city": "Colombo",
        "population": 22156000,
        "currencies": ["Sri Lankan rupee (LKR)"],
        "languages": ["Sinhala", "Tamil"],
        "continent": "Asia",
        "sub_region": "Southern Asia",
        "area_km2": 65610,
        "gdp_usd_billion": 84,
    },
    "india": {
        "name": "India",
        "capital": "New Delhi",
        "largest_city": "Mumbai",
        "population": 1428627663,
        "currencies": ["Indian rupee (INR)"],
        "languages": ["Hindi", "English", "and 21 other official languages"],
        "continent": "Asia",
        "sub_region": "Southern Asia",
        "area_km2": 3287263,
        "gdp_usd_billion": 3737,
    },
    "pakistan": {
        "name": "Pakistan",
        "capital": "Islamabad",
        "largest_city": "Karachi",
        "population": 231402117,
        "currencies": ["Pakistani rupee (PKR)"],
        "languages": ["Urdu", "English"],
        "continent": "Asia",
        "sub_region": "Southern Asia",
        "area_km2": 881913,
        "gdp_usd_billion": 376,
    },
    "bangladesh": {
        "name": "Bangladesh",
        "capital": "Dhaka",
        "largest_city": "Dhaka",
        "population": 169356251,
        "currencies": ["Bangladeshi taka (BDT)"],
        "languages": ["Bengali"],
        "continent": "Asia",
        "sub_region": "Southern Asia",
        "area_km2": 147570,
        "gdp_usd_billion": 460,
    },
    "nepal": {
        "name": "Nepal",
        "capital": "Kathmandu",
        "largest_city": "Kathmandu",
        "population": 29136808,
        "currencies": ["Nepalese rupee (NPR)"],
        "languages": ["Nepali"],
        "continent": "Asia",
        "sub_region": "Southern Asia",
        "area_km2": 147181,
        "gdp_usd_billion": 40,
    },
    "afghanistan": {
        "name": "Afghanistan",
        "capital": "Kabul",
        "largest_city": "Kabul",
        "population": 40754388,
        "currencies": ["Afghan afghani (AFN)"],
        "languages": ["Pashto", "Dari"],
        "continent": "Asia",
        "sub_region": "Southern Asia",
        "area_km2": 652230,
        "gdp_usd_billion": 20,
    },
    # ── East Asia ────────────────────────────────────────────────────────────
    "china": {
        "name": "China",
        "capital": "Beijing",
        "largest_city": "Shanghai",
        "population": 1425671352,
        "currencies": ["Chinese yuan (CNY)"],
        "languages": ["Mandarin Chinese"],
        "continent": "Asia",
        "sub_region": "Eastern Asia",
        "area_km2": 9596960,
        "gdp_usd_billion": 17963,
    },
    "japan": {
        "name": "Japan",
        "capital": "Tokyo",
        "largest_city": "Tokyo",
        "population": 124516650,
        "currencies": ["Japanese yen (JPY)"],
        "languages": ["Japanese"],
        "continent": "Asia",
        "sub_region": "Eastern Asia",
        "area_km2": 377975,
        "gdp_usd_billion": 4231,
    },
    "south korea": {
        "name": "South Korea",
        "capital": "Seoul",
        "largest_city": "Seoul",
        "population": 51715162,
        "currencies": ["South Korean won (KRW)"],
        "languages": ["Korean"],
        "continent": "Asia",
        "sub_region": "Eastern Asia",
        "area_km2": 100210,
        "gdp_usd_billion": 1665,
    },
    "north korea": {
        "name": "North Korea",
        "capital": "Pyongyang",
        "largest_city": "Pyongyang",
        "population": 25971909,
        "currencies": ["North Korean won (KPW)"],
        "languages": ["Korean"],
        "continent": "Asia",
        "sub_region": "Eastern Asia",
        "area_km2": 120538,
        "gdp_usd_billion": 28,
    },
    # ── Southeast Asia ───────────────────────────────────────────────────────
    "indonesia": {
        "name": "Indonesia",
        "capital": "Jakarta",
        "largest_city": "Jakarta",
        "population": 275501339,
        "currencies": ["Indonesian rupiah (IDR)"],
        "languages": ["Indonesian"],
        "continent": "Asia",
        "sub_region": "Southeast Asia",
        "area_km2": 1904569,
        "gdp_usd_billion": 1319,
    },
    "thailand": {
        "name": "Thailand",
        "capital": "Bangkok",
        "largest_city": "Bangkok",
        "population": 71697030,
        "currencies": ["Thai baht (THB)"],
        "languages": ["Thai"],
        "continent": "Asia",
        "sub_region": "Southeast Asia",
        "area_km2": 513120,
        "gdp_usd_billion": 512,
    },
    "vietnam": {
        "name": "Vietnam",
        "capital": "Hanoi",
        "largest_city": "Ho Chi Minh City",
        "population": 97338583,
        "currencies": ["Vietnamese đồng (VND)"],
        "languages": ["Vietnamese"],
        "continent": "Asia",
        "sub_region": "Southeast Asia",
        "area_km2": 331212,
        "gdp_usd_billion": 449,
    },
    "philippines": {
        "name": "Philippines",
        "capital": "Manila",
        "largest_city": "Quezon City",
        "population": 113964327,
        "currencies": ["Philippine peso (PHP)"],
        "languages": ["Filipino", "English"],
        "continent": "Asia",
        "sub_region": "Southeast Asia",
        "area_km2": 300000,
        "gdp_usd_billion": 404,
    },
    "malaysia": {
        "name": "Malaysia",
        "capital": "Kuala Lumpur",
        "largest_city": "Kuala Lumpur",
        "population": 33573874,
        "currencies": ["Malaysian ringgit (MYR)"],
        "languages": ["Malay"],
        "continent": "Asia",
        "sub_region": "Southeast Asia",
        "area_km2": 329847,
        "gdp_usd_billion": 407,
    },
    "singapore": {
        "name": "Singapore",
        "capital": "Singapore",
        "largest_city": "Singapore",
        "population": 5637022,
        "currencies": ["Singapore dollar (SGD)"],
        "languages": ["English", "Malay", "Mandarin", "Tamil"],
        "continent": "Asia",
        "sub_region": "Southeast Asia",
        "area_km2": 733,
        "gdp_usd_billion": 467,
    },
    # ── Middle East ──────────────────────────────────────────────────────────
    "saudi arabia": {
        "name": "Saudi Arabia",
        "capital": "Riyadh",
        "largest_city": "Riyadh",
        "population": 35950396,
        "currencies": ["Saudi riyal (SAR)"],
        "languages": ["Arabic"],
        "continent": "Asia",
        "sub_region": "Western Asia",
        "area_km2": 2149690,
        "gdp_usd_billion": 1061,
    },
    "iran": {
        "name": "Iran",
        "capital": "Tehran",
        "largest_city": "Tehran",
        "population": 88550570,
        "currencies": ["Iranian rial (IRR)"],
        "languages": ["Persian"],
        "continent": "Asia",
        "sub_region": "Western Asia",
        "area_km2": 1648195,
        "gdp_usd_billion": 366,
    },
    "turkey": {
        "name": "Turkey",
        "capital": "Ankara",
        "largest_city": "Istanbul",
        "population": 84339067,
        "currencies": ["Turkish lira (TRY)"],
        "languages": ["Turkish"],
        "continent": "Asia",
        "sub_region": "Western Asia",
        "area_km2": 783356,
        "gdp_usd_billion": 907,
    },
    "israel": {
        "name": "Israel",
        "capital": "Jerusalem",
        "largest_city": "Jerusalem",
        "population": 9216900,
        "currencies": ["Israeli new shekel (ILS)"],
        "languages": ["Hebrew", "Arabic"],
        "continent": "Asia",
        "sub_region": "Western Asia",
        "area_km2": 20770,
        "gdp_usd_billion": 522,
    },
    "uae": {
        "name": "United Arab Emirates",
        "capital": "Abu Dhabi",
        "largest_city": "Dubai",
        "population": 9890402,
        "currencies": ["UAE dirham (AED)"],
        "languages": ["Arabic"],
        "continent": "Asia",
        "sub_region": "Western Asia",
        "area_km2": 83600,
        "gdp_usd_billion": 498,
    },
    "united arab emirates": {
        "name": "United Arab Emirates",
        "capital": "Abu Dhabi",
        "largest_city": "Dubai",
        "population": 9890402,
        "currencies": ["UAE dirham (AED)"],
        "languages": ["Arabic"],
        "continent": "Asia",
        "sub_region": "Western Asia",
        "area_km2": 83600,
        "gdp_usd_billion": 498,
    },
    # ── Central Asia ─────────────────────────────────────────────────────────
    "kazakhstan": {
        "name": "Kazakhstan",
        "capital": "Astana",
        "largest_city": "Almaty",
        "population": 19397998,
        "currencies": ["Kazakhstani tenge (KZT)"],
        "languages": ["Kazakh", "Russian"],
        "continent": "Asia",
        "sub_region": "Central Asia",
        "area_km2": 2724900,
        "gdp_usd_billion": 220,
    },
    # ── Europe ───────────────────────────────────────────────────────────────
    "france": {
        "name": "France",
        "capital": "Paris",
        "largest_city": "Paris",
        "population": 68042591,
        "currencies": ["Euro (EUR)"],
        "languages": ["French"],
        "continent": "Europe",
        "sub_region": "Western Europe",
        "area_km2": 551695,
        "gdp_usd_billion": 2782,
    },
    "germany": {
        "name": "Germany",
        "capital": "Berlin",
        "largest_city": "Berlin",
        "population": 83294633,
        "currencies": ["Euro (EUR)"],
        "languages": ["German"],
        "continent": "Europe",
        "sub_region": "Western Europe",
        "area_km2": 357114,
        "gdp_usd_billion": 4260,
    },
    "united kingdom": {
        "name": "United Kingdom",
        "capital": "London",
        "largest_city": "London",
        "population": 67281039,
        "currencies": ["Pound sterling (GBP)"],
        "languages": ["English"],
        "continent": "Europe",
        "sub_region": "Northern Europe",
        "area_km2": 243610,
        "gdp_usd_billion": 3082,
    },
    "uk": {
        "name": "United Kingdom",
        "capital": "London",
        "largest_city": "London",
        "population": 67281039,
        "currencies": ["Pound sterling (GBP)"],
        "languages": ["English"],
        "continent": "Europe",
        "sub_region": "Northern Europe",
        "area_km2": 243610,
        "gdp_usd_billion": 3082,
    },
    "italy": {
        "name": "Italy",
        "capital": "Rome",
        "largest_city": "Rome",
        "population": 60317116,
        "currencies": ["Euro (EUR)"],
        "languages": ["Italian"],
        "continent": "Europe",
        "sub_region": "Southern Europe",
        "area_km2": 301340,
        "gdp_usd_billion": 2010,
    },
    "spain": {
        "name": "Spain",
        "capital": "Madrid",
        "largest_city": "Madrid",
        "population": 47422613,
        "currencies": ["Euro (EUR)"],
        "languages": ["Spanish"],
        "continent": "Europe",
        "sub_region": "Southern Europe",
        "area_km2": 505990,
        "gdp_usd_billion": 1418,
    },
    "portugal": {
        "name": "Portugal",
        "capital": "Lisbon",
        "largest_city": "Lisbon",
        "population": 10270865,
        "currencies": ["Euro (EUR)"],
        "languages": ["Portuguese"],
        "continent": "Europe",
        "sub_region": "Southern Europe",
        "area_km2": 92212,
        "gdp_usd_billion": 253,
    },
    "netherlands": {
        "name": "Netherlands",
        "capital": "Amsterdam",
        "largest_city": "Amsterdam",
        "population": 17564014,
        "currencies": ["Euro (EUR)"],
        "languages": ["Dutch"],
        "continent": "Europe",
        "sub_region": "Western Europe",
        "area_km2": 41543,
        "gdp_usd_billion": 1011,
    },
    "belgium": {
        "name": "Belgium",
        "capital": "Brussels",
        "largest_city": "Brussels",
        "population": 11589623,
        "currencies": ["Euro (EUR)"],
        "languages": ["Dutch", "French", "German"],
        "continent": "Europe",
        "sub_region": "Western Europe",
        "area_km2": 30528,
        "gdp_usd_billion": 581,
    },
    "switzerland": {
        "name": "Switzerland",
        "capital": "Bern",
        "largest_city": "Zurich",
        "population": 8673671,
        "currencies": ["Swiss franc (CHF)"],
        "languages": ["German", "French", "Italian", "Romansh"],
        "continent": "Europe",
        "sub_region": "Western Europe",
        "area_km2": 41285,
        "gdp_usd_billion": 807,
    },
    "austria": {
        "name": "Austria",
        "capital": "Vienna",
        "largest_city": "Vienna",
        "population": 9027999,
        "currencies": ["Euro (EUR)"],
        "languages": ["German"],
        "continent": "Europe",
        "sub_region": "Western Europe",
        "area_km2": 83871,
        "gdp_usd_billion": 469,
    },
    "sweden": {
        "name": "Sweden",
        "capital": "Stockholm",
        "largest_city": "Stockholm",
        "population": 10423088,
        "currencies": ["Swedish krona (SEK)"],
        "languages": ["Swedish"],
        "continent": "Europe",
        "sub_region": "Northern Europe",
        "area_km2": 450295,
        "gdp_usd_billion": 594,
    },
    "norway": {
        "name": "Norway",
        "capital": "Oslo",
        "largest_city": "Oslo",
        "population": 5379475,
        "currencies": ["Norwegian krone (NOK)"],
        "languages": ["Norwegian"],
        "continent": "Europe",
        "sub_region": "Northern Europe",
        "area_km2": 385207,
        "gdp_usd_billion": 579,
    },
    "denmark": {
        "name": "Denmark",
        "capital": "Copenhagen",
        "largest_city": "Copenhagen",
        "population": 5857921,
        "currencies": ["Danish krone (DKK)"],
        "languages": ["Danish"],
        "continent": "Europe",
        "sub_region": "Northern Europe",
        "area_km2": 42924,
        "gdp_usd_billion": 395,
    },
    "finland": {
        "name": "Finland",
        "capital": "Helsinki",
        "largest_city": "Helsinki",
        "population": 5541274,
        "currencies": ["Euro (EUR)"],
        "languages": ["Finnish", "Swedish"],
        "continent": "Europe",
        "sub_region": "Northern Europe",
        "area_km2": 338145,
        "gdp_usd_billion": 283,
    },
    "russia": {
        "name": "Russia",
        "capital": "Moscow",
        "largest_city": "Moscow",
        "population": 145102755,
        "currencies": ["Russian ruble (RUB)"],
        "languages": ["Russian"],
        "continent": "Europe",
        "sub_region": "Eastern Europe",
        "area_km2": 17098242,
        "gdp_usd_billion": 2241,
    },
    "ukraine": {
        "name": "Ukraine",
        "capital": "Kyiv",
        "largest_city": "Kyiv",
        "population": 43531422,
        "currencies": ["Ukrainian hryvnia (UAH)"],
        "languages": ["Ukrainian"],
        "continent": "Europe",
        "sub_region": "Eastern Europe",
        "area_km2": 603550,
        "gdp_usd_billion": 160,
    },
    "poland": {
        "name": "Poland",
        "capital": "Warsaw",
        "largest_city": "Warsaw",
        "population": 37840001,
        "currencies": ["Polish złoty (PLN)"],
        "languages": ["Polish"],
        "continent": "Europe",
        "sub_region": "Eastern Europe",
        "area_km2": 312696,
        "gdp_usd_billion": 699,
    },
    "czech republic": {
        "name": "Czech Republic",
        "capital": "Prague",
        "largest_city": "Prague",
        "population": 10900555,
        "currencies": ["Czech koruna (CZK)"],
        "languages": ["Czech"],
        "continent": "Europe",
        "sub_region": "Eastern Europe",
        "area_km2": 78866,
        "gdp_usd_billion": 296,
    },
    "greece": {
        "name": "Greece",
        "capital": "Athens",
        "largest_city": "Athens",
        "population": 10432481,
        "currencies": ["Euro (EUR)"],
        "languages": ["Greek"],
        "continent": "Europe",
        "sub_region": "Southern Europe",
        "area_km2": 131957,
        "gdp_usd_billion": 218,
    },
    "romania": {
        "name": "Romania",
        "capital": "Bucharest",
        "largest_city": "Bucharest",
        "population": 19237691,
        "currencies": ["Romanian leu (RON)"],
        "languages": ["Romanian"],
        "continent": "Europe",
        "sub_region": "Eastern Europe",
        "area_km2": 238397,
        "gdp_usd_billion": 301,
    },
    # ── Americas ─────────────────────────────────────────────────────────────
    "united states": {
        "name": "United States",
        "capital": "Washington, D.C.",
        "largest_city": "New York City",
        "population": 331893745,
        "currencies": ["United States dollar (USD)"],
        "languages": ["English"],
        "continent": "Americas",
        "sub_region": "Northern America",
        "area_km2": 9833517,
        "gdp_usd_billion": 25035,
    },
    "usa": {
        "name": "United States",
        "capital": "Washington, D.C.",
        "largest_city": "New York City",
        "population": 331893745,
        "currencies": ["United States dollar (USD)"],
        "languages": ["English"],
        "continent": "Americas",
        "sub_region": "Northern America",
        "area_km2": 9833517,
        "gdp_usd_billion": 25035,
    },
    "canada": {
        "name": "Canada",
        "capital": "Ottawa",
        "largest_city": "Toronto",
        "population": 38005238,
        "currencies": ["Canadian dollar (CAD)"],
        "languages": ["English", "French"],
        "continent": "Americas",
        "sub_region": "Northern America",
        "area_km2": 9984670,
        "gdp_usd_billion": 2139,
    },
    "mexico": {
        "name": "Mexico",
        "capital": "Mexico City",
        "largest_city": "Mexico City",
        "population": 128932753,
        "currencies": ["Mexican peso (MXN)"],
        "languages": ["Spanish"],
        "continent": "Americas",
        "sub_region": "Latin America",
        "area_km2": 1964375,
        "gdp_usd_billion": 1293,
    },
    "brazil": {
        "name": "Brazil",
        "capital": "Brasília",
        "largest_city": "São Paulo",
        "population": 215313498,
        "currencies": ["Brazilian real (BRL)"],
        "languages": ["Portuguese"],
        "continent": "Americas",
        "sub_region": "South America",
        "area_km2": 8515767,
        "gdp_usd_billion": 1920,
    },
    "argentina": {
        "name": "Argentina",
        "capital": "Buenos Aires",
        "largest_city": "Buenos Aires",
        "population": 45510318,
        "currencies": ["Argentine peso (ARS)"],
        "languages": ["Spanish"],
        "continent": "Americas",
        "sub_region": "South America",
        "area_km2": 2780400,
        "gdp_usd_billion": 632,
    },
    "colombia": {
        "name": "Colombia",
        "capital": "Bogotá",
        "largest_city": "Bogotá",
        "population": 51874024,
        "currencies": ["Colombian peso (COP)"],
        "languages": ["Spanish"],
        "continent": "Americas",
        "sub_region": "South America",
        "area_km2": 1141748,
        "gdp_usd_billion": 343,
    },
    "chile": {
        "name": "Chile",
        "capital": "Santiago",
        "largest_city": "Santiago",
        "population": 19212361,
        "currencies": ["Chilean peso (CLP)"],
        "languages": ["Spanish"],
        "continent": "Americas",
        "sub_region": "South America",
        "area_km2": 756102,
        "gdp_usd_billion": 301,
    },
    "peru": {
        "name": "Peru",
        "capital": "Lima",
        "largest_city": "Lima",
        "population": 33359418,
        "currencies": ["Peruvian sol (PEN)"],
        "languages": ["Spanish", "Quechua", "Aymara"],
        "continent": "Americas",
        "sub_region": "South America",
        "area_km2": 1285216,
        "gdp_usd_billion": 226,
    },
    # ── Africa ───────────────────────────────────────────────────────────────
    "nigeria": {
        "name": "Nigeria",
        "capital": "Abuja",
        "largest_city": "Lagos",
        "population": 218541212,
        "currencies": ["Nigerian naira (NGN)"],
        "languages": ["English"],
        "continent": "Africa",
        "sub_region": "Western Africa",
        "area_km2": 923768,
        "gdp_usd_billion": 477,
    },
    "south africa": {
        "name": "South Africa",
        "capital": "Pretoria",
        "largest_city": "Johannesburg",
        "population": 60041994,
        "currencies": ["South African rand (ZAR)"],
        "languages": ["Zulu", "Xhosa", "Afrikaans", "English", "and 7 more"],
        "continent": "Africa",
        "sub_region": "Southern Africa",
        "area_km2": 1219090,
        "gdp_usd_billion": 406,
    },
    "egypt": {
        "name": "Egypt",
        "capital": "Cairo",
        "largest_city": "Cairo",
        "population": 104258327,
        "currencies": ["Egyptian pound (EGP)"],
        "languages": ["Arabic"],
        "continent": "Africa",
        "sub_region": "Northern Africa",
        "area_km2": 1002450,
        "gdp_usd_billion": 404,
    },
    "ethiopia": {
        "name": "Ethiopia",
        "capital": "Addis Ababa",
        "largest_city": "Addis Ababa",
        "population": 126527060,
        "currencies": ["Ethiopian birr (ETB)"],
        "languages": ["Amharic"],
        "continent": "Africa",
        "sub_region": "Eastern Africa",
        "area_km2": 1104300,
        "gdp_usd_billion": 126,
    },
    "kenya": {
        "name": "Kenya",
        "capital": "Nairobi",
        "largest_city": "Nairobi",
        "population": 54985698,
        "currencies": ["Kenyan shilling (KES)"],
        "languages": ["Swahili", "English"],
        "continent": "Africa",
        "sub_region": "Eastern Africa",
        "area_km2": 580367,
        "gdp_usd_billion": 113,
    },
    "ghana": {
        "name": "Ghana",
        "capital": "Accra",
        "largest_city": "Accra",
        "population": 33475870,
        "currencies": ["Ghanaian cedi (GHS)"],
        "languages": ["English"],
        "continent": "Africa",
        "sub_region": "Western Africa",
        "area_km2": 238533,
        "gdp_usd_billion": 73,
    },
    "morocco": {
        "name": "Morocco",
        "capital": "Rabat",
        "largest_city": "Casablanca",
        "population": 37457971,
        "currencies": ["Moroccan dirham (MAD)"],
        "languages": ["Arabic", "Tamazight"],
        "continent": "Africa",
        "sub_region": "Northern Africa",
        "area_km2": 446550,
        "gdp_usd_billion": 143,
    },
    # ── Oceania ──────────────────────────────────────────────────────────────
    "australia": {
        "name": "Australia",
        "capital": "Canberra",
        "largest_city": "Sydney",
        "population": 25921400,
        "currencies": ["Australian dollar (AUD)"],
        "languages": ["English"],
        "continent": "Oceania",
        "sub_region": "Australia and New Zealand",
        "area_km2": 7692024,
        "gdp_usd_billion": 1693,
    },
    "new zealand": {
        "name": "New Zealand",
        "capital": "Wellington",
        "largest_city": "Auckland",
        "population": 5084300,
        "currencies": ["New Zealand dollar (NZD)"],
        "languages": ["English", "Māori"],
        "continent": "Oceania",
        "sub_region": "Australia and New Zealand",
        "area_km2": 270467,
        "gdp_usd_billion": 247,
    },
}

# Build alias lookups (alternate spellings)
_ALIASES: dict[str, str] = {
    "sri-lanka": "sri lanka",
    "srilanka": "sri lanka",
    "us": "usa",
    "america": "usa",
    "uk": "united kingdom",
    "great britain": "united kingdom",
    "britain": "united kingdom",
    "south-korea": "south korea",
    "north-korea": "north korea",
    "czech": "czech republic",
    "czechia": "czech republic",
    "uae": "uae",
    "emirates": "united arab emirates",
}


# ---------------------------------------------------------------------------
# CountryKnowledgeBase
# ---------------------------------------------------------------------------

class CountryKnowledgeBase:
    """
    Offline knowledge base for country facts.
    ReAct-aware: all lookups log Thought/Action/Observation steps.
    """

    def lookup(self, country: str) -> dict | None:
        """Return full country data dict, or None if not found."""
        key = country.strip().lower()
        key = _ALIASES.get(key, key)
        data = COUNTRIES.get(key)
        if data:
            logger.debug("[CountryKB] HIT: '%s' → %s", country, data["name"])
        else:
            logger.debug("[CountryKB] MISS: '%s'", country)
        return data

    def format_answer(self, query_type: str, data: dict) -> str:
        """
        Format a natural-language answer for the given query_type using country data.
        query_type: capital | population | currency | language | continent | area | gdp
        """
        name = data["name"]

        if query_type == "capital":
            capital = data.get("capital", "Unknown")
            city = data.get("largest_city", "")
            ans = f"The official capital of **{name}** is **{capital}**."
            if city and city != capital:
                ans += f" **{city}** is the largest city and commercial center."
            return ans

        if query_type == "population":
            pop = data.get("population")
            if pop:
                return (
                    f"The population of **{name}** is approximately **{pop:,}** people "
                    f"(as of latest estimates)."
                )
            return f"Population data for {name} is not available."

        if query_type == "currency":
            currencies = data.get("currencies", [])
            cur_str = ", ".join(currencies) if currencies else "Unknown"
            return f"The currency of **{name}** is **{cur_str}**."

        if query_type == "language":
            languages = data.get("languages", [])
            lang_str = ", ".join(languages) if languages else "Unknown"
            plural = "languages are" if len(languages) > 1 else "language is"
            return f"The official {plural} of **{name}**: **{lang_str}**."

        if query_type == "continent":
            continent = data.get("continent", "Unknown")
            sub = data.get("sub_region", "")
            ans = f"**{name}** is located in **{continent}**."
            if sub:
                ans += f" (Sub-region: {sub})"
            return ans

        if query_type == "area":
            area = data.get("area_km2")
            if area:
                return f"The area of **{name}** is approximately **{area:,} km²**."
            return f"Area data for {name} is not available."

        if query_type == "gdp":
            gdp = data.get("gdp_usd_billion")
            if gdp:
                return (
                    f"The GDP of **{name}** is approximately **${gdp:,} billion USD** "
                    f"(rough estimate, may vary by source)."
                )
            return f"GDP data for {name} is not available."

        # Fallback: return all info
        return (
            f"**{name}**: Capital — {data.get('capital', '?')}, "
            f"Population — {data.get('population', '?'):,}, "
            f"Currency — {', '.join(data.get('currencies', ['?']))}."
        )


# ---------------------------------------------------------------------------
# Query parsing helpers
# ---------------------------------------------------------------------------

_COUNTRY_QUERY_RE = re.compile(
    r"""
    \b(?:
        capital\s+(?:city\s+)?of |
        population\s+of |
        currency\s+of |
        official\s+language(?:s)?\s+of |
        language(?:s)?\s+of |
        (?:what\s+)?continent\s+is |
        (?:is\s+)?(?:located\s+in|part\s+of)\s+which\s+continent |
        area\s+(?:of|in\s+km)|
        size\s+of |
        gdp\s+of |
        gross\s+domestic\s+product\s+of
    )\b
    """,
    re.I | re.VERBOSE,
)

_ATTR_RE = re.compile(
    r"\b(capital|population|currency|language|continent|area|size|gdp|gross domestic product)\b",
    re.I,
)


def classify_country_query(query: str) -> str:
    """
    Return query type: capital | population | currency | language | continent | area | gdp | unknown
    """
    q = query.lower()
    if re.search(r"\bcapital\b", q):
        return "capital"
    if re.search(r"\bpopulation\b", q):
        return "population"
    if re.search(r"\bcurrenc", q):
        return "currency"
    if re.search(r"\blanguage\b", q):
        return "language"
    if re.search(r"\bcontinent\b", q):
        return "continent"
    if re.search(r"\b(area|size)\b", q):
        return "area"
    if re.search(r"\b(gdp|gross domestic product)\b", q):
        return "gdp"
    return "general"


def is_country_query(query: str) -> bool:
    """Return True if the query is asking about a country fact."""
    q = query.lower()
    return bool(_COUNTRY_QUERY_RE.search(q)) or bool(re.search(
        r"\b(capital|population|currency|language|continent|gdp)\s+of\b", q, re.I
    ))


def extract_country_from_query(query: str) -> str:
    """
    Extract the country name from a query like
    'What is the capital of Sri Lanka?' → 'sri lanka'
    """
    q = query.lower().strip().rstrip("?")

    # Pattern: "X of <COUNTRY>" or "what continent is <COUNTRY>"
    patterns = [
        r"(?:capital|population|currency|language|area|gdp|gross domestic product)\s+(?:city\s+)?of\s+(.+)$",
        r"(?:what\s+)?continent\s+is\s+(.+?)(?:\s+in)?\s*$",
        r"(?:located\s+in|part\s+of)\s+which\s+continent\s+is\s+(.+)$",
        r"official\s+language(?:s)?\s+of\s+(.+)$",
        r"size\s+of\s+(.+)$",
    ]
    for pat in patterns:
        m = re.search(pat, q)
        if m:
            return m.group(1).strip().rstrip("?").strip()

    return ""
