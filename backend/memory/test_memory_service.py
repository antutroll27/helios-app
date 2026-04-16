"""Tests for MemoryService.process_session (session_id variant)."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


def make_supabase_mock(messages_data):
    """
    Build a mock supabase client whose .table() returns STABLE mocks per table name.
    Each table name always returns the same mock object so assertions work correctly
    (side_effect returning a new MagicMock each call would break assert_called_once).
    """
    db = MagicMock()

    messages_mock = MagicMock()
    messages_mock.select.return_value.eq.return_value.order.return_value.execute.return_value.data = messages_data

    memories_mock = MagicMock()
    memories_mock.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "memory_md": "# HELIOS User Memory\n\n## Chronotype\n- No data yet"
    }
    memories_mock.upsert.return_value.execute.return_value = MagicMock()

    sessions_mock = MagicMock()
    sessions_mock.update.return_value.eq.return_value.execute.return_value = MagicMock()

    _table_map = {
        "chat_messages": messages_mock,
        "user_memories": memories_mock,
        "chat_sessions": sessions_mock,
    }
    db.table.side_effect = lambda name: _table_map[name]

    # Expose individual table mocks for assertions
    db._sessions_mock = sessions_mock
    db._memories_mock = memories_mock

    return db


@pytest.mark.asyncio
async def test_process_session_skips_under_4_messages():
    """Sessions with fewer than 4 messages (2 exchanges) are skipped — no Hermes call."""
    from backend.memory.memory_service import MemoryService

    db = make_supabase_mock([
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ])
    service = MemoryService(db)

    result = await service.process_session("uid-1", "sess-1", "kimi", "key-1")

    assert result is None
    db._memories_mock.upsert.assert_not_called()
    db._sessions_mock.update.assert_not_called()


@pytest.mark.asyncio
async def test_process_session_runs_hermes_and_marks_processed():
    """process_session fetches messages, runs Hermes, saves memory, marks session processed."""
    from backend.memory.memory_service import MemoryService

    messages = [
        {"role": "user", "content": "how's my sleep?"},
        {"role": "assistant", "content": "Your sleep looks short."},
        {"role": "user", "content": "what should I do?"},
        {"role": "assistant", "content": "Try going to bed 30 min earlier."},
    ]
    db = make_supabase_mock(messages)
    service = MemoryService(db)

    updated = "# HELIOS User Memory\n\n## Chronotype\n- Late chronotype\n"
    with patch.object(service.learner, "process_session", new=AsyncMock(return_value=updated)):
        result = await service.process_session("uid-1", "sess-1", "kimi", "key-1")

    assert result == updated
    # hermes_processed flag should have been set — use the stable sessions_mock reference
    db._sessions_mock.update.assert_called_once_with({"hermes_processed": True})


@pytest.mark.asyncio
async def test_process_session_exact_4_messages_runs():
    """Boundary: exactly 4 messages should trigger Hermes."""
    from backend.memory.memory_service import MemoryService

    messages = [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
        {"role": "user", "content": "c"},
        {"role": "assistant", "content": "d"},
    ]
    db = make_supabase_mock(messages)
    service = MemoryService(db)

    with patch.object(service.learner, "process_session", new=AsyncMock(return_value="updated")) as mock_hermes:
        await service.process_session("uid-1", "sess-1", "kimi", "key-1")

    mock_hermes.assert_called_once()
