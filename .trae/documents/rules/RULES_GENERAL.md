# General Project Rules & Constraints

## 1. Architecture Constraints
*   **API First**: No proprietary hardware dependencies. The system must run on standard Cloud/Server instances (Linux/Docker).
*   **DeepSeek Integration**: All AI calls must go through the unified `DeepSeek` Adapter. Do not hardcode specific model versions in business logic; use configuration.
*   **Environment**: 
    *   `DEV`: Localhost / Docker Compose.
    *   `PROD`: K8s / Cloud.
    *   Code must be environment-agnostic.

## 2. Development Workflow
*   **Documentation**: Update `.trae/documents/` when architecture changes.
*   **Commit Message**: `[Module] Action: Description` (e.g., `[Economy] Feat: Add wallet transaction rollback`).

## 3. Directory Structure
*   `/outModules/open-citycloud`: Core Backend (Python/Go).
*   `/outModules/TorFApp`: Client (Flutter).
*   `/outModules/MineplanetGo`: Legacy/Base Services.
