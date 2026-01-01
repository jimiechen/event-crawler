# Flutter Development Rules & Constraints

## Scope
Applies to: `TorFApp` (Client App)

## 1. Core Principles
*   **Performance**: Avoid rebuilding the entire widget tree. Use `const` constructors where possible.
*   **Responsiveness**: UI must never block the main thread. Complex logic goes to Isolate or Async methods.
*   **Separation**: Logic (Bloc/Controller) must be separated from UI (Widgets).

## 2. Tech Stack
*   **Framework**: Flutter (Dart >= 3.0)
*   **State Management**: 
    *   **New Features**: `flutter_bloc` (Preferred for complex state like Agent Soul/Economy).
    *   **Legacy**: `GetX` (Allowed for existing Navigation/Simple UI).
*   **Networking**: `Dio` (HTTP), `web_socket_channel` (Real-time).
*   **Local DB**: `Hive`.

## 3. Coding Standards
*   **Style**: Effective Dart.
*   **Null Safety**: Strict enforcement. No `!` unless absolutely guaranteed.
*   **Assets**: All assets must be registered in `pubspec.yaml` and accessed via `AppAssets` constant class.

## 4. Specific Constraints
*   **Map Rendering**: Tile rendering must be optimized. Don't render 1000 agents as individual heavy widgets; use `CustomPainter` or simplified markers for LOD.
*   **Data Flow**: 
    *   Server -> WebSocket -> Repo -> Bloc -> UI.
    *   UI -> Bloc -> Repo -> API -> Server.
