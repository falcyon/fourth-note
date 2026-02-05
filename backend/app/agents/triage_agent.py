"""Triage agent for classifying emails as investment-related or not."""

import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import List

from google import genai

from app.agents.base import BaseAgent, AgentResult
from app.config import get_settings


class TriageClassification(str, Enum):
    """Classification result for email triage."""

    YES = "YES"  # Clearly investment-related
    NO = "NO"  # Clearly NOT investment-related
    UNSURE = "UNSURE"  # Needs further analysis


@dataclass
class TriageInput:
    """Input data for triage agent."""

    subject: str
    sender: str
    attachment_names: List[str]
    body_text: str = ""  # Plain text email body (truncated)


TRIAGE_PROMPT = """You are classifying emails to determine if they contain investment pitch decks or investor materials.

Email subject: {subject}
Sender: {sender}
Attachment names: {attachments}
Email body (excerpt):
{body_excerpt}

Classify as:
- YES: Clearly an investment pitch deck, fund update, quarterly report, investor materials, or LP update
- NO: Clearly NOT investment-related (newsletters, receipts, personal emails, marketing, software notifications)
- UNSURE: Could be investment-related but not certain, needs further analysis of the actual document

Keywords that suggest YES:
- "investor update", "fund update", "quarterly report", "pitch deck", "LP update"
- "capital call", "distribution notice", "portfolio update"
- Fund names, investment firm names
- References to AUM, IRR, returns, commitments

Keywords that suggest NO:
- "order confirmation", "shipping notification", "receipt"
- "newsletter", "unsubscribe", "marketing"
- "password reset", "verify your email"

Return ONLY valid JSON with no additional text:
{{"classification": "YES|NO|UNSURE", "reason": "brief explanation"}}
"""


class TriageAgent(BaseAgent):
    """Determines if an email contains investment-related content.

    Uses Gemini Flash for fast, cheap classification based on email metadata.
    No PDF parsing needed - just looks at subject, sender, and attachment names.
    """

    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.google_api_key)

    @property
    def name(self) -> str:
        return "Triage"

    async def run(self, input_data: TriageInput) -> AgentResult:
        """Classify an email as investment-related or not.

        Args:
            input_data: TriageInput with subject, sender, attachment_names

        Returns:
            AgentResult with classification (YES/NO/UNSURE) and reason
        """
        try:
            # Format the prompt
            attachments_str = ", ".join(input_data.attachment_names) if input_data.attachment_names else "None"
            # Truncate body to first 1000 chars for the prompt
            body_excerpt = (input_data.body_text or "")[:1000]
            if not body_excerpt:
                body_excerpt = "(no body text)"

            prompt = TRIAGE_PROMPT.format(
                subject=input_data.subject or "(no subject)",
                sender=input_data.sender or "(unknown sender)",
                attachments=attachments_str,
                body_excerpt=body_excerpt,
            )

            self.log(f"Classifying: {input_data.subject[:50]}...")

            # Call Gemini Flash (fast and cheap)
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )

            # Parse the JSON response
            text = response.text.strip()
            # Remove markdown code blocks if present
            text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()

            result = json.loads(text)
            classification = TriageClassification(result.get("classification", "UNSURE"))
            reason = result.get("reason", "")

            self.log(f"Result: {classification.value} - {reason}")

            return AgentResult.ok(
                data={
                    "classification": classification,
                    "reason": reason,
                },
                subject=input_data.subject,
            )

        except json.JSONDecodeError as e:
            self.log(f"Failed to parse response: {e}")
            # Default to UNSURE if we can't parse
            return AgentResult.ok(
                data={
                    "classification": TriageClassification.UNSURE,
                    "reason": "Failed to parse classification response",
                }
            )
        except Exception as e:
            self.log(f"Error: {e}")
            return AgentResult.fail(str(e))
