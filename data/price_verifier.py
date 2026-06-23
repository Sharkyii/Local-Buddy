"""
PriceVerifier — looks up a hotel's current price via free web search, then asks
the LLM to read off a single number from the noisy results.

Distinct from agents/travel_agent.py's check_live_price tool: that one surfaces a
live result mid-conversation and never persists it. This one is meant to be run by
DataIngestionPipeline.verify_hotel_prices, which writes the extracted price back
onto the Hotel node in Neo4j (timestamped, since it can go stale).

Extraction prompt is deliberately a single plain-text instruction, not structured
JSON with multi-step reasoning — tested against this project's small local model
(qwen2.5:3b, see agents/base_agent.py): the elaborate version reliably failed even
when a clear price sat right in the text, while "just tell me the number" worked.
Smaller models follow one direct instruction far more reliably than several
conditional ones bundled together.
"""

import logging
import re
from typing import Any, Dict

import litellm
from ddgs import DDGS

from agents.base_agent import _select_model

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Based on this text, what is the per-night room price in Indian \
Rupees (INR) for "{hotel_name}"? Ignore any price in $ or other currencies, and ignore \
multi-night totals or add-on fees (like extra beds or breakfast). Reply with ONLY the \
number (no currency symbol, no commas, no other text). If no clear INR per-night price \
is mentioned, reply with exactly: none

{snippets}
"""

_NUMBER_RE = re.compile(r"\d[\d,]*")


class PriceVerifier:
    def __init__(self):
        self.model = _select_model()

    def verify_hotel_price(self, hotel_name: str, city_name: str) -> Dict[str, Any]:
        """Search the web for this hotel's current price and extract a number.
        Always returns a dict (price=None on any failure/no-match) — callers
        don't need to handle exceptions."""
        empty = {"price": None, "currency": "INR", "confidence": "low"}
        # Avoid a doubled city name in the query when it's already part of hotel_name
        # (e.g. "Hyatt Regency Ahmedabad" + "Ahmedabad, India") — noisier ranking otherwise.
        query = hotel_name if city_name.split(",")[0] in hotel_name else f"{hotel_name} {city_name}"
        try:
            hits = DDGS().text(f"{query} price per night INR", max_results=4)
        except Exception as error:
            logger.warning(f"  ⚠️  Search failed for {hotel_name}: {error}")
            return empty
        if not hits:
            return empty

        snippets = "\n".join(f"- {h.get('title', '')}: {h.get('body', '')}" for h in hits)
        prompt = EXTRACTION_PROMPT.format(hotel_name=hotel_name, snippets=snippets)
        try:
            response = litellm.completion(
                model=self.model, max_tokens=30,
                messages=[{"role": "user", "content": prompt}],
            )
            reply = response.choices[0].message.content.strip().lower()
            if "none" in reply:
                return empty
            match = _NUMBER_RE.search(reply)
            if not match:
                return empty
            price = int(match.group().replace(",", ""))
            return {"price": price, "currency": "INR", "confidence": "medium"}
        except Exception as error:
            logger.warning(f"  ⚠️  Price extraction failed for {hotel_name}: {error}")
            return empty
