"""
HELIOS Backend — Memory Service
Reads and writes per-user markdown memory files in Supabase.
No Mem0, no pgvector, no shared API keys — just Postgres + markdown.
"""

from typing import Optional
from backend.memory.hermes_learner import DEFAULT_MEMORY, HermesLearner


class MemoryService:
    """
    Manages per-user memory files stored as markdown text in Supabase.

    Each user has one memory row in the `user_memories` table containing
    their evolving profile as structured markdown. Hermes updates it
    after each chat session using the user's own LLM key.
    """

    def __init__(self, supabase_client):
        self.db = supabase_client
        self.learner = HermesLearner()

    async def get_memory(self, user_id: str) -> str:
        """
        Fetch the user's memory markdown from Supabase.
        Returns DEFAULT_MEMORY if no memory exists yet.
        """
        try:
            result = self.db.table("user_memories").select("memory_md").eq("user_id", user_id).single().execute()
            if result.data and result.data.get("memory_md"):
                return result.data["memory_md"]
        except Exception:
            pass
        return DEFAULT_MEMORY

    async def save_memory(self, user_id: str, memory_md: str) -> None:
        """
        Save/update the user's memory markdown in Supabase.
        Uses upsert — creates if new, updates if exists.
        """
        self.db.table("user_memories").upsert({
            "user_id": user_id,
            "memory_md": memory_md,
        }).execute()

    async def get_memory_for_prompt(self, user_id: str) -> str:
        """
        Fetch and format the user's memory for system prompt injection.
        Returns empty string if no meaningful memories exist.
        """
        memory_md = await self.get_memory(user_id)
        return HermesLearner.format_for_prompt(memory_md)

    async def process_session(
        self,
        user_id: str,
        session_id: str,
        provider: str,
        api_key: str,
    ) -> str | None:
        """
        Process a completed chat session by fetching messages from Supabase.
        Skips sessions with fewer than 4 messages (2 full exchanges).
        Marks the session hermes_processed=True when done.

        Uses the user's own LLM key — zero extra cost.
        """
        # Fetch messages from DB — `timestamp` column defined in backend/schema.sql
        try:
            result = self.db.table("chat_messages") \
                .select("role, content") \
                .eq("session_id", session_id) \
                .order("timestamp") \
                .execute()
            messages = result.data or []  # supabase-py returns None (not []) for empty results
        except Exception as e:
            print(f"[hermes] Failed to fetch messages for session {session_id}: {e}")
            return None

        if len(messages) < 4:  # Need at least 2 full exchanges
            return None

        current_memory = await self.get_memory(user_id)
        updated_memory = await self.learner.process_session(
            messages=messages,
            current_memory=current_memory,
            provider=provider,
            api_key=api_key,
        )
        await self.save_memory(user_id, updated_memory)

        # Mark session as hermes-processed
        try:
            self.db.table("chat_sessions") \
                .update({"hermes_processed": True}) \
                .eq("id", session_id) \
                .execute()
        except Exception as e:
            print(f"[hermes] Failed to mark session {session_id} processed: {e}")

        return updated_memory

    async def get_section(self, user_id: str, section: str) -> list[str]:
        """
        Get entries from a specific memory section.
        Useful for targeted queries (e.g., "what do we know about their caffeine habits?")
        """
        memory_md = await self.get_memory(user_id)
        return HermesLearner.extract_section(memory_md, section)

    async def reset_memory(self, user_id: str) -> None:
        """Reset user's memory to default (user requested deletion)."""
        await self.save_memory(user_id, DEFAULT_MEMORY)
