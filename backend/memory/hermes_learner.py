"""
HELIOS Backend — Hermes Memory Learner
Processes chat sessions to extract circadian insights and update
per-user markdown memory files. Uses the user's own LLM key.

The memory file is a structured markdown document that evolves over time
as Hermes learns more about the user's sleep patterns, caffeine habits,
protocol adherence, and communication preferences.
"""

from datetime import datetime
from typing import Optional

from backend.chat.llm_proxy import call_llm


# ─── Hermes System Prompt ────────────────────────────────────────────────────

HERMES_EXTRACT_PROMPT = """You are Hermes, the memory analyst for HELIOS (a circadian intelligence engine).

You are given:
1. A conversation transcript between a user and HELIOS
2. The user's current memory file (may be empty for new users)

Your job: Extract NEW circadian-relevant insights from the conversation and return an UPDATED memory file.

RULES:
- Only add information that is NEW or updates existing entries
- Remove outdated information if the user contradicts it
- Be concise — one line per insight, include specific times/numbers
- Use the exact category structure shown below
- If a category has no updates, keep existing entries unchanged
- If the conversation has nothing worth remembering, return the memory file unchanged
- NEVER fabricate information — only record what the user explicitly said or strongly implied

MEMORY FILE STRUCTURE (return this exact format):

```markdown
# HELIOS User Memory

## Chronotype & Sleep
- [entries about sleep timing, chronotype, sleep quality patterns]

## Caffeine
- [entries about caffeine intake, timing, sensitivity, habits]

## Light Exposure
- [entries about screen habits, outdoor time, work environment]

## Protocol Adherence
- [entries about which HELIOS recommendations they follow/ignore]

## Health & Biometrics
- [entries about HRV, wearable data, health conditions, medications]

## Lifestyle Context
- [entries about travel, work schedule, stress, exercise, timezone]

## Preferences
- [entries about communication style, what advice resonates, what they dislike]

## Last Updated
- [ISO timestamp of this update]
```

Return ONLY the updated markdown file. No explanations, no preamble."""


HERMES_UPDATE_PROMPT = """You are Hermes, the memory analyst for HELIOS.

Here is the user's current memory file:

---
{current_memory}
---

Here is the new conversation transcript:

---
{transcript}
---

Analyze the conversation and return the UPDATED memory file with any new insights incorporated. Keep existing entries that are still valid. Update or remove entries that are contradicted. Add new entries from this conversation.

Return ONLY the updated markdown file."""


# ─── Default Memory Template ────────────────────────────────────────────────

DEFAULT_MEMORY = """# HELIOS User Memory

## Chronotype & Sleep
- No data yet

## Caffeine
- No data yet

## Light Exposure
- No data yet

## Protocol Adherence
- No data yet

## Health & Biometrics
- No data yet

## Lifestyle Context
- No data yet

## Preferences
- No data yet

## Last Updated
- Never
"""


# ─── Hermes Learner ─────────────────────────────────────────────────────────

class HermesLearner:
    """
    Processes chat session transcripts and updates the user's memory file.
    Uses the user's own LLM API key — zero extra cost to us.
    """

    @staticmethod
    def format_transcript(messages: list[dict]) -> str:
        """Format chat messages into a readable transcript."""
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            # Truncate very long assistant responses (visual cards etc.)
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"{role}: {content}")
        return "\n\n".join(lines)

    @staticmethod
    async def process_session(
        messages: list[dict],
        current_memory: str,
        provider: str,
        api_key: str,
    ) -> str:
        """
        Process a completed chat session and return updated memory markdown.

        Args:
            messages: List of chat messages [{role, content}, ...]
            current_memory: User's current memory.md content (or DEFAULT_MEMORY)
            provider: User's LLM provider ID
            api_key: User's decrypted API key

        Returns:
            Updated memory markdown string
        """
        if not messages or len(messages) < 2:
            return current_memory

        transcript = HermesLearner.format_transcript(messages)

        # Build the Hermes prompt
        prompt = HERMES_UPDATE_PROMPT.format(
            current_memory=current_memory or DEFAULT_MEMORY,
            transcript=transcript,
        )

        try:
            # Use the user's own LLM key for the learning call
            raw_response = await call_llm(
                provider=provider,
                api_key=api_key,
                system_prompt=HERMES_EXTRACT_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract markdown from response (strip any code fences)
            updated_memory = _extract_markdown(raw_response)

            # Ensure timestamp is current
            now = datetime.now().isoformat()
            if "## Last Updated" in updated_memory:
                # Replace the last updated line
                lines = updated_memory.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("- ") and i > 0 and "Last Updated" in lines[i-1]:
                        lines[i] = f"- {now}"
                        break
                updated_memory = "\n".join(lines)

            return updated_memory

        except Exception as e:
            # If the LLM call fails, return existing memory unchanged
            print(f"Hermes learning failed: {e}")
            return current_memory

    @staticmethod
    def extract_section(memory_md: str, section: str) -> list[str]:
        """
        Extract entries from a specific section of the memory file.

        Args:
            memory_md: Full memory markdown
            section: Section header (e.g., "Chronotype & Sleep")

        Returns:
            List of entry strings (without the "- " prefix)
        """
        entries = []
        in_section = False

        for line in memory_md.split("\n"):
            if line.startswith("## "):
                in_section = section.lower() in line.lower()
                continue
            if in_section and line.startswith("- "):
                entry = line[2:].strip()
                if entry and entry != "No data yet":
                    entries.append(entry)

        return entries

    @staticmethod
    def format_for_prompt(memory_md: str) -> str:
        """
        Format the memory file into a concise block for system prompt injection.
        Strips the headers and "No data yet" lines, returns only real insights.
        """
        if not memory_md or memory_md.strip() == DEFAULT_MEMORY.strip():
            return ""

        lines = []
        for line in memory_md.split("\n"):
            # Skip headers, empty lines, "No data yet", and "Last Updated"
            if line.startswith("#"):
                continue
            if line.startswith("- No data yet"):
                continue
            if "Last Updated" in line:
                continue
            if line.startswith("- "):
                lines.append(line)

        if not lines:
            return ""

        return "\n".join(lines)


def _extract_markdown(text: str) -> str:
    """Extract markdown content from LLM response, stripping code fences."""
    # If wrapped in ```markdown ... ```
    if "```markdown" in text:
        parts = text.split("```markdown")
        if len(parts) > 1:
            md = parts[1].split("```")[0]
            return md.strip()

    # If wrapped in ``` ... ```
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last ``` lines
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    # No code fences — return as-is
    return text.strip()
