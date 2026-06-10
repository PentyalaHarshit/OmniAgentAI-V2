"""
tools/real_hotel_provider.py
=============================
Real Hotel Provider Tool — calls SerpApi Google Hotels API.

Configuration (.env)
--------------------
  HOTEL_PROVIDER=serpapi        # "serpapi" or "demo"
  SERPAPI_API_KEY=your_key      # get free key at https://serpapi.com

If no key is configured, returns a clear error message instead of
silently returning mock data.

Usage
-----
    provider = RealHotelProvider()
    result = provider.search_hotels(
        city="Paris",
        check_in="2025-08-01",
        check_out="2025-08-05",
        guests=2,
        budget=200
    )
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)


class RealHotelProvider:

    def __init__(self):
        self.provider    = os.getenv("HOTEL_PROVIDER", "demo").lower()
        self.serpapi_key = os.getenv("SERPAPI_API_KEY", "").strip()

    # ── Public API ────────────────────────────────────────────────────────

    def search_hotels(
        self,
        city: str,
        check_in: str,
        check_out: str,
        guests: int = 1,
        budget: float | None = None,
    ) -> dict:
        """
        Search hotels for the given parameters.

        Returns
        -------
        {
            "available": bool,
            "provider":  str,
            "hotels":    list[dict],   # sorted by price
            "error":     str | None,
        }
        """
        city     = (city or "").strip()
        check_in  = (check_in  or "").strip()
        check_out = (check_out or "").strip()

        if not city:
            return self._error("City is required to search hotels.")

        if self.provider == "serpapi" and self.serpapi_key:
            return self._search_serpapi(city, check_in, check_out, guests, budget)

        if self.provider == "serpapi" and not self.serpapi_key:
            return self._error(
                "SERPAPI_API_KEY is not set in .env. "
                "Get a free key at https://serpapi.com and add it to your .env file."
            )

        return self._error(
            f"Hotel provider '{self.provider}' is not supported. "
            "Set HOTEL_PROVIDER=serpapi and add SERPAPI_API_KEY in .env."
        )

    def is_configured(self) -> bool:
        return self.provider == "serpapi" and bool(self.serpapi_key)

    # ── SerpApi implementation ─────────────────────────────────────────────

    def _search_serpapi(
        self,
        city: str,
        check_in: str,
        check_out: str,
        guests: int,
        budget: float | None,
    ) -> dict:
        params = {
            "engine":          "google_hotels",
            "q":               city,
            "check_in_date":   check_in,
            "check_out_date":  check_out,
            "adults":          str(guests),
            "currency":        "USD",
            "gl":              "us",
            "hl":              "en",
            "api_key":         self.serpapi_key,
        }
        if budget:
            params["max_price"] = str(int(budget))

        try:
            resp = requests.get(
                "https://serpapi.com/search.json",
                params=params,
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.warning("SerpApi request failed: %s", e)
            return self._error(f"Hotel API request failed: {e}")
        except Exception as e:
            logger.warning("SerpApi parse error: %s", e)
            return self._error(f"Hotel API response error: {e}")

        properties = data.get("properties", [])
        hotels = []

        for item in properties[:10]:
            rate  = item.get("rate_per_night", {})
            price = rate.get("lowest") or rate.get("before_taxes_fees") or "N/A"

            hotel = {
                "name":      item.get("name", "Unknown Hotel"),
                "price":     price,
                "rating":    item.get("overall_rating", "N/A"),
                "reviews":   item.get("reviews", "N/A"),
                "address":   item.get("address", "Address unavailable"),
                "link":      item.get("link", ""),
                "amenities": item.get("amenities", [])[:6],
                "source":    "Google Hotels via SerpApi",
            }
            hotels.append(hotel)

        # Sort by price (parse numeric value, put "N/A" last)
        def _price_key(h):
            p = str(h.get("price", "")).replace("$", "").replace(",", "").strip()
            try:
                return float(p)
            except ValueError:
                return float("inf")

        hotels.sort(key=_price_key)

        return {
            "available": bool(hotels),
            "provider":  "SerpApi Google Hotels",
            "hotels":    hotels,
            "error":     None,
            "raw_count": len(properties),
        }

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _error(msg: str) -> dict:
        return {
            "available": False,
            "provider":  "none",
            "hotels":    [],
            "error":     msg,
        }
