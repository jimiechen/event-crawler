# 48-Hour Development Plan (Hourly Breakdown)

## Day 1: Stateless Agent Infrastructure (The Brain's Foundation)
**Goal**: Build the Python service capable of loading/saving Agent state from Redis.

| Time Slot | Module | Task | Output/Artifact |
| :--- | :--- | :--- | :--- |
| **09:00 - 10:00** | `oasis-simulation` | **Project Init**: Setup FastAPI, Poetry/Pipenv, Dockerfile. | `pyproject.toml`, `main.py` (Hello World) |
| **10:00 - 11:00** | `oasis-simulation` | **Data Schema**: Define `AgentProfile`, `AgentState`, `ShortTermMemory` Pydantic models. | `models/agent.py` |
| **11:00 - 12:00** | `Infra` | **DB Setup**: Write `docker-compose.yml` for Redis & PostgreSQL. | `docker-compose.yml` running |
| **12:00 - 13:00** | *Lunch Break* | | |
| **13:00 - 15:00** | `oasis-simulation` | **Context Loader**: Implement `RedisConnector` to fetch/store `AgentState` JSON. | `services/context_loader.py`, `tests/test_redis.py` |
| **15:00 - 17:00** | `oasis-simulation` | **State Committer**: Implement logic to calculate State Diff and atomic save. | `services/state_committer.py` |
| **17:00 - 18:00** | `oasis-simulation` | **API Layer**: Create `/agent/{id}/tick` endpoint that loads state -> no-op -> saves state. | `api/routes.py` |
| **18:00 - 19:00** | `oasis-simulation` | **Testing**: Write script to spawn 100 concurrent requests to `/tick`. | `scripts/stress_test.py` |

## Day 2: Economy Basics (The Wallet)
**Goal**: Build the Go service for Money and Inventory.

| Time Slot | Module | Task | Output/Artifact |
| :--- | :--- | :--- | :--- |
| **09:00 - 10:00** | `module-building` | **DB Migration**: Create `wallets` and `transactions` tables (SQL/GORM). | `sql/01_wallet.sql` |
| **10:00 - 12:00** | `module-building` | **Wallet Service**: Implement `GetBalance`, `Transfer`, `Mint` (Go). | `services/wallet_service.go` |
| **12:00 - 13:00** | *Lunch Break* | | |
| **13:00 - 15:00** | `module-building` | **Inventory Schema**: Create `items` and `user_inventory` tables. | `models/inventory.go` |
| **15:00 - 17:00** | `module-building` | **Inventory Logic**: Implement `AddItem`, `RemoveItem`, `CheckBalance`. | `services/inventory_service.go` |
| **17:00 - 18:00** | `module-building` | **API Exposure**: Expose Tars/HTTP interfaces for Frontend. | `api/economy.proto` |
| **18:00 - 19:00** | `Integration` | **Cross-Call Test**: Python Agent calls Go Wallet to "Get Balance". | `tests/integration_test.py` |

---
**Note**: Day 2 assumes `module-building` environment is already roughly set up. If not, 09:00-10:00 includes setup.
