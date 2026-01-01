# Project Memo & Questions

## Pending Clarifications
1.  **Redis Cluster**: Do we need a full Redis Cluster for Day 1, or is a single instance sufficient for < 10k Agents? (Assuming Single for now).
2.  **Tars Protocol**: Are we strictly using Tars binary protocol or migrating to gRPC/Protobuf completely? (Current plan: Protobuf preferred for new services, Tars for legacy).
3.  **Flutter State**: `TorFApp` uses `GetX` heavily. Migration to `Bloc` for new features might introduce friction. Need to decide if we wrap Bloc in GetX or keep distinct.

## Technical Debt / Risks
*   `TorFApp` has mixed mock data. Cleaning this up might break existing demos.
*   Python <-> Go communication: Need to define the standard (HTTP/JSON vs gRPC). HTTP is easier for MVP.
