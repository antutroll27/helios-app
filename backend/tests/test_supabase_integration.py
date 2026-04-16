"""
HELIOS Backend — Phase 3 Supabase Integration Smoke Test
Manual run only (not a pytest unit test).

Run from repo root:
    python -m backend.tests.test_supabase_integration

Requires:
    - backend/.env (or project root .env) with SUPABASE_URL and SUPABASE_KEY
    - Schema applied: backend/schema.sql + backend/schema_v2.sql

What this checks:
    1. Required tables exist in Supabase
    2. MemoryService.get_memory() returns DEFAULT_MEMORY for a new (unknown) user
    3. MemoryService.get_memory_for_prompt() returns a string (may be empty)
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

REQUIRED_TABLES = [
    "users",
    "user_memories",
    "app_sessions",
    "chat_sessions",
    "chat_messages",
    "sleep_logs",
    "data_imports",
    "shared_llm_usage",
]

# A UUID that will never exist in the DB — used to test new-user behaviour
_DUMMY_USER_ID = "00000000-0000-0000-0000-000000000001"

_PASS = "  \u2713"
_FAIL = "  \u2717"
_failures: list[str] = []


def _check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"{_PASS} {label}")
    else:
        print(f"{_FAIL} {label}" + (f": {detail}" if detail else ""))
        _failures.append(label)


def check_env() -> bool:
    ok = bool(SUPABASE_URL and SUPABASE_KEY)
    _check("SUPABASE_URL and SUPABASE_KEY are set", ok,
           "Set them in .env before running this test")
    return ok


def check_tables(db) -> None:
    print("\nChecking required tables...")
    for table in REQUIRED_TABLES:
        try:
            db.table(table).select("id").limit(1).execute()
            _check(f"Table '{table}' exists", True)
        except Exception as exc:
            _check(f"Table '{table}' exists", False, str(exc))


async def check_memory_service(db) -> None:
    print("\nChecking MemoryService...")
    from backend.memory.memory_service import MemoryService
    from backend.memory.hermes_learner import DEFAULT_MEMORY

    service = MemoryService(db)

    memory = await service.get_memory(_DUMMY_USER_ID)
    _check(
        "get_memory() returns a string",
        isinstance(memory, str),
        f"got {type(memory)}",
    )
    _check(
        "get_memory() returns DEFAULT_MEMORY for unknown user",
        memory == DEFAULT_MEMORY,
        f"got {repr(str(memory)[:60])}" if memory != DEFAULT_MEMORY else "",
    )

    prompt_block = await service.get_memory_for_prompt(_DUMMY_USER_ID)
    _check(
        "get_memory_for_prompt() returns a string",
        isinstance(prompt_block, str),
        f"got {type(prompt_block)}",
    )


def main() -> None:
    print("=" * 50)
    print("HELIOS Phase 3 — Supabase Integration Smoke Test")
    print("=" * 50)

    if not check_env():
        print("\n\u274c Cannot connect without credentials. Exiting.")
        sys.exit(1)

    try:
        from supabase import create_client
        db = create_client(SUPABASE_URL, SUPABASE_KEY)
        _check("Supabase client initialized", True)
    except Exception as exc:
        _check("Supabase client initialized", False, str(exc))
        print("\nCannot connect to Supabase. Exiting.")
        sys.exit(1)

    check_tables(db)
    asyncio.run(check_memory_service(db))

    print("\n" + "=" * 50)
    if _failures:
        print(f"\u274c {len(_failures)} check(s) failed: {', '.join(_failures)}")
        sys.exit(1)
    else:
        print("\u2705 All checks passed")


if __name__ == "__main__":
    main()
