# Update CTO Architecture Proposal

## 1. Update Roadmap Section
I will expand the "Roadmap" section (lines 114-129) in `CTO_ARCHITECTURE_PROPOSAL_V1.md` to provide more specific and detailed technical tasks.

**New Roadmap Content:**
*   **Phase 1 (KeyVault & Economy):** Focus on building the `KeyVault` microservice with AES-256 encryption, `KeyValidator` for health checks, `CreditSystem` for "Proof of Contribution" (PoC), and integrating "Compute Consumption" into the economy system.
*   **Phase 2 (LOD System):** Explicitly designate `module-oasis-simulation` as the base for the **LOD 3 Worker Cluster**. Key tasks include refactoring it to be **stateless** (Context Injection), implementing the `LOD Controller` for dynamic switching, and deploying vLLM/Ollama for LOD 2.
*   **Phase 3 (Reality Injection & Scale):** Detail the pipeline from `module-bettafish` (Crawler) -> `Narrator Agent` -> Game Events. Include specific stress tests for 100k active / 900k dormant agents.

## 2. Fix Mermaid Diagram
I will check and fix the Mermaid diagram syntax at line 61 to ensure it renders correctly in the preview.

## 3. Evaluate `module-oasis-simulation`
I will add a specific evaluation note in the "Existing Code Suggestions" section (or nearby) stating that `module-oasis-simulation` is suitable but needs **stateless refactoring** to serve as the LOD 3 execution engine for the million-agent architecture.

**Target File:** `/Users/mac/ok-mcp/event-crawler/outModules/open-citycloud/CTO_ARCHITECTURE_PROPOSAL_V1.md` (Note: User referred to `.trae/documents/...` but previous context shows the file was created in `outModules/open-citycloud`. I will edit the one that exists.)
