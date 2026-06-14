"""
agents/country_agent.py
========================
Dedicated Country Agent — answers all country-fact queries.

Supported query types
---------------------
  capital    – What is the capital of Sri Lanka?
  population – What is the population of China?
  currency   – What is the currency of India?
  language   – What is the official language of France?
  continent  – What continent is Brazil in?
  area       – What is the area of Canada?
  gdp        – What is the GDP of Germany?

ReAct loop (Thought → Action → Observation → Verification → Final)
-------------------------------------------------------------------
  Thought   : Classify query type and extract country entity.
  Action    : Look up country in offline knowledge base.
  Observation: Retrieved capital / population / currency / etc.
  Action    : If KB miss → call RestCountries API.
  Verification: Confirm the specific field is present; not None.
  Final     : Format natural-language answer with source attribution.
"""

import re
import logging
import requests

from tools.country_knowledge_base import (
    CountryKnowledgeBase,
    classify_country_query,
    extract_country_from_query,
    is_country_query,
)

logger = logging.getLogger(__name__)

_RESTCOUNTRIES_URL = "https://restcountries.com/v3.1/name/{}"
_TIMEOUT = 8


class CountryAgent:
    name = "CountryAgent"
    agent_type = "Country"

    def __init__(self):
        self.kb = CountryKnowledgeBase()

    # ── Public API ────────────────────────────────────────────────────────

    def can_handle(self, query: str) -> bool:
        """Return True if this agent can answer the query."""
        return is_country_query(query)

    def run(self, query: str, prefilled_fields: dict | None = None,
            session_id: str = "default") -> dict:
        """
        Full ReAct pipeline for country queries.
        Returns the same response dict shape as BaseAgent.response().
        """
        thoughts: list[str] = []
        original_query = self._clean(query)

        # ── Thought: Classify ─────────────────────────────────────────────
        query_type = classify_country_query(original_query)
        country_raw = extract_country_from_query(original_query)

        thoughts.append(
            f"Thought: Country query detected. "
            f"Type='{query_type}', Entity='{country_raw}'."
        )

        if not country_raw:
            return self._no_answer(original_query, thoughts,
                                   "Could not extract country name from query.")

        # ── Action: Offline KB ────────────────────────────────────────────
        thoughts.append(
            f"Action: Look up '{country_raw}' in offline Country Knowledge Base."
        )
        kb_data = self.kb.lookup(country_raw)

        if kb_data:
            thoughts.append(
                f"Observation: KB hit → {kb_data['name']} "
                f"| capital={kb_data.get('capital')} "
                f"| population={kb_data.get('population'):,} "
                f"| currencies={kb_data.get('currencies')}"
            )
        else:
            thoughts.append(
                f"Observation: KB miss for '{country_raw}'. "
                "Action: Call RestCountries API."
            )
            kb_data = self._fetch_restcountries(country_raw, thoughts)

        # ── Verification ─────────────────────────────────────────────────
        if not kb_data:
            msg = (
                f"I could not find information about **{country_raw.title()}**. "
                "Please check the country name and try again."
            )
            return self._no_answer(original_query, thoughts, msg)

        field_value = self._get_field(kb_data, query_type)
        thoughts.append(
            f"Verification: Field '{query_type}' → "
            f"{'✓ present' if field_value else '✗ missing'}."
        )

        if not field_value:
            msg = (
                f"I found **{kb_data['name']}** but the **{query_type}** "
                "data is not available."
            )
            return self._no_answer(original_query, thoughts, msg)

        # ── Final Answer ──────────────────────────────────────────────────
        answer = self.kb.format_answer(query_type, kb_data)
        source = kb_data.get("source", "Offline Knowledge Base")
        thoughts.append(f"Final: {answer}")

        verification = {
            "verified": True,
            "confidence": 1.0 if "Built-in" in source else 0.92,
            "reason": f"Answer verified from {source}.",
            "corrected": answer,
            "sources_used": 1,
        }

        return {
            "agent": self.name,
            "query": original_query,
            "thought_count": len(thoughts),
            "thoughts": thoughts,
            "answer": answer,
            "extra": {
                "slot_filling": False,
                "source_stage": f"country_agent:{source.lower().replace(' ', '_')}",
                "verification": verification,
                "country_data": {
                    "name": kb_data.get("name"),
                    "capital": kb_data.get("capital"),
                    "population": kb_data.get("population"),
                    "currencies": kb_data.get("currencies"),
                    "languages": kb_data.get("languages"),
                    "continent": kb_data.get("continent"),
                },
            },
        }

    # ── RestCountries API fallback ────────────────────────────────────────

    def _fetch_restcountries(self, country: str, thoughts: list[str]) -> dict | None:
        """Fetch from RestCountries API and return a normalised data dict."""
        try:
            url = _RESTCOUNTRIES_URL.format(country)
            thoughts.append(f"Action: GET {url}")
            resp = requests.get(url, timeout=_TIMEOUT)
            if resp.status_code != 200:
                thoughts.append(
                    f"Observation: RestCountries returned {resp.status_code}."
                )
                return None

            data = resp.json()
            # Prefer exact name match
            selected = data[0]
            for item in data:
                common = item.get("name", {}).get("common", "").lower()
                official = item.get("name", {}).get("official", "").lower()
                if country.lower() in [common, official]:
                    selected = item
                    break

            currencies_raw = selected.get("currencies", {})
            currency_names = [
                f"{v.get('name', k)} ({k})" for k, v in currencies_raw.items()
            ]
            languages_raw = selected.get("languages", {})
            language_names = list(languages_raw.values())

            result = {
                "name": selected.get("name", {}).get("common", country.title()),
                "capital": (selected.get("capital") or ["Unknown"])[0],
                "largest_city": (selected.get("capital") or ["Unknown"])[0],
                "population": selected.get("population"),
                "currencies": currency_names,
                "languages": language_names,
                "continent": selected.get("continents", ["Unknown"])[0]
                if selected.get("continents") else "Unknown",
                "sub_region": selected.get("subregion", ""),
                "area_km2": selected.get("area"),
                "gdp_usd_billion": None,  # RestCountries doesn't provide GDP
                "source": "RestCountries API",
            }

            thoughts.append(
                f"Observation: RestCountries returned data for "
                f"{result['name']}."
            )
            return result

        except Exception as exc:
            thoughts.append(f"Observation: RestCountries error — {exc}")
            return None

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _clean(query: str) -> str:
        """Strip LLM guidance and file context markers."""
        if "[Free LLM Tree Guidance]" in query:
            query = query.split("[Free LLM Tree Guidance]", 1)[0]
        if "[Uploaded File Context]" in query:
            query = query.split("[Uploaded File Context]", 1)[0]
        return query.strip()

    @staticmethod
    def _get_field(data: dict, query_type: str):
        """Return the relevant field value for verification (falsy = missing)."""
        field_map = {
            "capital": data.get("capital"),
            "population": data.get("population"),
            "currency": data.get("currencies"),
            "language": data.get("languages"),
            "continent": data.get("continent"),
            "area": data.get("area_km2"),
            "gdp": data.get("gdp_usd_billion"),
        }
        return field_map.get(query_type, True)  # unknown types pass verification

    def _no_answer(self, query: str, thoughts: list[str], msg: str) -> dict:
        return {
            "agent": self.name,
            "query": query,
            "thought_count": len(thoughts),
            "thoughts": thoughts,
            "answer": msg,
            "extra": {
                "slot_filling": False,
                "source_stage": "country_agent:not_found",
                "verification": {
                    "verified": False,
                    "confidence": 0.0,
                    "reason": "Country or field not found.",
                    "corrected": "",
                    "sources_used": 0,
                },
            },
        }
