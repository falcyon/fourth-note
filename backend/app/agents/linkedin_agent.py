"""LinkedIn agent for finding LinkedIn profiles for investment leaders."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.agents.base import BaseAgent, AgentResult
from app.config import get_settings


@dataclass
class LinkedInInput:
    """Input data for LinkedIn lookup."""

    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    previous_roles: Optional[List[str]] = None
    education: Optional[List[str]] = None
    background: Optional[str] = None
    firm_name: Optional[str] = None  # Fallback company context

    @classmethod
    def from_leader_dict(cls, leader: Dict[str, Any], firm_name: str = None) -> "LinkedInInput":
        """Create from a leader dictionary extracted by Gemini."""
        return cls(
            name=leader.get("name", "Unknown"),
            title=leader.get("title"),
            company=leader.get("company"),
            previous_roles=leader.get("previous_roles"),
            education=leader.get("education"),
            background=leader.get("background"),
            firm_name=firm_name,
        )


class LinkedInAgent(BaseAgent):
    """Finds LinkedIn profile URL for a single person.

    Uses Perplexity API with online search to look up the actual LinkedIn profile.
    Can run in parallel for multiple leaders.
    """

    def __init__(self):
        settings = get_settings()
        # Use Perplexity API (OpenAI-compatible endpoint)
        if settings.perplexity_api_key:
            self.client = OpenAI(
                api_key=settings.perplexity_api_key,
                base_url="https://api.perplexity.ai"
            )
        else:
            self.client = None

    @property
    def name(self) -> str:
        return "LinkedIn"

    def _build_context(self, input_data: LinkedInInput) -> str:
        """Build search context from leader info."""
        parts = [input_data.name]

        if input_data.title:
            parts.append(input_data.title)

        if input_data.company or input_data.firm_name:
            parts.append(f"at {input_data.company or input_data.firm_name}")

        if input_data.previous_roles:
            for role in input_data.previous_roles[:3]:
                parts.append(role)

        if input_data.education:
            for edu in input_data.education[:2]:
                parts.append(edu)

        if input_data.background:
            parts.append(input_data.background[:150])

        return "\n".join(parts)

    async def run(self, input_data: LinkedInInput) -> AgentResult:
        """Look up LinkedIn profile for a person.

        Args:
            input_data: LinkedInInput with name and contextual info

        Returns:
            AgentResult with name and linkedin_url (or None if not found)
        """
        name = input_data.name

        if not self.client:
            self.log(f"{name}: Perplexity client not configured, skipping")
            return AgentResult.ok(
                data={"name": name, "linkedin_url": None},
                reason="Perplexity not configured",
            )

        try:
            context = self._build_context(input_data)
            self.log(f"Searching: {context[:80]}...")

            # Use Perplexity with online search model
            response = self.client.chat.completions.create(
                model="sonar",  # Perplexity's online search model
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that finds LinkedIn profile URLs. Always respond with just the LinkedIn URL if found, or say 'Not found' if you cannot find it. Do not explain or add extra text."
                    },
                    {
                        "role": "user",
                        "content": f"Find the LinkedIn profile URL for this person:\n\n{context}"
                    }
                ],
            )

            # Get the response text
            text = response.choices[0].message.content if response.choices else None
            self.log(f"{name}: response={text[:200] if text else 'None'}...")

            if not text:
                return AgentResult.ok(
                    data={"name": name, "linkedin_url": None},
                    reason="Empty response",
                )

            # Extract LinkedIn URL from response
            url_match = re.search(r'https?://[^\s]*linkedin\.com/in/[^\s\)\"\'\]\>\`]+', text)
            if url_match:
                linkedin_url = url_match.group(0).rstrip(".,;:")
                # Clean up URL-encoded special chars at the end (like %60 = backtick)
                linkedin_url = re.sub(r'%[0-9A-Fa-f]{2}$', '', linkedin_url)
                # Remove any trailing punctuation that might have been URL-encoded
                linkedin_url = linkedin_url.rstrip(".,;:)")
                self.log(f"{name}: FOUND {linkedin_url}")
                return AgentResult.ok(
                    data={"name": name, "linkedin_url": linkedin_url},
                )

            self.log(f"{name}: no LinkedIn URL in response")
            return AgentResult.ok(
                data={"name": name, "linkedin_url": None},
                reason="No URL in response",
            )

        except Exception as e:
            self.log(f"{name}: error - {e}")
            return AgentResult.fail(
                error=str(e),
                name=name,
            )
