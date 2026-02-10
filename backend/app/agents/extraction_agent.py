"""Extraction agent for extracting investment data from PDF documents."""

import json
import re
from typing import Any, Dict, List, Optional

from google import genai

from app.agents.base import BaseAgent, AgentResult
from app.config import get_settings


# Field definitions with formatting instructions
FIELDS_FORMATS = {
    "Investment": "No specific format",
    "Firm": "No specific format",
    "Strategy Description": "Return as bullet points, one key point per line. Start each line with '• '. Example:\n• Focus on mid-cap growth equities\n• Long/short strategy with 60% net exposure\n• Target companies with strong cash flow",
    "Leaders/PM/CEO": """Extract ALL information about each leader/executive mentioned in the document.
For each person, include as much detail as possible:
- Full name
- Current title/role at this firm
- Previous titles/roles and companies
- Education (universities, degrees)
- Years of experience
- Any other biographical details mentioned
Return as a JSON array of objects with these keys:
- 'name': Full name
- 'title': Current title/role
- 'company': Current company/firm
- 'previous_roles': Array of previous positions (e.g., ["CEO at XYZ Corp", "VP at ABC Inc"])
- 'education': Array of education (e.g., ["MBA Harvard", "BS MIT"])
- 'background': Any other relevant background info as a string
Example: [{"name": "John Smith", "title": "CEO", "company": "Acme Capital", "previous_roles": ["Partner at BigFund LP"], "education": ["MBA Wharton"], "background": "20 years in private equity"}]""",
    "Management Fees": "No specific format",
    "Incentive Fees": "Format as 'x% Pref | x% incentive fee', e.g., '8% Pref | 20% incentive fee'",
    "Liquidity/Lock": "No specific format",
    "Target Net Returns": "Format as percentage or range, e.g., '10-12%'",
}

EXTRACTION_PROMPT = f"""
You are analyzing an investment pitch deck.

Extract the following fields from the document.
If a field is not present or unclear, return null.

Fields and formatting instructions:
{chr(10).join(f"- {field}: {fmt}" for field, fmt in FIELDS_FORMATS.items())}

Return valid JSON only. Do not include any other text or explanation.
"""

# Mapping from API field names to database column names
FIELD_MAPPING = {
    "Investment": "investment_name",
    "Firm": "firm",
    "Strategy Description": "strategy_description",
    "Leaders/PM/CEO": "leaders_json",
    "Management Fees": "management_fees",
    "Incentive Fees": "incentive_fees",
    "Liquidity/Lock": "liquidity_lock",
    "Target Net Returns": "target_net_returns",
}


class ExtractionAgent(BaseAgent):
    """Extracts structured investment data from PDF markdown content.

    Uses Gemini to analyze the document and extract key investment fields
    like firm name, strategy, fees, leaders, etc.
    """

    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.google_api_key)

    @property
    def name(self) -> str:
        return "Extraction"

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON object from response text."""
        text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE)
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("No JSON object found in response")
        return json.loads(match.group(0))

    def _map_fields(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map extracted field names to database column names."""
        mapped = {}
        for api_field, db_field in FIELD_MAPPING.items():
            value = raw_data.get(api_field)
            if value is None:
                mapped[db_field] = None
            elif db_field == "leaders_json":
                # Keep the full leader data for LinkedIn lookup
                if isinstance(value, list):
                    mapped[db_field] = value
                elif isinstance(value, str):
                    # Fallback: Gemini returned string, parse as pipe-separated
                    mapped[db_field] = [
                        {"name": name.strip()}
                        for name in value.split("|") if name.strip()
                    ]
                else:
                    mapped[db_field] = None
            elif db_field == "strategy_description":
                # Join array of bullet points into newline-separated string
                if isinstance(value, list):
                    mapped[db_field] = "\n".join(str(item) for item in value)
                else:
                    mapped[db_field] = str(value)
            else:
                mapped[db_field] = str(value)
        return mapped

    async def run(self, markdown_content: str) -> AgentResult:
        """Extract investment data from markdown content.

        Args:
            markdown_content: The markdown text from a converted PDF

        Returns:
            AgentResult with:
                - mapped_fields: Dict with database column names
                - raw_data: Original extraction response
                - leaders_raw: Raw leader data for LinkedIn lookup
                - firm_name: Firm name for LinkedIn context
        """
        try:
            self.log("Extracting investment data...")

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=EXTRACTION_PROMPT + "\n\nDOCUMENT:\n" + markdown_content,
            )

            raw_data = self._extract_json(response.text)
            leaders_raw = raw_data.get("Leaders/PM/CEO", [])
            firm_name = raw_data.get("Firm")

            leader_count = len(leaders_raw) if isinstance(leaders_raw, list) else 0
            self.log(f"Found {leader_count} leaders")

            # Log the raw leader data
            if isinstance(leaders_raw, list):
                for i, leader in enumerate(leaders_raw[:5]):
                    self.log(f"  Leader {i+1}: {leader.get('name', 'Unknown')}")

            mapped_fields = self._map_fields(raw_data)

            return AgentResult.ok(
                data={
                    "mapped_fields": mapped_fields,
                    "raw_data": raw_data,
                    "leaders_raw": leaders_raw if isinstance(leaders_raw, list) else [],
                    "firm_name": firm_name,
                },
                leader_count=leader_count,
            )

        except Exception as e:
            self.log(f"Error: {e}")
            return AgentResult.fail(str(e))
