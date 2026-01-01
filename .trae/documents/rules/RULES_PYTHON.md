# Python Development Rules & Constraints

## Scope
Applies to: `module-oasis-simulation` (Stateless Agent Core, AI Logic)

## 1. Core Principles
*   **Statelessness**: NEVER store Agent state in global variables or memory dictionaries (`self.agents = {}` is FORBIDDEN). All state must be loaded from Redis/DB at the start of a request and saved back at the end.
*   **Async First**: All I/O operations (DB, Redis, HTTP) must be `async`. Use `aiohttp`, `aioredis`, `asyncpg`.
*   **Type Safety**: 100% Type Hints coverage. Use `mypy` for validation.

## 2. Tech Stack
*   **Framework**: FastAPI
*   **Data Models**: Pydantic v2
*   **Database**: PostgreSQL (via `SQLAlchemy` Async or `Tortoise-ORM`), Redis (via `redis-py` async)
*   **AI**: OpenAI SDK (compatible with DeepSeek API)

## 3. Coding Standards
*   **Style**: PEP 8.
*   **Docstrings**: Google Style docstrings for all public functions.
*   **Error Handling**: Use custom Exception classes, catch specifically.
*   **Config**: Use `pydantic-settings` via `.env` files. NO hardcoded API keys.

## 4. Specific Constraints
*   **Agent Identity**: All internal logic must reference Agents by `AgentID` (UUID/Int), never by object reference.
*   **Memory**: Large context (History) must be summarized before storage. Do not dump raw JSON > 10KB into Redis keys without compression.
