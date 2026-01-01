# Go Development Rules & Constraints

## Scope
Applies to: `module-building` (Economy), `module-market`, `MineplanetGo` (Legacy)

## 1. Core Principles
*   **Precision**: Monetary values must use `shopspring/decimal` or Integer (cents). **NEVER use float32/float64 for currency**.
*   **Concurrency**: Use Goroutines carefully. Always handle context cancellation. Avoid unbounded channel buffers.
*   **Microservices**: Strictly follow Tars protocol if extending existing Tars services.

## 2. Tech Stack
*   **Framework**: TarsGo (RPC), Gin (HTTP Gateway)
*   **Database**: GORM v2 (MySQL/PostgreSQL)
*   **Protocol**: Protobuf (Preferred) or Tars (Legacy)

## 3. Coding Standards
*   **Style**: Uber Go Style Guide.
*   **Error Handling**: Return `error` as the last return value. Wrap errors using `fmt.Errorf("...: %w", err)`.
*   **Project Layout**: Follow standard Go project layout (`cmd/`, `internal/`, `pkg/`, `api/`).

## 4. Specific Constraints
*   **Transactions**: All economic actions (Transfer, Craft, Buy/Sell) MUST be wrapped in DB Transactions.
*   **Interfaces**: Define interfaces for all external dependencies (Mockable for testing).
*   **Log**: Use structural logging (Zap or Tars logs).
